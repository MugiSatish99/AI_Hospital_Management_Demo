import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import sqlite3
import math
from datetime import datetime
from groq import Groq

from database import (
    get_users, get_patients,
    get_history, get_doctor_extra,
    get_messages, delete_user,
    add_user, add_doctor_extra,
    send_message, get_requests,
    update_request_status
)


DOCTOR_SPECIALIZATIONS = [
    "General Physician",
    "Internal Medicine",
    "Family Medicine",
    "Emergency Medicine",
    "Critical Care Specialist",
    "Cardiologist",
    "Cardiac Surgeon",
    "Neurologist",
    "Neurosurgeon",
    "Orthopedic",
    "Orthopedic Surgeon",
    "Dermatologist",
    "ENT Specialist",
    "Ophthalmologist",
    "Dentist",
    "Pediatrician",
    "Neonatologist",
    "Gynecologist",
    "Obstetrician",
    "Psychiatrist",
    "Psychologist",
    "Pulmonologist",
    "Gastroenterologist",
    "Hepatologist",
    "Nephrologist",
    "Urologist",
    "Endocrinologist",
    "Diabetologist",
    "Oncologist",
    "Radiation Oncologist",
    "Hematologist",
    "Rheumatologist",
    "Allergist / Immunologist",
    "Infectious Disease Specialist",
    "General Surgeon",
    "Plastic Surgeon",
    "Vascular Surgeon",
    "Thoracic Surgeon",
    "Anesthesiologist",
    "Radiologist",
    "Pathologist",
    "Physiotherapist",
    "Nutritionist / Dietitian",
    "Rehabilitation Specialist",
    "Pain Management Specialist",
    "Sports Medicine Specialist",
    "Geriatrician",
    "Sexologist",
    "Ayurveda Doctor",
    "Homeopathy Doctor"
]


def patient_columns():
    return [
        "ID", "Name", "Symptoms", "Result", "Date", "Time",
        "Status", "assigned_doctor", "Hospital"
    ]


def clean_value(value):
    if value is None or str(value).lower() in ["none", "nan", ""]:
        return "Not Assigned"
    return value


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_best_hospital(lat, lon, symptoms):
    try:
        df = pd.read_csv("hospitals.csv")

        df["distance"] = df.apply(
            lambda row: calculate_distance(lat, lon, row["lat"], row["lon"]),
            axis=1
        )

        s = str(symptoms).lower()

        if "heart" in s or "chest" in s:
            spec = "cardiology"
        elif "brain" in s or "head" in s:
            spec = "neurology"
        elif "bone" in s:
            spec = "orthopedic"
        elif "skin" in s:
            spec = "dermatology"
        elif "child" in s or "baby" in s:
            spec = "pediatrics"
        elif "pregnancy" in s or "women" in s:
            spec = "gynecology"
        else:
            spec = "general"

        filtered = df[df["specialization"].astype(str).str.lower().str.contains(spec)]

        if not filtered.empty:
            return filtered.sort_values("distance").iloc[0]["name"]

        return df.sort_values("distance").iloc[0]["name"]

    except:
        return None


def send_notification(user, msg):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        message TEXT,
        time TEXT
    )
    """)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO notifications (user, message, time) VALUES (?,?,?)",
        (user, msg, now)
    )

    conn.commit()
    conn.close()


def auto_assign_doctor(symptoms):
    s = str(symptoms).lower()
    if "chest" in s or "heart" in s or "cardiac" in s:
        return "random3"
    elif "brain" in s or "head" in s or "psych" in s or "stroke" in s or "seizure" in s:
        return "random2"
    else:
        return "random1"


def send_to_hospital(pid, hospital, symptoms):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE patients ADD COLUMN hospital TEXT")
    except:
        pass

    try:
        c.execute("ALTER TABLE patients ADD COLUMN assigned_doctor TEXT")
    except:
        pass

    doctor = auto_assign_doctor(symptoms)

    c.execute("""
    UPDATE patients
    SET hospital=?, assigned_doctor=?, status='ASSIGNED'
    WHERE id=?
    """, (hospital, doctor, pid))

    conn.commit()
    conn.close()

    send_notification("admin", f"Patient {pid} sent to {hospital}")
    send_notification("doctor", f"New patient assigned: {pid}")
    send_notification("staff", f"Prepare patient: {pid}")




def update_patient_hospital_from_request(patient_name, hospital, symptoms):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE patients ADD COLUMN hospital TEXT")
    except:
        pass

    try:
        c.execute("ALTER TABLE patients ADD COLUMN assigned_doctor TEXT")
    except:
        pass

    doctor = auto_assign_doctor(symptoms)

    c.execute("""
    UPDATE patients
    SET hospital=?, assigned_doctor=?, status='ASSIGNED'
    WHERE name=?
    """, (hospital, doctor, patient_name))

    conn.commit()
    conn.close()


def delete_user_full(username):
    delete_user(username)

    image_path = f"doctor_images/{username}.png"

    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except:
            pass

def get_hospital_patients(hospital):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    try:
        data = c.execute("""
        SELECT id, name, symptoms, result, date, time, status, assigned_doctor, hospital
        FROM patients
        WHERE hospital=?
        """, (hospital,)).fetchall()
    except:
        data = []

    conn.close()
    return data


def doctor_accept(pid, doctor):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    UPDATE patients
    SET assigned_doctor=?, status='IN_PROGRESS'
    WHERE id=?
    """, (doctor, pid))

    conn.commit()
    conn.close()


def get_all_hospitals():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    try:
        data = c.execute("""
        SELECT DISTINCT hospital FROM patients
        WHERE hospital IS NOT NULL AND hospital!=''
        """).fetchall()

        hospitals = [d[0] for d in data if d[0]]
    except:
        hospitals = []

    conn.close()
    return hospitals


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ai_response(text):
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": text}],
            model="llama3-70b-8192"
        )
        return res.choices[0].message.content
    except:
        return "AI not available"


def doctor_card(
    username,
    name,
    phone,
    specialization,
    qualification="MBBS",
    experience="Fresher",
    image_path=None
):

    with st.container():
        # Check database for custom profile image first
        from database import get_doctor_extra
        extra_info = get_doctor_extra(username)
        db_image = extra_info[6] if (extra_info and len(extra_info) > 6) else None
        
        if db_image:
            st.image(db_image, width=120)
        elif image_path and os.path.exists(image_path):
            st.image(image_path, width=120)
        else:
            st.image(
                "https://cdn-icons-png.flaticon.com/512/3774/3774299.png",
                width=120
            )

        st.markdown(
            f"""
            <h2 style='margin-bottom:0px;'>Dr. {clean_value(name)}</h2>
            <h4 style='color:#2563eb; margin-top:5px;'>
                🩺 {clean_value(specialization)}
            </h4>
            """,
            unsafe_allow_html=True
        )

        if st.button("View Full Info", key=f"view_{username}"):
            st.info(f"""
👨‍⚕️ Doctor Full Details

Name: Dr. {clean_value(name)}

Specialization: {clean_value(specialization)}

Qualification: {clean_value(qualification)}

Experience: {clean_value(experience)}

Phone: {clean_value(phone)}

Username: {clean_value(username)}
""")
            # Update Doctor Profile Photo Widget
            new_img = st.file_uploader("Update Doctor Photo (Max 5MB)", type=["jpg", "jpeg", "png"], key=f"up_img_{username}")
            if new_img is not None:
                try:
                    from utils import process_profile_image
                    from database import update_doctor_image
                    from datetime import datetime
                    
                    img_bytes = process_profile_image(new_img)
                    img_path = f"doctor_images/{username}.png"
                    os.makedirs("doctor_images", exist_ok=True)
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)
                    update_doctor_image(username, img_bytes, img_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("✅ Profile photo updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating photo: {e}")
                    
            if db_image or (image_path and os.path.exists(image_path)):
                if st.button("❌ Remove Photo", key=f"rem_img_{username}"):
                    from database import delete_doctor_image
                    delete_doctor_image(username)
                    if image_path and os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except:
                            pass
                    st.success("✅ Profile photo removed successfully!")
                    st.rerun()


def show():
    import random, time, json

    # ── Styled page header ──────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    html, body, [class*='css'] { font-family: 'Inter', sans-serif; }
    .adm-page-title {
        background: linear-gradient(120deg,#0f62fe,#0043ce);
        color: white; border-radius: 16px; padding: 22px 28px; margin-bottom: 20px;
        display: flex; align-items: center; gap: 16px;
    }
    .adm-page-title .icon { font-size: 38px; }
    .adm-page-title h1 { margin:0; font-size:26px; font-weight:900; }
    .adm-page-title p  { margin:4px 0 0 0; font-size:14px; opacity:0.88; }
    .role-badge {
        display:inline-block; padding:3px 10px; border-radius:20px;
        font-size:11px; font-weight:700; text-transform:uppercase;
    }
    .rb-patient  { background:#dbeafe; color:#1e40af; }
    .rb-doctor   { background:#dcfce7; color:#15803d; }
    .rb-staff    { background:#fef9c3; color:#854d0e; }
    .rb-admin    { background:#ede9fe; color:#6d28d9; }
    .rb-hospital { background:#fee2e2; color:#b91c1c; }
    .cred-card {
        background:#f0f9ff; border:1px solid #bae6fd; border-radius:12px;
        padding:16px 20px; margin:12px 0;
    }
    .cred-card code { background:#e0f2fe; padding:2px 6px; border-radius:4px;
        font-size:13px; color:#0369a1; }
    .acc-table th { background:#f1f5f9; color:#334155; font-size:13px; }
    .acc-table td { font-size:13px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="adm-page-title">
      <div class="icon">🏥</div>
      <div>
        <h1>AI Hospital — Admin Dashboard</h1>
        <p>Manage users, accounts, doctors, analytics &amp; hospital operations</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar navigation ──────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style='background:linear-gradient(135deg,#0f62fe,#0043ce);color:white;
         border-radius:12px;padding:12px 16px;margin-bottom:12px;'>
      <b style='font-size:15px;'>👤 {st.session_state.user}</b><br>
      <span style='font-size:12px;opacity:.85;'>Role: Admin</span>
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio("Navigation", [
        "📊 Dashboard",
        "➕ Create Account",
        "🗂️ Manage Accounts",
        "👥 Users",
        "👨‍⚕️ Doctors",
        "💬 Messages",
        "📈 Analytics",
        "🤖 AI Assistant",
        "🏨 Hospital Control",
        "📋 Hospital Requests",
    ])

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    # ➕  CREATE ACCOUNT  (full, clean, role-aware)
    # ════════════════════════════════════════════════════════════════════════
    if menu == "➕ Create Account":
        st.markdown("## ➕ Create New Account")
        st.caption("Create Patient, Doctor, Staff, Admin, or Hospital accounts with full credentials.")
        st.divider()

        # Role selector with visual badges
        role = st.selectbox(
            "👤 Select Account Role",
            ["Patient", "Doctor", "Staff", "Admin", "Hospital"],
            help="Choose the type of account to create"
        )

        # Auto-generate defaults (stable per role selection)
        if f"cre_rand_{role}" not in st.session_state:
            st.session_state[f"cre_rand_{role}"] = random.randint(1000, 9999)
        _rn = st.session_state[f"cre_rand_{role}"]

        prefix_map = {"Patient": "PAT", "Doctor": "DOC", "Staff": "STF", "Admin": "ADM", "Hospital": "HSP"}
        generated_id = f"{prefix_map[role]}-{_rn}"

        st.markdown(f"""
        <div class='cred-card'>
          <b>🪪 Auto-Generated ID:</b> <code>{generated_id}</code>
          &nbsp;&mdash;&nbsp; You may customise the username and password below.
        </div>
        """, unsafe_allow_html=True)

        # ── Section A: Core credentials ──
        st.markdown("#### 🔐 Account Credentials")
        cr1, cr2 = st.columns(2)
        with cr1:
            username = st.text_input("Username ✱", value=f"{role.lower()}_{_rn}",
                                     placeholder="Unique login username")
            password = st.text_input("Password ✱", value=f"{role[:3].lower()}{_rn}@Hosp",
                                     type="password", placeholder="Minimum 6 characters")
            confirm_pwd = st.text_input("Confirm Password ✱", type="password",
                                        placeholder="Re-enter password")
        with cr2:
            name_label = "Hospital Name" if role == "Hospital" else "Full Name ✱"
            name  = st.text_input(name_label, placeholder="Enter full name")
            email = st.text_input("Email Address", placeholder="user@example.com")
            phone = st.text_input("Mobile Number", placeholder="10-digit mobile number")

        # ── Section B: Demographics (non-hospital) ──
        age, gender, blood, address, city = 30, "Male", "O+", "", ""
        if role != "Hospital":
            st.markdown("#### 📋 Personal Details")
            d1, d2, d3 = st.columns(3)
            with d1:
                age    = st.number_input("Age", 1, 120, 30)
            with d2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            with d3:
                blood  = st.selectbox("Blood Group",
                    ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            a1, a2 = st.columns(2)
            with a1:
                address = st.text_input("Address", placeholder="Street / Colony / Area")
            with a2:
                city = st.text_input("City", placeholder="e.g. Visakhapatnam")

        # ── Section C: Role-specific fields ──
        patient_id = doctor_id = staff_id = hospital_id = None
        emergency_contact = allergies = chronic_diseases = None
        previous_diseases = previous_medications = previous_reports = None
        specialization = qualification = experience = doctor_image = None
        availability = "Available"
        department = "General"
        latitude, longitude = 0.0, 0.0
        total_beds = available_beds = icu_beds = 0
        departments_list  = "General, Emergency"
        available_doctors_list = ""
        status_hospital = "Active"

        if role == "Patient":
            patient_id = generated_id
            st.markdown("#### 🩺 Clinical Profile")
            emergency_contact = st.text_input("Emergency Contact Number",
                placeholder="e.g. 9876500000")
            c1p, c2p = st.columns(2)
            with c1p:
                allergies = st.text_area("Allergies",
                    placeholder="e.g. Penicillin, Peanuts", height=80)
                chronic_diseases = st.text_area("Chronic / Existing Diseases",
                    placeholder="e.g. Type-2 Diabetes, Hypertension", height=80)
            with c2p:
                previous_diseases = st.text_area("Previous Diagnosed Diseases",
                    placeholder="e.g. Pneumonia (2024)", height=80)
                previous_medications = st.text_area("Previous Medications",
                    placeholder="e.g. Metformin 500mg", height=80)
            previous_reports = st.text_area("Past Medical Reports Summary",
                placeholder="e.g. HbA1c: 7.2% (June 2026)")

        elif role == "Doctor":
            doctor_id = generated_id
            st.markdown("#### 👨‍⚕️ Professional Details")
            d1, d2 = st.columns(2)
            with d1:
                specialization = st.selectbox("Specialization ✱", DOCTOR_SPECIALIZATIONS)
                qualification  = st.text_input("Qualification", placeholder="e.g. MBBS, MD, MS")
            with d2:
                experience   = st.text_input("Experience", placeholder="e.g. 8 Years")
                availability = st.selectbox("Availability", ["Available", "Busy", "Away"])
            department = st.text_input("Department", value=specialization or "General")
            prasad_branch = st.selectbox("Assigned Hospital Branch", [
                "Prasad Hospitals, Gajuwaka",
                "Prasad Hospitals, MVP Colony",
                "Prasad Hospitals, Kukatpally",
            ])
            hospital_id = prasad_branch
            city = "hyderabad" if "Kukatpally" in prasad_branch else "visakhapatnam"
            doctor_image = st.file_uploader("Upload Doctor Photo",
                type=["jpg", "jpeg", "png"])

        elif role == "Staff":
            staff_id = generated_id
            st.markdown("#### 🏷️ Staff Details")
            s1, s2 = st.columns(2)
            with s1:
                department = st.text_input("Department", placeholder="e.g. Cardiology, ICU")
                staff_designation = st.text_input("Designation / Role",
                    placeholder="e.g. Senior Nurse, Lab Technician")
            with s2:
                staff_branch = st.selectbox("Assigned Hospital Branch", [
                    "Prasad Hospitals, Gajuwaka",
                    "Prasad Hospitals, MVP Colony",
                    "Prasad Hospitals, Kukatpally",
                ])
                availability = st.selectbox("Status", ["Available", "On Leave", "Inactive"])
            hospital_id = staff_branch
            city = "hyderabad" if "Kukatpally" in staff_branch else "visakhapatnam"

        elif role == "Admin":
            st.markdown("#### 🔑 Admin Privileges")
            admin_dept = st.text_input("Admin Department",
                value="Hospital Administration",
                placeholder="e.g. Hospital Administration, IT Admin")
            department = admin_dept
            hospital_id = "Prasad Hospitals — Admin"
            st.info("ℹ️ Admin accounts have full access to all panels, user management, and system settings.")

        elif role == "Hospital":
            hospital_id = generated_id
            st.markdown("#### 🏨 Hospital Details")
            h1, h2 = st.columns(2)
            with h1:
                address = st.text_input("Hospital Address")
                city    = st.text_input("Hospital City")
                emergency_contact = st.text_input("Emergency Contact Number")
            with h2:
                latitude  = st.number_input("Latitude",  format="%.4f", value=17.3850)
                longitude = st.number_input("Longitude", format="%.4f", value=78.4867)
                status_hospital = st.selectbox("Status", ["Active", "Inactive"])
            b1, b2, b3 = st.columns(3)
            with b1:
                total_beds = st.number_input("Total Beds", min_value=0, value=50)
            with b2:
                available_beds = st.number_input("Available Beds", min_value=0, value=15)
            with b3:
                icu_beds = st.number_input("ICU Beds", min_value=0, value=5)
            departments_list = st.text_area(
                "Supported Departments (comma-separated)",
                value="Cardiology, Neurology, Orthopedic, Dermatology, General")
            available_doctors_list = st.text_area("Available Doctors (comma-separated)")

        # ── Section D: Face registration (optional) ──
        with st.expander("📸 Optional: Register Face for Face-Login", expanded=False):
            st.caption("Capture a clear face photo to enable Face Recognition Login.")
            face_img = st.camera_input("Capture Face", key=f"face_cam_{generated_id}")
            face_signature_json = None
            if face_img:
                try:
                    from PIL import Image
                    from face_auth import get_face_landmarks, get_face_signature
                    pil_face  = Image.open(face_img).convert("RGB")
                    face_lms  = get_face_landmarks(pil_face)
                    if face_lms:
                        face_signature_json = json.dumps(get_face_signature(face_lms))
                        st.success("✅ Face captured!")
                    else:
                        st.warning("No face detected — try again with better lighting.")
                except Exception as fe:
                    st.error(f"Face error: {fe}")

        st.divider()

        # ── Submit ──
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            create_clicked = st.button("✅ Create Account", type="primary",
                                       use_container_width=True)
        with col_btn2:
            if st.button("🔄 Reset Form", use_container_width=True):
                for k in [f"cre_rand_{role}"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

        if create_clicked:
            # Validate
            errors = []
            if not username.strip():
                errors.append("Username is required.")
            if not password.strip() or len(password) < 6:
                errors.append("Password must be at least 6 characters.")
            if password != confirm_pwd:
                errors.append("Passwords do not match.")
            if not name.strip() and role != "Hospital":
                errors.append("Full name is required.")
            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                status = add_user(
                    username=username.strip(),
                    password=password.strip(),
                    role=role.lower(),
                    name=name.strip(),
                    age=int(age),
                    blood=blood,
                    phone=phone.strip() or None,
                    img=None,
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    staff_id=staff_id,
                    emergency_contact=emergency_contact,
                    allergies=allergies,
                    chronic_diseases=chronic_diseases,
                    previous_diseases=previous_diseases,
                    previous_medications=previous_medications,
                    previous_reports=previous_reports,
                    gender=gender,
                    email=email.strip() or None,
                    address=address.strip() or None,
                    city=city.strip() or None,
                    hospital_id=hospital_id,
                    qualification=qualification,
                    experience=experience,
                    specialization=specialization,
                    department=department or "General",
                    availability=availability,
                    latitude=latitude,
                    longitude=longitude,
                    total_beds=int(total_beds),
                    available_beds=int(available_beds),
                    icu_beds=int(icu_beds),
                    departments=departments_list,
                    available_doctors=available_doctors_list,
                    status=status_hospital,
                    face_landmarks_signature=face_signature_json,
                )

                err_map = {
                    "exists":         "Username already exists. Choose a different one.",
                    "email_exists":   "Email is already registered to another account.",
                    "phone_exists":   "Phone number is already registered to another account.",
                    "patient_exists": "Patient ID already exists — refresh to get a new ID.",
                    "doctor_exists":  "Doctor ID already exists.",
                    "staff_exists":   "Staff ID already exists.",
                    "hospital_exists":"Hospital ID already exists.",
                }
                if status in err_map:
                    st.error(f"❌ {err_map[status]}")
                else:
                    # Post-creation extras
                    if role == "Doctor":
                        os.makedirs("doctor_images", exist_ok=True)
                        img_bytes = None
                        image_path = f"doctor_images/{username}.png"
                        if doctor_image:
                            try:
                                from utils import process_profile_image
                                img_bytes = process_profile_image(doctor_image)
                                with open(image_path, "wb") as f:
                                    f.write(img_bytes)
                            except Exception as de:
                                st.warning(f"Photo save failed: {de}")
                        add_doctor_extra(username, specialization, qualification, experience)
                        if img_bytes:
                            from database import update_doctor_image
                            update_doctor_image(username, img_bytes, image_path,
                                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                    elif role == "Hospital":
                        try:
                            conn_hb = sqlite3.connect("hospital.db")
                            c_hb = conn_hb.cursor()
                            c_hb.execute("""
                              INSERT OR REPLACE INTO hospital_beds
                              (hospital_name,total_beds,available_beds,total_icu,available_icu,emergency_support)
                              VALUES (?,?,?,?,?,?)
                            """, (name, total_beds, available_beds, icu_beds, icu_beds,
                                  "Yes" if any(d in departments_list
                                               for d in ["Cardiology","Neurology","Emergency"])
                                  else "No"))
                            conn_hb.commit()
                            conn_hb.close()
                        except Exception as hbe:
                            print("Hospital beds insert error:", hbe)

                    # Success card
                    st.success(f"✅ {role} account created successfully!")
                    badge_cls = {
                        "Patient":"rb-patient","Doctor":"rb-doctor",
                        "Staff":"rb-staff","Admin":"rb-admin","Hospital":"rb-hospital"
                    }.get(role, "rb-patient")
                    st.markdown(f"""
                    <div class='cred-card' style='border-color:#6ee7b7;background:#f0fdf4;'>
                      <div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>
                        <span style='font-size:26px;'>{'🏥' if role=='Hospital' else '👤'}</span>
                        <div>
                          <b style='font-size:16px;'>{name or username}</b>&nbsp;
                          <span class='role-badge {badge_cls}'>{role}</span>
                        </div>
                      </div>
                      <table style='width:100%;border-collapse:collapse;font-size:13px;'>
                        <tr>
                          <td style='padding:4px 8px;'><b>🪪 ID</b></td>
                          <td><code>{generated_id}</code></td>
                          <td style='padding:4px 8px;'><b>👤 Username</b></td>
                          <td><code>{username}</code></td>
                        </tr>
                        <tr>
                          <td style='padding:4px 8px;'><b>🔑 Password</b></td>
                          <td><code>{password}</code></td>
                          <td style='padding:4px 8px;'><b>📞 Phone</b></td>
                          <td>{phone or '—'}</td>
                        </tr>
                        <tr>
                          <td style='padding:4px 8px;'><b>📧 Email</b></td>
                          <td>{email or '—'}</td>
                          <td style='padding:4px 8px;'><b>🏙️ City</b></td>
                          <td>{city or '—'}</td>
                        </tr>
                      </table>
                      <p style='margin:10px 0 0 0;font-size:12px;color:#6b7280;'>
                        ⚠️ Share these credentials securely with the account holder.
                      </p>
                    </div>
                    """, unsafe_allow_html=True)
                    # Reset random seed so next creation gets new defaults
                    if f"cre_rand_{role}" in st.session_state:
                        del st.session_state[f"cre_rand_{role}"]
                    time.sleep(1.5)
                    st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    # 🗂️  MANAGE ACCOUNTS  — view / reset-password / delete by role
    # ════════════════════════════════════════════════════════════════════════
    elif menu == "🗂️ Manage Accounts":
        st.markdown("## 🗂️ Manage Accounts")
        st.caption("View all accounts, reset passwords, and delete accounts by role.")
        st.divider()

        filter_role = st.selectbox("Filter by Role",
            ["All", "patient", "doctor", "staff", "admin", "hospital"])

        conn_m = sqlite3.connect("hospital.db")
        c_m    = conn_m.cursor()
        if filter_role == "All":
            c_m.execute("""
                SELECT id, username, name, role, phone, email, patient_id, doctor_id,
                       staff_id, hospital_id, city, status
                FROM users ORDER BY role, name
            """)
        else:
            c_m.execute("""
                SELECT id, username, name, role, phone, email, patient_id, doctor_id,
                       staff_id, hospital_id, city, status
                FROM users WHERE LOWER(role)=? ORDER BY name
            """, (filter_role,))
        rows_m = c_m.fetchall()
        conn_m.close()

        if not rows_m:
            st.info("No accounts found for the selected role.")
        else:
            st.markdown(f"**{len(rows_m)} account(s) found**")

            # Search
            srch = st.text_input("🔍 Search by name or username", placeholder="Type to filter...")
            if srch:
                rows_m = [r for r in rows_m
                          if srch.lower() in str(r[1]).lower()
                          or srch.lower() in str(r[2]).lower()]

            badge_cls_map = {
                "patient":"rb-patient","doctor":"rb-doctor",
                "staff":"rb-staff","admin":"rb-admin","hospital":"rb-hospital"
            }

            for row in rows_m:
                uid, uname, uname_full, urole, uphone, uemail, upid, udid, usid, uhid, ucity, ustatus = row
                bc = badge_cls_map.get(urole, "rb-patient")
                with st.expander(
                    f"{'👤' if urole not in ['doctor'] else '👨‍⚕️'} {uname_full or uname}   "
                    f"— {urole.title()} | {ucity or '—'}",
                    expanded=False
                ):
                    i1, i2 = st.columns(2)
                    with i1:
                        st.markdown(f"<span class='role-badge {bc}'>{urole.upper()}</span>",
                                    unsafe_allow_html=True)
                        st.write(f"**Username:** `{uname}`")
                        st.write(f"**ID:** {upid or udid or usid or uhid or '—'}")
                        st.write(f"**Phone:** {uphone or '—'}")
                    with i2:
                        st.write(f"**Email:** {uemail or '—'}")
                        st.write(f"**City:** {ucity or '—'}")
                        st.write(f"**Hospital/Branch:** {uhid or '—'}")
                        st.write(f"**Status:** {ustatus or 'Active'}")

                    st.markdown("**🔑 Reset Password**")
                    new_pw = st.text_input(f"New password for `{uname}`",
                                           type="password",
                                           key=f"newpw_{uid}",
                                           placeholder="Min 6 characters")
                    if st.button("💾 Save New Password", key=f"savepw_{uid}"):
                        if new_pw and len(new_pw) >= 6:
                            try:
                                conn_pw = sqlite3.connect("hospital.db")
                                c_pw = conn_pw.cursor()
                                c_pw.execute("UPDATE users SET password=? WHERE id=?",
                                             (new_pw, uid))
                                conn_pw.commit()
                                conn_pw.close()
                                st.success(f"✅ Password updated for `{uname}`.")
                            except Exception as pwe:
                                st.error(f"Failed: {pwe}")
                        else:
                            st.warning("Password must be at least 6 characters.")

                    st.markdown("---")
                    if st.button(f"🗑️ Delete account `{uname}`", key=f"del_{uid}",
                                 type="secondary"):
                        try:
                            conn_del = sqlite3.connect("hospital.db")
                            c_del = conn_del.cursor()
                            c_del.execute("DELETE FROM users WHERE id=?", (uid,))
                            conn_del.commit()
                            conn_del.close()
                            st.success(f"🗑️ Account `{uname}` deleted.")
                            st.rerun()
                        except Exception as de:
                            st.error(f"Delete failed: {de}")

    # ════════════════════════════════════════════════════════════════════════
    # Map old menu keys to new ones for remaining sections
    # ════════════════════════════════════════════════════════════════════════
    elif menu == "📊 Dashboard":
        menu = "Dashboard"
    elif menu == "👥 Users":
        menu = "Users"
    elif menu == "👨‍⚕️ Doctors":
        menu = "Doctors"
    elif menu == "💬 Messages":
        menu = "Messages"
    elif menu == "📈 Analytics":
        menu = "Analytics"
    elif menu == "🤖 AI Assistant":
        menu = "AI Assistant"
    elif menu == "🏨 Hospital Control":
        menu = "Hospital Control"
    elif menu == "📋 Hospital Requests":
        menu = "Hospital Requests"

    if menu == "Dashboard":

        data = get_patients()

        df = pd.DataFrame(
            data,
            columns=patient_columns()
        ) if data else pd.DataFrame()

        st.subheader("Patient Records")

        if not df.empty:

            df["Hospital"] = df["Hospital"].apply(clean_value)
            df["assigned_doctor"] = df["assigned_doctor"].apply(clean_value)

            st.dataframe(df, width="stretch")

            st.subheader("Auto Hospital Assignment")

            for _, row in df.iterrows():
                lat, lon = 17.3850, 78.4867
                hospital = get_best_hospital(lat, lon, row["Symptoms"])

                if hospital:
                    st.write(f"👤 {row['Name']} → {hospital}")

                    if st.button(f"Send {row['ID']}", key=f"send_{row['ID']}"):
                        send_to_hospital(row["ID"], hospital, row["Symptoms"])
                        st.success("Sent successfully")
                        st.rerun()
        else:
            st.info("No patient records found")

    elif menu == "Users":

        st.subheader("👥 Users Management")

        users = get_users()

        if not users:
            st.info("No users found")

        else:
            df = pd.DataFrame(
                users,
                columns=[
                    "ID",
                    "Username",
                    "Password",
                    "Role",
                    "Name",
                    "Age",
                    "Phone",
                    "Blood Group"
                ]
            )

            df["Role"] = df["Role"].astype(str).str.lower()

            st.markdown("## All Users")
            st.dataframe(
                df.drop(columns=["Password"], errors="ignore"),
                width="stretch"
            )

            st.markdown("---")
            st.markdown("###  Table-wise User Control")

            role_filter = st.selectbox(
                "Select User Type",
                ["patient", "doctor", "staff"],
                format_func=lambda x: x.title()
            )

            filtered_df = df[df["Role"] == role_filter].copy()

            if filtered_df.empty:
                st.info(f"No {role_filter}s found")

            else:
                if role_filter == "doctor":
                    extra_rows = []

                    for _, row in filtered_df.iterrows():
                        extra = get_doctor_extra(row["Username"])

                        specialization = (
                            extra[1]
                            if extra and len(extra) > 1 and extra[1]
                            else "General Physician"
                        )

                        qualification = (
                            extra[2]
                            if extra and len(extra) > 2 and extra[2]
                            else "MBBS"
                        )

                        experience = (
                            extra[3]
                            if extra and len(extra) > 3 and extra[3]
                            else "Fresher"
                        )

                        availability = (
                            extra[4]
                            if extra and len(extra) > 4 and extra[4]
                            else "Available"
                        )

                        extra_rows.append({
                            "ID": row["ID"],
                            "Username": row["Username"],
                            "Role": row["Role"],
                            "Name": row["Name"],
                            "Age": row["Age"],
                            "Phone": row["Phone"],
                            "Blood Group": row["Blood Group"],
                            "Specialization": specialization,
                            "Qualification": qualification,
                            "Experience": experience,
                            "Availability": availability
                        })

                    display_df = pd.DataFrame(extra_rows)

                else:
                    display_df = filtered_df.drop(columns=["Password"], errors="ignore")

                st.markdown(f"### {role_filter.title()} Table")
                st.dataframe(display_df, width="stretch")

                st.markdown("---")
                st.markdown("###  Delete Selected User")

                usernames = filtered_df["Username"].astype(str).tolist()

                selected_user = st.selectbox(
                    "Select user to delete",
                    usernames,
                    key=f"delete_select_{role_filter}"
                )

                selected_row = filtered_df[
                    filtered_df["Username"].astype(str) == str(selected_user)
                ].iloc[0]

                st.warning(f"""
You selected:

Name: {clean_value(selected_row['Name'])}

Username: {clean_value(selected_row['Username'])}

Role: {clean_value(selected_row['Role'])}

Phone: {clean_value(selected_row['Phone'])}
""")

                confirm = st.checkbox(
                    f"Yes, delete {selected_user}",
                    key=f"confirm_delete_{role_filter}_{selected_user}"
                )

                if st.button(
                    "Delete Selected User",
                    key=f"delete_btn_{role_filter}_{selected_user}"
                ):

                    if confirm:
                        delete_user_full(selected_user)
                        st.success(f"{role_filter.title()} deleted successfully")
                        st.rerun()

                    else:
                        st.warning("Please confirm before deleting")

    elif menu == "Doctors":

        st.markdown("## 👨‍⚕️ Doctor Management")
        st.caption("Create, view, edit, and manage all doctor accounts and their credentials.")

        tab_list, tab_create, tab_edit, tab_creds, tab_delete = st.tabs([
            "📋 All Doctors", "➕ Create Doctor", "✏️ Edit Doctor",
            "🔑 Credentials", "🗑️ Delete Doctor"
        ])

        users = get_users()
        doctors = [u for u in users if len(u) > 3 and u[3] == "doctor"]

        # ── helper ──────────────────────────────────────────────────────────
        def _doc_extra(uname):
            ex = get_doctor_extra(uname)
            return {
                "spec":  ex[1] if ex and len(ex) > 1 and ex[1] else "General Physician",
                "qual":  ex[2] if ex and len(ex) > 2 and ex[2] else "MBBS",
                "exp":   ex[3] if ex and len(ex) > 3 and ex[3] else "N/A",
                "avail": ex[4] if ex and len(ex) > 4 and ex[4] else "Available",
            }

        # ── TAB 1 : All Doctors ─────────────────────────────────────────────
        with tab_list:
            if not doctors:
                st.info("No doctors registered yet. Use **Create Doctor** tab to add one.")
            else:
                srch_d = st.text_input("🔍 Search doctors by name / specialization",
                                       key="adm_doc_search")
                cols_d = st.columns(3)
                shown  = 0
                for idx, d in enumerate(doctors):
                    uname  = d[1] if len(d) > 1 else "N/A"
                    dname  = d[4] if len(d) > 4 and d[4] else uname
                    dphone = d[6] if len(d) > 6 and d[6] else "N/A"
                    demail = d[19] if len(d) > 19 and d[19] else "—"
                    dhosp  = d[21] if len(d) > 21 and d[21] else "Prasad Hospitals"
                    ex     = _doc_extra(uname)

                    if srch_d and srch_d.lower() not in dname.lower() \
                               and srch_d.lower() not in ex["spec"].lower():
                        continue

                    img_path = f"doctor_images/{uname}.png"
                    with cols_d[shown % 3]:
                        st.markdown(f"""
                        <div style='background:white;border-radius:16px;padding:18px;
                             box-shadow:0 4px 20px rgba(0,0,0,0.09);
                             border-top:4px solid #0f62fe;margin-bottom:18px;'>
                          <div style='display:flex;align-items:center;gap:12px;'>
                            <div style='font-size:36px;'>{'🖼️' if not os.path.exists(img_path) else '👨‍⚕️'}</div>
                            <div>
                              <b style='font-size:15px;color:#071a44;'>Dr. {dname}</b><br>
                              <span style='color:#0f62fe;font-size:13px;font-weight:700;'>{ex["spec"]}</span>
                            </div>
                          </div>
                          <hr style='margin:10px 0;border-color:#e8f0fe;'>
                          <table style='font-size:12px;width:100%;'>
                            <tr><td>🏥 Hospital</td><td><b>{dhosp}</b></td></tr>
                            <tr><td>🎓 Qualification</td><td>{ex["qual"]}</td></tr>
                            <tr><td>⏱️ Experience</td><td>{ex["exp"]}</td></tr>
                            <tr><td>📞 Phone</td><td>{dphone}</td></tr>
                            <tr><td>📧 Email</td><td>{demail}</td></tr>
                            <tr><td>🟢 Status</td>
                              <td><span style='background:{"#dcfce7" if ex["avail"]=="Available" else "#fef9c3"};
                              color:{"#15803d" if ex["avail"]=="Available" else "#854d0e"};
                              padding:2px 8px;border-radius:8px;font-size:11px;
                              font-weight:700;'>{ex["avail"]}</span></td>
                            </tr>
                            <tr><td>👤 Username</td><td><code>{uname}</code></td></tr>
                          </table>
                        </div>
                        """, unsafe_allow_html=True)
                        if os.path.exists(img_path):
                            st.image(img_path, width=80)
                    shown += 1
                if shown == 0:
                    st.info("No doctors match the search.")
                st.markdown(f"**Total: {shown} doctor(s)**")

        # ── TAB 2 : Create Doctor ────────────────────────────────────────────
        with tab_create:
            st.markdown("### ➕ Register New Doctor Account")
            st.caption("Fill all details — the doctor can log in immediately with the generated credentials.")

            import random as _r
            if "adm_doc_rand" not in st.session_state:
                st.session_state["adm_doc_rand"] = _r.randint(1000, 9999)
            _drn = st.session_state["adm_doc_rand"]
            _doc_id = f"DOC-{_drn}"

            st.markdown(f"""
            <div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;
                 padding:12px 18px;margin-bottom:16px;'>
              <b>🪪 Auto-Generated Doctor ID:</b>
              <code style='background:#e0f2fe;padding:2px 8px;border-radius:6px;
              color:#0369a1;'>{_doc_id}</code>
              &nbsp;— The doctor logs in with the username &amp; password below.
            </div>
            """, unsafe_allow_html=True)

            # Credentials
            st.markdown("#### 🔐 Login Credentials")
            dc1, dc2 = st.columns(2)
            with dc1:
                d_uname  = st.text_input("Username ✱", value=f"doctor_{_drn}",
                                          key="adm_d_uname")
                d_pwd    = st.text_input("Password ✱", value=f"doc{_drn}@Hosp",
                                          type="password", key="adm_d_pwd")
                d_pwd_cf = st.text_input("Confirm Password ✱", type="password",
                                          key="adm_d_pwdcf")
            with dc2:
                d_name  = st.text_input("Full Name ✱", placeholder="e.g. Dr. Arun Sharma",
                                         key="adm_d_name")
                d_email = st.text_input("Email Address", placeholder="doctor@hospital.com",
                                         key="adm_d_email")
                d_phone = st.text_input("Phone Number", placeholder="10-digit mobile",
                                         key="adm_d_phone")

            # Personal info
            st.markdown("#### 📋 Personal Details")
            dp1, dp2, dp3 = st.columns(3)
            with dp1:
                d_age    = st.number_input("Age", 22, 80, 35, key="adm_d_age")
            with dp2:
                d_gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                                        key="adm_d_gen")
            with dp3:
                d_blood  = st.selectbox("Blood Group",
                    ["A+","A-","B+","B-","O+","O-","AB+","AB-"], key="adm_d_blood")
            da1, da2 = st.columns(2)
            with da1:
                d_addr = st.text_input("Address", placeholder="Colony / Street",
                                       key="adm_d_addr")
            with da2:
                d_city = st.text_input("City", placeholder="e.g. Visakhapatnam",
                                       key="adm_d_city")

            # Professional info
            st.markdown("#### 👨‍⚕️ Professional Details")
            dpr1, dpr2 = st.columns(2)
            with dpr1:
                d_spec  = st.selectbox("Specialization ✱", DOCTOR_SPECIALIZATIONS,
                                        key="adm_d_spec")
                d_qual  = st.text_input("Qualification ✱",
                                         placeholder="e.g. MBBS, MD, MS, DNB",
                                         key="adm_d_qual")
            with dpr2:
                d_exp   = st.text_input("Experience",
                                         placeholder="e.g. 8 Years",
                                         key="adm_d_exp")
                d_avail = st.selectbox("Availability Status",
                                        ["Available", "Busy", "Away", "On Leave"],
                                        key="adm_d_avail")
            d_dept = st.text_input("Department", value=d_spec,
                                    key="adm_d_dept")

            # Hospital branch
            st.markdown("#### 🏥 Hospital Assignment")
            d_branch = st.selectbox("Assign to Hospital Branch", [
                "Prasad Hospitals, Gajuwaka",
                "Prasad Hospitals, MVP Colony",
                "Prasad Hospitals, Kukatpally",
            ], key="adm_d_branch")
            d_hosp_city = "hyderabad" if "Kukatpally" in d_branch else "visakhapatnam"

            # Photo
            d_photo = st.file_uploader("Doctor Profile Photo (optional)",
                                        type=["jpg","jpeg","png"],
                                        key="adm_d_photo")

            st.divider()
            dbtn1, dbtn2 = st.columns([3, 1])
            with dbtn1:
                d_create = st.button("✅ Create Doctor Account", type="primary",
                                     use_container_width=True, key="adm_d_create")
            with dbtn2:
                if st.button("🔄 Reset", use_container_width=True, key="adm_d_reset"):
                    if "adm_doc_rand" in st.session_state:
                        del st.session_state["adm_doc_rand"]
                    st.rerun()

            if d_create:
                _errs = []
                if not d_uname.strip():    _errs.append("Username is required.")
                if not d_pwd.strip() or len(d_pwd) < 6:
                    _errs.append("Password must be ≥ 6 characters.")
                if d_pwd != d_pwd_cf:      _errs.append("Passwords do not match.")
                if not d_name.strip():     _errs.append("Full name is required.")
                if not d_qual.strip():     _errs.append("Qualification is required.")
                for _e in _errs:
                    st.error(f"❌ {_e}")

                if not _errs:
                    _st = add_user(
                        username=d_uname.strip(),
                        password=d_pwd.strip(),
                        role="doctor",
                        name=d_name.strip(),
                        age=int(d_age),
                        blood=d_blood,
                        phone=d_phone.strip() or None,
                        email=d_email.strip() or None,
                        doctor_id=_doc_id,
                        gender=d_gender,
                        address=d_addr.strip() or None,
                        city=d_hosp_city,
                        hospital_id=d_branch,
                        specialization=d_spec,
                        qualification=d_qual.strip(),
                        experience=d_exp.strip() or "N/A",
                        department=d_dept or d_spec,
                        availability=d_avail,
                    )
                    _err_map = {
                        "exists":        "Username already taken.",
                        "email_exists":  "Email already registered.",
                        "phone_exists":  "Phone already registered.",
                        "doctor_exists": "Doctor ID already exists — refresh to get a new one.",
                    }
                    if _st in _err_map:
                        st.error(f"❌ {_err_map[_st]}")
                    else:
                        add_doctor_extra(d_uname.strip(), d_spec, d_qual.strip(), d_exp.strip())
                        if d_photo:
                            try:
                                os.makedirs("doctor_images", exist_ok=True)
                                from utils import process_profile_image
                                _ib = process_profile_image(d_photo)
                                _ip = f"doctor_images/{d_uname.strip()}.png"
                                with open(_ip, "wb") as _f: _f.write(_ib)
                                from database import update_doctor_image
                                update_doctor_image(d_uname.strip(), _ib, _ip,
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            except Exception as _pe:
                                st.warning(f"Photo save failed: {_pe}")

                        st.success("✅ Doctor account created successfully!")
                        st.markdown(f"""
                        <div style='background:#f0fdf4;border:1.5px solid #6ee7b7;
                             border-radius:14px;padding:18px 22px;margin-top:10px;'>
                          <b style='font-size:17px;'>👨‍⚕️ Dr. {d_name}</b>
                          &nbsp;<span style='background:#dcfce7;color:#15803d;
                          padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700;
                          text-transform:uppercase;'>Doctor</span><br><br>
                          <table style='font-size:13px;border-collapse:collapse;width:100%;'>
                            <tr>
                              <td style='padding:4px 10px;'><b>🪪 Doctor ID</b></td>
                              <td><code style='background:#d1fae5;padding:2px 8px;
                              border-radius:4px;'>{_doc_id}</code></td>
                              <td style='padding:4px 10px;'><b>👤 Username</b></td>
                              <td><code style='background:#d1fae5;padding:2px 8px;
                              border-radius:4px;'>{d_uname}</code></td>
                            </tr>
                            <tr>
                              <td style='padding:4px 10px;'><b>🔑 Password</b></td>
                              <td><code style='background:#d1fae5;padding:2px 8px;
                              border-radius:4px;'>{d_pwd}</code></td>
                              <td style='padding:4px 10px;'><b>🩺 Specialization</b></td>
                              <td>{d_spec}</td>
                            </tr>
                            <tr>
                              <td style='padding:4px 10px;'><b>🏥 Hospital</b></td>
                              <td colspan='3'>{d_branch}</td>
                            </tr>
                            <tr>
                              <td style='padding:4px 10px;'><b>📞 Phone</b></td>
                              <td>{d_phone or "—"}</td>
                              <td style='padding:4px 10px;'><b>📧 Email</b></td>
                              <td>{d_email or "—"}</td>
                            </tr>
                          </table>
                          <p style='margin:12px 0 0;font-size:12px;color:#6b7280;'>
                            ⚠️ Share credentials securely. Doctor can log in immediately.
                          </p>
                        </div>
                        """, unsafe_allow_html=True)
                        if "adm_doc_rand" in st.session_state:
                            del st.session_state["adm_doc_rand"]
                        time.sleep(1.5)
                        st.rerun()

        # ── TAB 3 : Edit Doctor ──────────────────────────────────────────────
        with tab_edit:
            st.markdown("### ✏️ Edit Doctor Profile")
            if not doctors:
                st.info("No doctors found.")
            else:
                doc_names = {
                    (d[4] if len(d) > 4 and d[4] else d[1]): d[1]
                    for d in doctors
                }
                sel_disp = st.selectbox("Select Doctor to Edit",
                                        list(doc_names.keys()),
                                        key="adm_edit_sel")
                sel_un   = doc_names[sel_disp]

                # Pull current data
                conn_e = sqlite3.connect("hospital.db")
                c_e    = conn_e.cursor()
                c_e.execute("""
                    SELECT name, age, gender, phone, email, address, city,
                           hospital_id, specialization, qualification,
                           experience, availability, department
                    FROM users WHERE username=?
                """, (sel_un,))
                cur = c_e.fetchone()
                conn_e.close()

                if not cur:
                    st.error("Doctor record not found.")
                else:
                    cn, ca, cg, cph, cem, cad, cct, chid, csp, cql, cex, cav, cdp = cur
                    st.markdown("#### 📝 Update Details")
                    e1, e2 = st.columns(2)
                    with e1:
                        e_name  = st.text_input("Full Name", value=cn or "",
                                                key=f"ed_n_{sel_un}")
                        e_phone = st.text_input("Phone", value=cph or "",
                                                key=f"ed_ph_{sel_un}")
                        e_email = st.text_input("Email", value=cem or "",
                                                key=f"ed_em_{sel_un}")
                        e_addr  = st.text_input("Address", value=cad or "",
                                                key=f"ed_ad_{sel_un}")
                    with e2:
                        e_age   = st.number_input("Age", 22, 80,
                                                   int(ca) if ca else 35,
                                                   key=f"ed_ag_{sel_un}")
                        e_gen   = st.selectbox("Gender", ["Male","Female","Other"],
                            index=["Male","Female","Other"].index(cg)
                                  if cg in ["Male","Female","Other"] else 0,
                            key=f"ed_ge_{sel_un}")
                        e_city  = st.text_input("City", value=cct or "",
                                                key=f"ed_ci_{sel_un}")
                    st.markdown("#### 👨‍⚕️ Professional Details")
                    ep1, ep2 = st.columns(2)
                    with ep1:
                        e_spec  = st.selectbox("Specialization", DOCTOR_SPECIALIZATIONS,
                            index=DOCTOR_SPECIALIZATIONS.index(csp)
                                  if csp in DOCTOR_SPECIALIZATIONS else 0,
                            key=f"ed_sp_{sel_un}")
                        e_qual  = st.text_input("Qualification", value=cql or "",
                                                key=f"ed_ql_{sel_un}")
                    with ep2:
                        e_exp   = st.text_input("Experience", value=cex or "",
                                                key=f"ed_ex_{sel_un}")
                        e_avail = st.selectbox("Availability",
                            ["Available","Busy","Away","On Leave"],
                            index=["Available","Busy","Away","On Leave"].index(cav)
                                  if cav in ["Available","Busy","Away","On Leave"] else 0,
                            key=f"ed_av_{sel_un}")
                    e_dept  = st.text_input("Department", value=cdp or e_spec,
                                            key=f"ed_dp_{sel_un}")
                    e_hosp  = st.selectbox("Hospital Branch", [
                        "Prasad Hospitals, Gajuwaka",
                        "Prasad Hospitals, MVP Colony",
                        "Prasad Hospitals, Kukatpally",
                    ], index=0, key=f"ed_ho_{sel_un}")
                    e_photo = st.file_uploader("Update Profile Photo",
                                               type=["jpg","jpeg","png"],
                                               key=f"ed_pi_{sel_un}")

                    if st.button("💾 Save Changes", type="primary",
                                 use_container_width=True,
                                 key=f"ed_save_{sel_un}"):
                        try:
                            conn_u = sqlite3.connect("hospital.db")
                            c_u    = conn_u.cursor()
                            c_u.execute("""
                                UPDATE users SET
                                  name=?, age=?, gender=?, phone=?, email=?,
                                  address=?, city=?, hospital_id=?,
                                  specialization=?, qualification=?,
                                  experience=?, availability=?, department=?
                                WHERE username=?
                            """, (e_name, int(e_age), e_gen, e_phone, e_email,
                                  e_addr, e_city, e_hosp, e_spec, e_qual,
                                  e_exp, e_avail, e_dept, sel_un))
                            conn_u.commit()
                            conn_u.close()
                            # Update doctor_extra
                            add_doctor_extra(sel_un, e_spec, e_qual, e_exp)
                            # Update photo
                            if e_photo:
                                os.makedirs("doctor_images", exist_ok=True)
                                from utils import process_profile_image
                                from database import update_doctor_image
                                _ib2 = process_profile_image(e_photo)
                                _ip2 = f"doctor_images/{sel_un}.png"
                                with open(_ip2, "wb") as _f2: _f2.write(_ib2)
                                update_doctor_image(sel_un, _ib2, _ip2,
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            st.success(f"✅ Dr. {e_name}'s profile updated successfully!")
                            st.rerun()
                        except Exception as _ue:
                            st.error(f"Update failed: {_ue}")

        # ── TAB 4 : Credentials / Reset Password ─────────────────────────────
        with tab_creds:
            st.markdown("### 🔑 View & Reset Doctor Credentials")
            st.caption("Reset login passwords for any doctor account.")
            if not doctors:
                st.info("No doctors found.")
            else:
                for d in doctors:
                    uname = d[1] if len(d) > 1 else "N/A"
                    dname = d[4] if len(d) > 4 and d[4] else uname
                    dph   = d[6] if len(d) > 6 and d[6] else "—"
                    dem   = d[19] if len(d) > 19 and d[19] else "—"
                    ex    = _doc_extra(uname)

                    with st.expander(
                        f"👨‍⚕️ Dr. {dname}  —  {ex['spec']}",
                        expanded=False
                    ):
                        c_i1, c_i2 = st.columns(2)
                        with c_i1:
                            st.write(f"**Username:** `{uname}`")
                            st.write(f"**Doctor ID:** {d[22] if len(d) > 22 else '—'}")
                            st.write(f"**Phone:** {dph}")
                        with c_i2:
                            st.write(f"**Email:** {dem}")
                            st.write(f"**Hospital:** {d[21] if len(d) > 21 and d[21] else 'Prasad Hospitals'}")
                            st.write(f"**Status:** {ex['avail']}")

                        st.markdown("---")
                        new_pw = st.text_input(
                            f"New password for Dr. {dname}",
                            type="password",
                            key=f"adm_dpw_{uname}",
                            placeholder="Min 6 characters"
                        )
                        if st.button("💾 Update Password",
                                     key=f"adm_dub_{uname}",
                                     use_container_width=True):
                            if new_pw and len(new_pw) >= 6:
                                try:
                                    conn_pw = sqlite3.connect("hospital.db")
                                    c_pw = conn_pw.cursor()
                                    c_pw.execute(
                                        "UPDATE users SET password=? WHERE username=?",
                                        (new_pw, uname))
                                    conn_pw.commit()
                                    conn_pw.close()
                                    st.success(f"✅ Password updated for Dr. {dname}.")
                                except Exception as pe:
                                    st.error(f"Failed: {pe}")
                            else:
                                st.warning("Password must be ≥ 6 characters.")

        # ── TAB 5 : Delete Doctor ────────────────────────────────────────────
        with tab_delete:
            st.markdown("### 🗑️ Delete Doctor Account")
            if not doctors:
                st.info("No doctors to delete.")
            else:
                doc_map2 = {
                    (d[4] if len(d) > 4 and d[4] else d[1]): d[1]
                    for d in doctors
                }
                del_disp = st.selectbox("Select Doctor to Delete",
                                        list(doc_map2.keys()),
                                        key="adm_del_doc_sel")
                del_un   = doc_map2[del_disp]

                st.warning(f"""
⚠️ You are about to permanently delete the account for **Dr. {del_disp}** (username: `{del_un}`).
This action **cannot be undone**. All associated data will be removed.
                """)
                confirm_del = st.checkbox(
                    f"Yes, I confirm deletion of Dr. {del_disp}'s account",
                    key=f"adm_del_conf_{del_un}"
                )
                if st.button("🗑️ Delete Doctor Account", type="secondary",
                             key=f"adm_del_btn_{del_un}",
                             use_container_width=True):
                    if confirm_del:
                        try:
                            delete_user_full(del_un)
                            # Also remove doctor_extra entry
                            conn_dx = sqlite3.connect("hospital.db")
                            c_dx    = conn_dx.cursor()
                            c_dx.execute("DELETE FROM doctor_extra WHERE username=?",
                                         (del_un,))
                            conn_dx.commit()
                            conn_dx.close()
                            st.success(f"✅ Dr. {del_disp}'s account deleted.")
                            st.rerun()
                        except Exception as _de2:
                            st.error(f"Deletion failed: {_de2}")
                    else:
                        st.warning("Please tick the confirmation checkbox first.")

    elif menu == "Messages":

        st.subheader("Messages")

        messages = get_messages("admin")

        if messages:
            st.dataframe(pd.DataFrame(messages), width="stretch")
        else:
            st.info("No messages")

    elif menu == "Analytics":
        st.subheader("📊 Disease Trend & Hospital Analytics Dashboard")

        def extract_disease(result_str):
            if not result_str:
                return "Unknown"
            res = str(result_str).lower()
            if "condition:" in res:
                try:
                    return result_str.split("Condition:")[-1].split("\n")[0].strip()
                except:
                    pass
            if "disease:" in res:
                try:
                    return result_str.split("Disease:")[-1].split("\n")[0].strip()
                except:
                    pass
            if "emergency case" in res:
                return "Emergency Cardiac/Trauma"
            if "nose bleeding" in res:
                return "Nose Bleeding"
            if "bleeding wound" in res:
                return "Bleeding Wound"
            if "burn" in res:
                return "Burn Injury"
            if "skin issue" in res:
                return "Skin Issue"
            return "General Illness"

        data = get_patients()

        if data:
            df = pd.DataFrame(data, columns=patient_columns())
            df["Disease"] = df["Result"].apply(extract_disease)
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("### 🦠 Predicted Disease Distribution")
                disease_counts = df["Disease"].value_counts().head(8)
                if not disease_counts.empty:
                    fig1, ax1 = plt.subplots(figsize=(6, 4))
                    colors = plt.cm.tab10(range(len(disease_counts)))
                    ax1.bar(disease_counts.index, disease_counts.values, color=colors)
                    ax1.set_ylabel("Number of Cases")
                    ax1.set_title("Top Predicted Diseases")
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig1)
                else:
                    st.info("No disease data to plot.")
                    
            with c2:
                st.markdown("### 🚨 Emergency & Severity Levels")
                df["Severity"] = df["Status"].fillna("NORMAL").str.upper()
                df["Severity"] = df["Severity"].replace("ASSIGNED", "MEDIUM")
                severity_counts = df["Severity"].value_counts()
                if not severity_counts.empty:
                    fig2, ax2 = plt.subplots(figsize=(6, 4))
                    ax2.pie(severity_counts.values, labels=severity_counts.index, autopct="%1.1f%%", startangle=90, colors=['#ff4d4d', '#ff9999', '#33cc33', '#3399ff'])
                    ax2.axis('equal')
                    ax2.set_title("Cases by Severity Level")
                    plt.tight_layout()
                    st.pyplot(fig2)
                else:
                    st.info("No severity data to plot.")
                    
            st.divider()
            
            st.markdown("### 📈 Patient Intake & Booking Trends")
            df["IntakeDate"] = pd.to_datetime(df["Date"], errors='coerce')
            df_intake = df.dropna(subset=["IntakeDate"]).copy()
            if not df_intake.empty:
                daily_intake = df_intake.groupby("Date").size().reset_index(name="Count")
                daily_intake = daily_intake.sort_values("Date")
                
                fig3, ax3 = plt.subplots(figsize=(10, 4))
                ax3.plot(daily_intake["Date"], daily_intake["Count"], marker="o", color="#0f62fe", linewidth=2)
                ax3.set_xlabel("Date")
                ax3.set_ylabel("Number of Registrations")
                ax3.set_title("Daily Patient Registrations over Time")
                plt.xticks(rotation=45)
                plt.grid(True, linestyle="--", alpha=0.5)
                plt.tight_layout()
                st.pyplot(fig3)
            else:
                st.info("No date details found to map intake trends.")
        else:
            st.info("No patient data available for dashboard analysis.")

    elif menu == "AI Assistant":

        st.subheader(" AI Assistant")

        text = st.text_area("Ask")

        if st.button("Ask AI"):
            if text:
                st.success(ai_response(text))
            else:
                st.warning("Enter question")

    elif menu == "Hospital Control":

        st.title(" Hospital Control Center")

        data = get_patients()

        if not data:
            st.info("No patient data available")

        else:

            df = pd.DataFrame(
                data,
                columns=patient_columns()
            )

            df["Hospital"] = df["Hospital"].apply(clean_value)
            df["assigned_doctor"] = df["assigned_doctor"].apply(clean_value)

            hospitals = sorted(
                df["Hospital"]
                .dropna()
                .unique()
                .tolist()
            )

            hospitals = [h for h in hospitals if h != "Not Assigned"]

            if not hospitals:
                st.warning("No hospitals assigned yet")
                st.stop()

            selected_hospital = st.selectbox(
                "🏥 Select Hospital",
                hospitals
            )

            hospital_df = df[
                df["Hospital"] == selected_hospital
            ].copy()

            hospital_df = hospital_df.sort_values(
                by="ID",
                ascending=False
            )

            total_patients = len(hospital_df)

            emergency_cases = hospital_df[
                hospital_df["Result"]
                .astype(str)
                .str.lower()
                .str.contains(
                    "emergency|critical|high|heart|stroke",
                    na=False
                )
            ]

            completed_cases = hospital_df[
                hospital_df["Status"]
                .astype(str)
                .str.upper() == "COMPLETED"
            ]

            discharged_cases = hospital_df[
                hospital_df["Status"]
                .astype(str)
                .str.upper() == "DISCHARGED"
            ]

            active_cases = hospital_df[
                hospital_df["Status"]
                .astype(str)
                .str.upper()
                .isin(["ASSIGNED", "IN_PROGRESS", "TRANSFERRED"])
            ]

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "👥 Total Patients",
                    total_patients
                )

            with c2:
                st.metric(
                    " Emergency",
                    len(emergency_cases)
                )

            with c3:
                st.metric(
                    " Active",
                    len(active_cases)
                )

            with c4:
                st.metric(
                    "Completed",
                    len(completed_cases)
                )

            st.caption(f" Discharged: {len(discharged_cases)}")

            st.markdown("---")

            doctors = [
                u[1]
                for u in get_users()
                if len(u) > 3 and str(u[3]).lower() == "doctor"
            ]

            if not doctors:
                st.warning("No doctors available")

            for _, row in hospital_df.iterrows():

                pid = row["ID"]
                status = str(row["Status"]).upper().strip()
                assigned_doctor = clean_value(row["assigned_doctor"])

                if status == "COMPLETED":
                    status_color = "green"

                elif status == "DISCHARGED":
                    status_color = "blue"

                elif status in ["ASSIGNED", "IN_PROGRESS", "TRANSFERRED"]:
                    status_color = "orange"

                else:
                    status_color = "red"

                is_emergency = any(x in str(row["Result"]).lower() for x in [
                    "emergency",
                    "critical",
                    "heart",
                    "stroke",
                    "high"
                ])

                with st.container(border=True):

                    if is_emergency and status not in ["COMPLETED", "DISCHARGED"]:
                        st.error(
                            f" Emergency Case #{pid}"
                        )

                    st.markdown(f"""
### 👤 {row['Name']}

🏥 Hospital: {row['Hospital']}

🩺 Symptoms: {row['Symptoms']}

🤖 Result: {row['Result']}

📌 Status: :{status_color}[{status}]

👨‍⚕️ Doctor: {assigned_doctor}
""")

                    # Completed / Discharged ayyaka buttons remove
                    if status in ["COMPLETED", "DISCHARGED"]:
                        st.markdown("---")
                        continue

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        if doctors and status not in ["IN_PROGRESS", "COMPLETED", "DISCHARGED"]:

                            selected_doctor = st.selectbox(
                                f"Assign Doctor {pid}",
                                doctors,
                                key=f"doctor_{pid}"
                            )

                            if st.button(
                                f" Assign Doctor #{pid}",
                                key=f"assign_{pid}",
                                use_container_width=True
                            ):

                                conn = sqlite3.connect("hospital.db")
                                c = conn.cursor()

                                c.execute("""
                                UPDATE patients
                                SET assigned_doctor=?,
                                    status='IN_PROGRESS'
                                WHERE id=?
                                """, (
                                    selected_doctor,
                                    pid
                                ))

                                conn.commit()
                                conn.close()

                                st.success("Doctor Assigned Successfully")
                                st.rerun()

                        elif status == "IN_PROGRESS":
                            st.success(" Doctor already assigned")

                    with col2:

                        if status != "COMPLETED":

                            if st.button(
                                f"Complete #{pid}",
                                key=f"complete_{pid}",
                                use_container_width=True
                            ):

                                conn = sqlite3.connect("hospital.db")
                                c = conn.cursor()

                                c.execute("""
                                UPDATE patients
                                SET status='COMPLETED'
                                WHERE id=?
                                """, (pid,))

                                conn.commit()
                                conn.close()

                                st.success("Case Completed")
                                st.rerun()

                    with col3:

                        if status != "DISCHARGED":

                            if st.button(
                                f"🏠 Discharge #{pid}",
                                key=f"discharge_{pid}",
                                use_container_width=True
                            ):

                                conn = sqlite3.connect("hospital.db")
                                c = conn.cursor()

                                c.execute("""
                                UPDATE patients
                                SET status='DISCHARGED'
                                WHERE id=?
                                """, (pid,))

                                conn.commit()
                                conn.close()

                                st.success("Patient Discharged")
                                st.rerun()

                    st.markdown("---")


    elif menu == " Hospital Requests":

        st.title(" Emergency Hospital Requests")

        requests = get_requests()

        def is_important_case(r):
            text = f"{r[3]} {r[4]}".lower()

            return any(x in text for x in [
                "chest pain", "heart", "stroke", "unconscious",
                "breathing", "bleeding", "accident", "critical",
                "emergency", "high", "severe", "fracture", "burn",
                "head injury"
            ])

        def request_order(r):
            status = str(r[7]).strip().lower()

            if status == "rejected":
                status_score = 0
            elif status == "accepted" and "doctor:" in str(r[4]).lower():
                status_score = 2
            elif status == "accepted":
                status_score = 1
            else:
                status_score = 3

            important_score = 1 if is_important_case(r) else 0

            return (status_score, important_score, r[0])

        requests = sorted(
            requests,
            key=request_order,
            reverse=True
        )

        pending_requests = []
        important_requests = []
        accepted_requests = []
        assigned_requests = []

        for r in requests:
            status = str(r[7]).strip().lower()
            result = str(r[4]).lower()

            if status == "rejected":
                continue

            if status == "accepted" and "doctor:" in result:
                assigned_requests.append(r)
            elif status == "accepted":
                accepted_requests.append(r)
            else:
                pending_requests.append(r)

                if is_important_case(r):
                    important_requests.append(r)

        pending_requests = sorted(
            pending_requests,
            key=lambda r: (is_important_case(r), r[0]),
            reverse=True
        )

        important_requests = sorted(
            important_requests,
            key=lambda r: r[0],
            reverse=True
        )

        accepted_requests = sorted(
            accepted_requests,
            key=lambda r: r[0],
            reverse=True
        )

        assigned_requests = sorted(
            assigned_requests,
            key=lambda r: (is_important_case(r), r[0]),
            reverse=True
        )

        st.subheader(" Important Cases First")

        if not important_requests:
            st.info("No important cases now")
        else:
            for r in important_requests:
                st.error(f"""
Important Case #{r[0]}

 Patient: {r[1]}

Hospital: {clean_value(r[2])}

Symptoms: {r[3]}

Result: {r[4]}

Status: {r[7]}

Time: {r[8]}
""")

        st.markdown("---")
        st.subheader("Pending Requests")

        if not pending_requests:
            st.success("No pending requests")
        else:
            for r in pending_requests:

                req_id = r[0]
                patient_name = r[1]
                hospital = clean_value(r[2])
                symptoms = r[3]
                result = r[4]
                lat = r[5]
                lon = r[6]
                status = r[7]
                created_at = r[8]

                box = st.error if is_important_case(r) else st.info

                box(f"""
Request #{req_id}

Patient: {patient_name}

Hospital: {hospital}

Symptoms: {symptoms}

Result: {result}

Location: ({lat}, {lon})

Status: {status}

Time: {created_at}
""")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        f"ACCEPT #{req_id}",
                        key=f"admin_accept_{req_id}",
                        use_container_width=True
                    ):
                        update_request_status(req_id, "Accepted")

                        update_patient_hospital_from_request(
                            patient_name,
                            hospital,
                            symptoms
                        )

                        st.success("Accepted and hospital assigned")
                        st.rerun()

                with col2:
                    if st.button(
                        f"REJECT #{req_id}",
                        key=f"admin_reject_{req_id}",
                        use_container_width=True
                    ):
                        update_request_status(req_id, "Rejected")
                        st.error("Request rejected")
                        st.rerun()

                st.markdown("---")

        st.subheader("Accepted Cases")

        if not accepted_requests:
            st.info("No accepted cases")
        else:
            for r in accepted_requests:
                st.success(f"""
Accepted Case #{r[0]}

Patient: {r[1]}

Hospital: {clean_value(r[2])}

Symptoms: {r[3]}

Result: {r[4]}

Location: ({r[5]}, {r[6]})

Time: {r[8]}
""")

        st.markdown("---")
        st.subheader("Assigned Cases")

        if not assigned_requests:
            st.info("No assigned cases")
        else:
            for r in assigned_requests:
                st.info(f"""
Assigned Case #{r[0]}

Patient: {r[1]}

Hospital: {clean_value(r[2])}

Symptoms: {r[3]}

Result: {r[4]}

Location: ({r[5]}, {r[6]})

Time: {r[8]}
""")

