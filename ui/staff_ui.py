import streamlit as st
import pandas as pd
import os

from database import (
    add_user,
    get_users,
    get_doctor_extra,
    get_active_patients,
    update_patient_status,
    get_all_patients,
    get_patient_full_history,
    get_assigned_patients,
    get_history
)

from utils import (
    detect_status,
    map_symptom_to_specialization,
    get_live_location,
    select_best_hospital,
    get_map_embed,
    hospital_chat_response,
    simulate_ambulance
)

from hospitals import get_hospitals
from ai import get_ai_response


def show():

    st.title("👩‍⚕️ Staff Patient Panel")
    st.info(f"👨‍⚕️ Staff Logged In: {st.session_state.user}")

    # Check if Prasad Hospital Staff or other receiving hospital staff
    is_prasad_staff = False
    staff_hosp = None
    try:
        import sqlite3
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT hospital_id FROM users WHERE username=?", (st.session_state.user,))
        row_h = c.fetchone()
        staff_hosp = row_h[0] if row_h else None
        conn.close()
    except Exception as e:
        print("Error fetching staff hospital:", e)
        
    if not staff_hosp or "prasad" in str(staff_hosp).lower():
        is_prasad_staff = True

    menu_options = [
        "📊 Patient Dashboard",
        "➕ Add Patient",
        "📱 Create Account",
        "🔐 Manage Accounts",
        "🚨 Emergency Patients",
        "🏨 Hospital Beds",
        "📋 Shared Records",
        "👨‍⚕️ Assigned Patients",
        "👥 All Patients",
        "📜 Patient History",
        "🧠 Patient AI Assistant"
    ]
    if is_prasad_staff:
        menu_options.append("🏨 Prasad Referral Center")
    else:
        menu_options.append("📥 Received Referrals")

    menu = st.sidebar.radio("Menu", menu_options)

    if menu == "📊 Patient Dashboard":

        st.subheader("📊 Patient Overview")

        all_patients = get_all_patients()
        emergency_patients = get_active_patients()
        assigned_patients = get_assigned_patients(st.session_state.user)

        total_patients = len(all_patients) if all_patients else 0
        total_emergency = len(emergency_patients) if emergency_patients else 0
        total_assigned = len(assigned_patients) if assigned_patients else 0

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Patients", total_patients)
        c2.metric("Emergency Cases", total_emergency)
        c3.metric("Assigned Patients", total_assigned)

        st.divider()

        st.subheader("🆕 Recent Patients")

        if all_patients:
            df = pd.DataFrame(all_patients, columns=[
                "ID", "Name", "Symptoms", "Status", "Date", "Time"
            ])
            st.dataframe(df.tail(10), width="stretch")
        else:
            st.info("No patients found")

    elif menu == "➕ Add Patient":

        import random
        import sqlite3 as _sqlite3

        st.subheader("➕ Create Patient Account")
        st.caption("Fill in patient details to register a new patient in the system.")

        # ── Auto-generate credentials ──
        rand_num = random.randint(1000, 9999)
        def_username  = f"patient_{rand_num}"
        def_password  = f"pat{rand_num}"
        gen_patient_id = f"PAT-{rand_num}"

        st.info(f"🔑 **Auto-generated Patient ID:** `{gen_patient_id}`  ·  You can change the username/password below.")

        # ── Basic credentials ──
        col1, col2 = st.columns(2)
        with col1:
            sp_username = st.text_input("Username", value=def_username)
            sp_password = st.text_input("Password", value=def_password, type="password")
            sp_phone    = st.text_input("Phone / Mobile", placeholder="e.g. 9876543210")
            sp_email    = st.text_input("Email (optional)")
        with col2:
            sp_name   = st.text_input("Full Name")
            sp_age    = st.number_input("Age", 1, 120, value=30)
            sp_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            sp_blood  = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

        sp_address = st.text_input("Address (optional)")
        sp_city    = st.text_input("City (optional)")

        st.divider()
        st.subheader("📋 Clinical Profile")

        sp_emergency  = st.text_input("Emergency Contact Number", placeholder="e.g. 9876500000")
        sp_allergies  = st.text_area("Allergies", placeholder="e.g. Penicillin, Peanuts", height=70)
        sp_chronic    = st.text_area("Chronic / Existing Diseases", placeholder="e.g. Type-2 Diabetes, Hypertension", height=70)
        sp_prev_dis   = st.text_area("Previous Diagnosed Diseases", placeholder="e.g. Pneumonia (2024)", height=60)
        sp_prev_meds  = st.text_area("Previous Medications", placeholder="e.g. Metformin 500mg daily", height=60)
        sp_prev_rep   = st.text_area("Past Medical Reports Summary", placeholder="e.g. HbA1c: 7.2% (June 2026)", height=60)

        if st.button("✅ Create Patient Account", type="primary"):
            if not sp_username or not sp_password:
                st.warning("⚠️ Username and password are required.")
            elif not sp_name:
                st.warning("⚠️ Please enter the patient's full name.")
            else:
                res = add_user(
                    username=sp_username,
                    password=sp_password,
                    role="patient",
                    name=sp_name,
                    age=int(sp_age),
                    blood=sp_blood,
                    phone=sp_phone,
                    email=sp_email if sp_email else None,
                    patient_id=gen_patient_id,
                    emergency_contact=sp_emergency if sp_emergency else None,
                    allergies=sp_allergies if sp_allergies else None,
                    chronic_diseases=sp_chronic if sp_chronic else None,
                    previous_diseases=sp_prev_dis if sp_prev_dis else None,
                    previous_medications=sp_prev_meds if sp_prev_meds else None,
                    previous_reports=sp_prev_rep if sp_prev_rep else None,
                    gender=sp_gender,
                    address=sp_address if sp_address else None,
                    city=sp_city if sp_city else None,
                )
                # Save patient_id separately since add_user checks uniqueness
                if res == "created":
                    try:
                        _conn = _sqlite3.connect("hospital.db")
                        _c    = _conn.cursor()
                        _c.execute("UPDATE users SET patient_id=? WHERE username=?", (gen_patient_id, sp_username))
                        _conn.commit()
                        _conn.close()
                    except Exception as _e:
                        print("patient_id update error:", _e)

                if res == "created":
                    st.success(f"✅ Patient Account Created Successfully!")
                    st.markdown(f"""
<div style='background:#eef5ff;border-left:5px solid #0f62fe;border-radius:10px;padding:14px 18px;margin-top:8px;'>
<b>🪪 Patient ID:</b> <code>{gen_patient_id}</code><br>
<b>👤 Username:</b> <code>{sp_username}</code> &nbsp;|&nbsp; <b>🔑 Password:</b> <code>{sp_password}</code><br>
<b>📛 Name:</b> {sp_name} &nbsp;|&nbsp; <b>🩸 Blood Group:</b> {sp_blood} &nbsp;|&nbsp; <b>📞 Phone:</b> {sp_phone or '—'}
</div>
""", unsafe_allow_html=True)
                elif res == "exists":
                    st.error("❌ Username already exists. Please choose a different username.")
                elif res == "email_exists":
                    st.error("❌ This email is already registered with another account.")
                elif res == "phone_exists":
                    st.error("❌ This phone number is already registered with another account.")
                elif res == "patient_exists":
                    st.error("❌ A patient with this ID already exists. Refresh to get a new ID.")
                else:
                    st.error(f"❌ Account creation failed: {res}")

    # ════════════════════════════════════════════════════════════════════════
    # 📱 CREATE ACCOUNT  (Staff-level: Patient, Doctor, Staff)
    # ════════════════════════════════════════════════════════════════════════
    elif menu == "📱 Create Account":
        import random as _rand_mod
        st.markdown("## 📱 Create New Account")
        st.caption("Create Patient, Doctor, or Staff accounts from the staff panel.")
        st.divider()

        role = st.selectbox("👤 Account Role", ["Patient", "Doctor", "Staff"],
                            help="Staff can create Patient, Doctor, or Staff accounts")

        # Stable random seed per role
        _sk = f"stf_rand_{role}"
        if _sk not in st.session_state:
            st.session_state[_sk] = _rand_mod.randint(1000, 9999)
        _rn = st.session_state[_sk]

        _pfx = {"Patient": "PAT", "Doctor": "DOC", "Staff": "STF"}
        _gen_id = f"{_pfx[role]}-{_rn}"

        st.markdown(f"""
        <div style='background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;
             padding:12px 18px;margin-bottom:12px;'>
          <b>🪪 Auto-Generated ID:</b> <code style='background:#e0f2fe;padding:2px 6px;
          border-radius:4px;color:#0369a1;'>{_gen_id}</code>
          &nbsp;&mdash;&nbsp; You may customise username and password below.
        </div>
        """, unsafe_allow_html=True)

        # ── Credentials ──
        st.markdown("#### 🔐 Account Credentials")
        _cr1, _cr2 = st.columns(2)
        with _cr1:
            _uname   = st.text_input("Username ✱", value=f"{role.lower()}_{_rn}",
                                     key="stf_cre_uname")
            _pwd     = st.text_input("Password ✱", value=f"{role[:3].lower()}{_rn}@Hosp",
                                     type="password", key="stf_cre_pwd")
            _pwd_cf  = st.text_input("Confirm Password ✱", type="password",
                                     key="stf_cre_pwdcf")
        with _cr2:
            _nl      = "Full Name ✱"
            _name    = st.text_input(_nl, placeholder="Enter full legal name",
                                     key="stf_cre_name")
            _email   = st.text_input("Email Address", placeholder="user@example.com",
                                     key="stf_cre_email")
            _phone   = st.text_input("Mobile Number", placeholder="10-digit number",
                                     key="stf_cre_phone")

        # ── Personal details ──
        st.markdown("#### 📋 Personal Details")
        _p1, _p2, _p3 = st.columns(3)
        with _p1:
            _age    = st.number_input("Age", 1, 120, 30, key="stf_cre_age")
        with _p2:
            _gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                                   key="stf_cre_gen")
        with _p3:
            _blood  = st.selectbox("Blood Group",
                ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"],
                key="stf_cre_blood")
        _a1, _a2 = st.columns(2)
        with _a1:
            _addr = st.text_input("Address", placeholder="Street / Area",
                                  key="stf_cre_addr")
        with _a2:
            _city = st.text_input("City", placeholder="e.g. Visakhapatnam",
                                  key="stf_cre_city")

        # ── Role-specific fields ──
        _patient_id = _doctor_id = _staff_id = _hospital_id = None
        _ec = _allg = _chron = _prev_d = _prev_m = _prev_r = None
        _spec = _qual = _exp = _dept = _doc_img = None
        _avail = "Available"

        if role == "Patient":
            _patient_id = _gen_id
            st.markdown("#### 🩺 Clinical Profile")
            _ec    = st.text_input("Emergency Contact",
                       placeholder="e.g. 9876500000", key="stf_ec")
            _ca, _cb = st.columns(2)
            with _ca:
                _allg  = st.text_area("Allergies",
                           placeholder="e.g. Penicillin", height=75, key="stf_allg")
                _chron = st.text_area("Chronic Diseases",
                           placeholder="e.g. Diabetes", height=75, key="stf_chron")
            with _cb:
                _prev_d = st.text_area("Previous Diseases",
                            placeholder="e.g. Pneumonia (2024)", height=75,
                            key="stf_pvd")
                _prev_m = st.text_area("Previous Medications",
                            placeholder="e.g. Metformin 500mg", height=75,
                            key="stf_pvm")
            _prev_r = st.text_area("Medical Reports Summary",
                          placeholder="e.g. HbA1c: 7.2%", key="stf_pvr")

        elif role == "Doctor":
            _doctor_id = _gen_id
            SPECS = [
                "General Physician", "Cardiologist", "Neurologist", "Orthopedic",
                "Dermatologist", "Pediatrician", "Gynecologist", "Psychiatrist",
                "Pulmonologist", "Gastroenterologist", "Oncologist",
                "Emergency Medicine", "Internal Medicine", "Endocrinologist",
                "Nephrologist", "Ophthalmologist", "ENT Specialist", "Urologist",
                "Radiologist", "Anesthesiologist", "Pathologist", "Physiotherapist"
            ]
            st.markdown("#### 👨‍⚕️ Doctor Details")
            _d1, _d2 = st.columns(2)
            with _d1:
                _spec  = st.selectbox("Specialization ✱", SPECS, key="stf_spec")
                _qual  = st.text_input("Qualification",
                           placeholder="e.g. MBBS, MD", key="stf_qual")
            with _d2:
                _exp   = st.text_input("Experience",
                           placeholder="e.g. 5 Years", key="stf_exp")
                _avail = st.selectbox("Availability",
                           ["Available", "Busy", "Away"], key="stf_avail")
            _dept = st.text_input("Department", value=_spec or "General",
                                  key="stf_dept")
            _branch = st.selectbox("Hospital Branch", [
                "Prasad Hospitals, Gajuwaka",
                "Prasad Hospitals, MVP Colony",
                "Prasad Hospitals, Kukatpally",
            ], key="stf_branch_doc")
            _hospital_id = _branch
            _city = "hyderabad" if "Kukatpally" in _branch else "visakhapatnam"
            _doc_img = st.file_uploader("Doctor Photo (optional)",
                           type=["jpg", "jpeg", "png"], key="stf_doc_img")

        elif role == "Staff":
            _staff_id = _gen_id
            st.markdown("#### 🏷️ Staff Details")
            _s1, _s2 = st.columns(2)
            with _s1:
                _dept  = st.text_input("Department",
                           placeholder="e.g. ICU, Radiology", key="stf_dept_s")
                _desig = st.text_input("Designation",
                           placeholder="e.g. Senior Nurse", key="stf_desig")
            with _s2:
                _sbranch = st.selectbox("Hospital Branch", [
                    "Prasad Hospitals, Gajuwaka",
                    "Prasad Hospitals, MVP Colony",
                    "Prasad Hospitals, Kukatpally",
                ], key="stf_branch_s")
                _avail = st.selectbox("Status",
                    ["Available", "On Leave", "Inactive"], key="stf_avail_s")
            _hospital_id = _sbranch
            _city = "hyderabad" if "Kukatpally" in _sbranch else "visakhapatnam"

        st.divider()

        _btn1, _btn2 = st.columns([3, 1])
        with _btn1:
            _clicked = st.button("✅ Create Account", type="primary",
                                 use_container_width=True, key="stf_create_btn")
        with _btn2:
            if st.button("🔄 Reset", use_container_width=True, key="stf_reset_btn"):
                if _sk in st.session_state:
                    del st.session_state[_sk]
                st.rerun()

        if _clicked:
            _errs = []
            if not _uname.strip():
                _errs.append("Username is required.")
            if not _pwd.strip() or len(_pwd) < 6:
                _errs.append("Password must be ≥ 6 characters.")
            if _pwd != _pwd_cf:
                _errs.append("Passwords do not match.")
            if not _name.strip():
                _errs.append("Full name is required.")
            if _errs:
                for _e in _errs:
                    st.error(f"❌ {_e}")
            else:
                _res = add_user(
                    username=_uname.strip(),
                    password=_pwd.strip(),
                    role=role.lower(),
                    name=_name.strip(),
                    age=int(_age),
                    blood=_blood,
                    phone=_phone.strip() or None,
                    email=_email.strip() or None,
                    patient_id=_patient_id,
                    doctor_id=_doctor_id,
                    staff_id=_staff_id,
                    hospital_id=_hospital_id,
                    emergency_contact=_ec,
                    allergies=_allg,
                    chronic_diseases=_chron,
                    previous_diseases=_prev_d,
                    previous_medications=_prev_m,
                    previous_reports=_prev_r,
                    gender=_gender,
                    address=_addr.strip() or None,
                    city=_city.strip() if _city else None,
                    specialization=_spec,
                    qualification=_qual,
                    experience=_exp,
                    department=_dept or "General",
                    availability=_avail,
                )
                _err_mp = {
                    "exists": "Username already taken.",
                    "email_exists": "Email already registered.",
                    "phone_exists": "Phone already registered.",
                    "patient_exists": "Patient ID already exists.",
                    "doctor_exists": "Doctor ID already exists.",
                    "staff_exists": "Staff ID already exists.",
                }
                if _res in _err_mp:
                    st.error(f"❌ {_err_mp[_res]}")
                else:
                    # Save doctor image if provided
                    if role == "Doctor" and _doc_img:
                        try:
                            os.makedirs("doctor_images", exist_ok=True)
                            from utils import process_profile_image
                            _ib = process_profile_image(_doc_img)
                            _ip = f"doctor_images/{_uname}.png"
                            with open(_ip, "wb") as _f:
                                _f.write(_ib)
                        except Exception as _de:
                            st.warning(f"Photo save failed: {_de}")

                    st.success(f"✅ {role} account created!")
                    st.markdown(f"""
                    <div style='background:#f0fdf4;border:1px solid #6ee7b7;
                         border-radius:12px;padding:16px 20px;margin-top:10px;'>
                      <b style='font-size:16px;'>👤 {_name}</b>
                      &nbsp;<span style='background:#dcfce7;color:#15803d;
                      padding:2px 8px;border-radius:10px;font-size:11px;
                      font-weight:700;text-transform:uppercase;'>{role}</span><br><br>
                      <table style='font-size:13px;border-collapse:collapse;width:100%;'>
                        <tr>
                          <td style='padding:3px 8px;'><b>🪪 ID</b></td>
                          <td><code style='background:#d1fae5;padding:2px 6px;
                          border-radius:4px;'>{_gen_id}</code></td>
                          <td style='padding:3px 8px;'><b>👤 Username</b></td>
                          <td><code style='background:#d1fae5;padding:2px 6px;
                          border-radius:4px;'>{_uname}</code></td>
                        </tr>
                        <tr>
                          <td style='padding:3px 8px;'><b>🔑 Password</b></td>
                          <td><code style='background:#d1fae5;padding:2px 6px;
                          border-radius:4px;'>{_pwd}</code></td>
                          <td style='padding:3px 8px;'><b>📞 Phone</b></td>
                          <td>{_phone or '—'}</td>
                        </tr>
                        <tr>
                          <td style='padding:3px 8px;'><b>📧 Email</b></td>
                          <td colspan='3'>{_email or '—'}</td>
                        </tr>
                      </table>
                      <p style='margin:10px 0 0 0;font-size:12px;color:#6b7280;'>
                        ⚠️ Share credentials securely with the account holder.
                      </p>
                    </div>
                    """, unsafe_allow_html=True)
                    if _sk in st.session_state:
                        del st.session_state[_sk]

    # ════════════════════════════════════════════════════════════════════════
    # 🔐 MANAGE ACCOUNTS  (Staff-level: view + reset password)
    # ════════════════════════════════════════════════════════════════════════
    elif menu == "🔐 Manage Accounts":
        import sqlite3 as _sq
        st.markdown("## 🔐 Manage Accounts")
        st.caption("View accounts and reset passwords. Staff can manage Patient and Staff accounts.")
        st.divider()

        _fil = st.selectbox("Filter by Role",
            ["All", "patient", "doctor", "staff"])
        _srch = st.text_input("🔍 Search by name or username")

        _conn_m = _sq.connect("hospital.db")
        _c_m    = _conn_m.cursor()
        _q = """
            SELECT id, username, name, role, phone, email, patient_id,
                   doctor_id, staff_id, hospital_id, city, status
            FROM users
        """
        if _fil != "All":
            _c_m.execute(_q + " WHERE LOWER(role)=? ORDER BY name", (_fil,))
        else:
            _c_m.execute(_q + " ORDER BY role, name")
        _rows = _c_m.fetchall()
        _conn_m.close()

        if _srch:
            _rows = [r for r in _rows
                     if _srch.lower() in str(r[1]).lower()
                     or _srch.lower() in str(r[2]).lower()]

        if not _rows:
            st.info("No accounts found.")
        else:
            st.markdown(f"**{len(_rows)} account(s)**")
            _badge = {
                "patient": ("#dbeafe", "#1e40af"),
                "doctor":  ("#dcfce7", "#15803d"),
                "staff":   ("#fef9c3", "#854d0e"),
            }
            for _row in _rows:
                _uid, _un, _fn, _rol, _ph, _em, _pid, _did, _sid, _hid, _ct, _st = _row
                _bc, _fc = _badge.get(_rol, ("#f1f5f9", "#334155"))
                with st.expander(
                    f"👤 {_fn or _un}  —  {_rol.title()} | {_ct or '—'}",
                    expanded=False
                ):
                    _m1, _m2 = st.columns(2)
                    with _m1:
                        st.markdown(
                            f"<span style='background:{_bc};color:{_fc};"
                            f"padding:2px 8px;border-radius:10px;font-size:11px;"
                            f"font-weight:700;text-transform:uppercase;'>{_rol}</span>",
                            unsafe_allow_html=True
                        )
                        st.write(f"**Username:** `{_un}`")
                        st.write(f"**ID:** {_pid or _did or _sid or _hid or '—'}")
                        st.write(f"**Phone:** {_ph or '—'}")
                    with _m2:
                        st.write(f"**Email:** {_em or '—'}")
                        st.write(f"**City:** {_ct or '—'}")
                        st.write(f"**Branch:** {_hid or '—'}")
                        st.write(f"**Status:** {_st or 'Active'}")

                    st.markdown("**🔑 Reset Password**")
                    _npw = st.text_input(
                        f"New password for `{_un}`",
                        type="password",
                        key=f"stf_pw_{_uid}",
                        placeholder="Min 6 characters"
                    )
                    if st.button("💾 Update Password",
                                 key=f"stf_upw_{_uid}"):
                        if _npw and len(_npw) >= 6:
                            try:
                                _cw = _sq.connect("hospital.db")
                                _cc = _cw.cursor()
                                _cc.execute(
                                    "UPDATE users SET password=? WHERE id=?",
                                    (_npw, _uid)
                                )
                                _cw.commit()
                                _cw.close()
                                st.success(f"✅ Password updated for `{_un}`.")
                            except Exception as _pe:
                                st.error(f"Failed: {_pe}")
                        else:
                            st.warning("⚠️ Password must be ≥ 6 characters.")

    elif menu == "🚨 Emergency Patients":

        st.subheader("🚨 Emergency Patients")

        patients = get_active_patients()

        if patients:
            df = pd.DataFrame(
                patients,
                columns=["ID", "Name", "Symptoms", "Status"]
            )

            st.dataframe(df, width="stretch")

            selected_id = st.selectbox("Select Patient Case ID", df["ID"])

            row = df[df["ID"] == selected_id].iloc[0]
            symptoms = row["Symptoms"]

            st.info(f"🤒 Symptoms: {symptoms}")

            ai_reply = get_ai_response(symptoms)
            st.success(f"🤖 AI Suggestion: {ai_reply}")

            spec = map_symptom_to_specialization(symptoms)
            st.success(f"🩺 Required Department: {spec}")

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button("👨‍⚕️ Assign Doctor", key=f"assign_{selected_id}"):

                    doctors = get_users()
                    matched = None

                    for d in doctors:
                        if len(d) > 3 and d[3] == "doctor":
                            extra = get_doctor_extra(d[1])

                            if extra and len(extra) > 1 and str(extra[1]).lower() == spec.lower():
                                matched = d
                                break

                    update_patient_status(selected_id, "ASSIGNED")

                    if matched:
                        st.success(f"👨‍⚕️ Assigned Doctor: Dr. {matched[4]}")

                        image_path = f"doctor_images/{matched[1]}.png"
                        extra_matched = get_doctor_extra(matched[1])
                        db_image = extra_matched[6] if (extra_matched and len(extra_matched) > 6) else None
                        
                        if db_image:
                            st.image(db_image, width=120)
                        elif os.path.exists(image_path):
                            st.image(image_path, width=120)

                        st.info(f"""
🩺 Specialization: {spec}

📞 Phone: {matched[6]}
""")
                    else:
                        st.warning("No matching doctor found")

                    st.rerun()

            with c2:
                if st.button("🚑 Ambulance Status", key=f"ambu_{selected_id}"):
                    for step in simulate_ambulance():
                        st.warning(step)

            with c3:
                if st.button("🏥 Find Hospital", key=f"hos_{selected_id}"):

                    lat, lon = get_live_location()

                    hospitals = get_hospitals("chennai", spec, lat, lon)

                    if isinstance(hospitals, pd.DataFrame):
                        hospitals = hospitals.to_dict(orient="records")

                    best = select_best_hospital(hospitals)

                    if best:
                        st.success(f"🏥 {best['name']}")

                        st.info(f"""
📍 Address: {best.get('address', 'N/A')}

📞 Phone: {best.get('phone', 'N/A')}

🩺 Department: {best.get('specialization', 'N/A')}

⭐ Rating: {best.get('rating', 'N/A')}

📏 Distance: {best.get('distance', 'N/A')} KM
""")

                        if best.get("lat") and best.get("lon"):
                            st.markdown(
                                get_map_embed(best["lat"], best["lon"]),
                                unsafe_allow_html=True
                            )
                    else:
                        st.warning("No hospital found")

        else:
            st.success("No emergency patients")

    elif menu == "🏨 Hospital Beds":
        st.subheader("🏨 Hospital Beds & ICU Management")
        from database import get_all_hospital_beds, update_hospital_beds, get_hospital_beds
        
        beds_list = get_all_hospital_beds()
        
        if not beds_list:
            st.warning("No hospitals found in the beds database.")
        else:
            hosp_names = [h['hospital_name'] for h in beds_list]
            selected_hosp = st.selectbox("Select Hospital to Manage", hosp_names)
            
            stats = get_hospital_beds(selected_hosp)
            if stats:
                st.info(f"""
                🏥 **Hospital:** {selected_hosp}
                ⭐ **Emergency Support:** {stats['emergency_support']}
                🛌 **Total Beds:** {stats['total_beds']} | 🛌 **Available Beds:** {stats['available_beds']}
                🏥 **Total ICU:** {stats['total_icu']} | 🏥 **Available ICU:** {stats['available_icu']}
                """)
                
                with st.form("update_beds_form"):
                    new_avail = st.number_input("Update Available Beds Count", min_value=0, max_value=stats['total_beds'], value=stats['available_beds'])
                    new_avail_icu = st.number_input("Update Available ICU Beds Count", min_value=0, max_value=stats['total_icu'], value=stats['available_icu'])
                    
                    sub_btn = st.form_submit_button("Update Bed Availability")
                    if sub_btn:
                        update_hospital_beds(selected_hosp, new_avail, new_avail_icu)
                        st.success(f"Successfully updated availability for {selected_hosp}!")
                        st.rerun()

    elif menu == "📋 Shared Records":
        st.subheader("📋 Shared Clinical Patient Records (Hospital Wide)")
        st.caption("Clinical details sent dynamically when a patient books a consultation or is flagged as an emergency.")
        
        from database import get_shared_history, get_all_hospital_beds
        import json
        
        beds_list = get_all_hospital_beds()
        if not beds_list:
            st.warning("No hospitals configured in the beds database.")
        else:
            hosp_names = [h['hospital_name'] for h in beds_list]
            selected_hosp = st.selectbox("Filter by Hospital Location", hosp_names)
            
            records = get_shared_history(hospital_name=selected_hosp)
            if not records:
                st.info(f"No shared clinical records found for {selected_hosp}.")
            else:
                for r in records:
                    try:
                        payload = json.loads(r['shared_data'])
                    except:
                        payload = {}
                        
                    st.markdown("---")
                    st.markdown(f"### 👤 Patient: {payload.get('patient_name')} ({payload.get('patient_id')})")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Age:** {payload.get('age')} | **Gender:** {payload.get('gender')}")
                        st.write(f"**Phone:** {payload.get('phone')}")
                        st.write(f"**Emergency Contact:** {payload.get('emergency_contact')}")
                    with c2:
                        st.write(f"**Severity Level:** :red[{payload.get('emergency_severity')}]")
                        st.write(f"**Risk Score:** {payload.get('risk_score')}%")
                        st.write(f"**Shared Time:** {payload.get('timestamp')}")
                        
                    st.info(f"📋 **Current Symptoms:** {payload.get('current_symptoms')}")
                    st.success(f"🤖 **Predicted Illness:** {payload.get('predicted_disease')}")
                    
                    with st.expander("🩺 View Complete Profile & Contacts"):
                        st.write(f"🚫 **Allergies:** {payload.get('allergies')}")
                        st.write(f"🩺 **Existing Chronic Diseases:** {payload.get('existing_diseases')}")
                        st.write(f"💊 **Previous Diseases:** {payload.get('previous_diseases')}")
                        st.write(f"💊 **Previous Medications:** {payload.get('previous_medications')}")
                        st.write(f"📋 **Past Medical Reports Summary:** {payload.get('previous_reports')}")
                        st.write(f"🚑 **First Aid Advised:** {payload.get('first_aid_recommendations')}")
                        st.write(f"💊 **Medication Recommendation:** {payload.get('medication_recommendations')}")

    elif menu == "👨‍⚕️ Assigned Patients":

        st.subheader("👨‍⚕️ Assigned Patients")

        data = get_assigned_patients(st.session_state.user)

        if data:
            df = pd.DataFrame(data, columns=[
                "ID", "Name", "Symptoms", "Result",
                "Date", "Time", "Status",
                "Assigned Doctor", "Hospital"
            ])

            st.dataframe(df, width="stretch")

            for _, row in df.iterrows():
                st.markdown("---")
                st.success(f"👤 {row['Name']}")
                st.write(f"🩺 Symptoms: {row['Symptoms']}")
                st.write(f"🏥 Hospital: {row['Hospital']}")
                st.write(f"📌 Status: {row['Status']}")
                st.write(f"👨‍⚕️ Doctor: {row['Assigned Doctor']}")

        else:
            st.info("No assigned patients")

    elif menu == "👥 All Patients":

        st.subheader("👥 All Patients")

        patients = get_all_patients()

        if patients:
            df = pd.DataFrame(patients, columns=[
                "ID", "Name", "Symptoms", "Status", "Date", "Time"
            ])

            search = st.text_input("🔍 Search Patient")

            if search:
                df = df[df["Name"].astype(str).str.contains(search, case=False)]

            st.dataframe(df, width="stretch")

            if not df.empty:
                selected = st.selectbox("Select Patient", df["Name"])

                if st.button("View Patient Details"):
                    st.session_state["view_patient"] = selected
                    st.rerun()
        else:
            st.info("No patients found")

    elif menu == "📜 Patient History":

        st.subheader("📜 Patient History")

        history = get_history("all")

        if history:
            df = pd.DataFrame(history, columns=[
                "Name", "Symptoms", "Result", "Date", "Time"
            ])
            st.dataframe(df, width="stretch")
        else:
            st.info("No patient history found")

    elif menu == "🧠 Patient AI Assistant":

        st.subheader("🧠 Patient AI Assistant")

        user_input = st.text_area("Enter Patient Symptoms / Question")

        if st.button("Analyze Patient Symptoms"):

            if user_input:

                ai_reply = get_ai_response(user_input)
                st.info(f"🤖 AI Response: {ai_reply}")

                spec = map_symptom_to_specialization(user_input)
                st.success(f"👨‍⚕️ Suggested Department: {spec}")

                priority = detect_status(user_input)
                st.info(f"📌 Priority Level: {priority}")

                if priority == "EMERGENCY":
                    st.error("🚨 Emergency Case")
                elif priority == "HIGH":
                    st.warning("⚠️ High Priority")
                else:
                    st.success("Normal Case")

            else:
                st.warning("Enter patient symptoms")

    elif menu == "🏨 Prasad Referral Center":
        st.subheader("🏨 Prasad Hospital Emergency Referral Center")
        
        action = st.radio("Select Action", ["🔍 Search & Identify Patient", "➕ Register New Patient"])
        
        if action == "🔍 Search & Identify Patient":
            st.write("First identify the patient using Patient ID or Phone Number.")
            search_val = st.text_input("Enter Patient ID or phone number", key="referral_search_query")
            
            if search_val:
                import sqlite3
                conn = sqlite3.connect("hospital.db")
                c = conn.cursor()
                c.execute("""
                SELECT username, name, age, gender, phone, patient_id, allergies, chronic_diseases, previous_medications, previous_diseases, previous_reports 
                FROM users 
                WHERE patient_id=? OR phone=?
                """, (search_val, search_val))
                pat = c.fetchone()
                conn.close()
                
                if pat:
                    p_username, p_name, p_age, p_gender, p_phone, p_id, p_allergies, p_chronic, p_meds, p_diseases, p_reports = pat
                    st.success(f"✅ Patient Identified: {p_name} (ID: {p_id})")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Patient ID:** {p_id}")
                        st.write(f"**Full Name:** {p_name}")
                        st.write(f"**Age / Gender:** {p_age} / {p_gender}")
                    with c2:
                        st.write(f"**Phone:** {p_phone}")
                        st.write(f"**Allergies:** {p_allergies or 'None'}")
                        st.write(f"**Chronic Diseases:** {p_chronic or 'None'}")
                        
                    with st.expander("📜 View Full Medical History & Reports"):
                        st.write(f"**Previous Diseases:** {p_diseases or 'None'}")
                        st.write(f"**Previous Medications:** {p_meds or 'None'}")
                        st.write(f"**Previous Reports Summary:** {p_reports or 'None'}")
                        
                        from database import get_history
                        h_events = get_history(p_username)
                        if h_events:
                            st.write("**Past consultations:**")
                            for h in h_events:
                                st.info(f"📅 {h[3]} at {h[4]} | Symptoms: {h[1]} | Diagnosis & Treatment: {h[2]}")
                        else:
                            st.write("No past consultation history.")
                            
                        conn = sqlite3.connect("hospital.db")
                        c = conn.cursor()
                        c.execute("SELECT id, hospital, status, symptoms, result, created_at FROM hospital_requests WHERE patient_name=?", (p_username,))
                        em_events = c.fetchall()
                        conn.close()
                        if em_events:
                            st.write("**Past Emergency Referrals:**")
                            for em in em_events:
                                st.warning(f"🚨 {em[5]} | Referred to: {em[1]} | Symptoms: {em[3]} | Status: {em[2]}")
                        else:
                            st.write("No past emergency records.")
                            
                    st.write("---")
                    st.subheader("➕ Create Emergency Referral")
                    current_symptoms = st.text_area("Enter Current Emergency Symptoms", placeholder="e.g. Severe chest pain and sweating")
                    
                    if current_symptoms:
                        from ui.patient_ui import map_symptom_to_specialization, auto_assign_doctor
                        spec = map_symptom_to_specialization(current_symptoms)
                        assigned_doc = auto_assign_doctor(current_symptoms)
                        
                        from hospitals import get_hospitals
                        hosp_df = get_hospitals("visakhapatnam", current_symptoms)
                        hosp_list = hosp_df["name"].tolist() if not hosp_df.empty else []
                        
                        if hosp_list:
                            receiving_hosp = hosp_list[0]
                            p_lat = 17.6868
                            p_lon = 83.2185
                            
                            st.info(f"📋 **Automated Triage Routing:** Target Hospital: **{receiving_hosp}** | Specialty: **{spec}** | Prasad Doctor: **{assigned_doc}**")
                            
                            if st.button("⚡ Dispatch & Transmit Automated Referral Package", key=f"auto_dispatch_{p_id}"):
                                import random
                                em_id = f"EMERG-{random.randint(1000, 9999)}"
                                ref_id = f"REF-{random.randint(1000, 9999)}"
                                
                                from database import save_referral_request, save_emergency
                                protocol_key = "heart_attack"
                                if "neuro" in current_symptoms.lower() or "stroke" in current_symptoms.lower():
                                    protocol_key = "stroke"
                                elif "respiratory" in current_symptoms.lower() or "breathless" in current_symptoms.lower():
                                    protocol_key = "asthma"
                                    
                                from database import get_medical_knowledge
                                p_data = get_medical_knowledge("protocol", protocol_key)
                                first_aid_inst = p_data.get("immediate_response") if p_data else "Keep the patient resting and calm. Call ambulance."
                                
                                save_emergency(
                                    emergency_id=em_id,
                                    patient_id=p_id,
                                    patient_name=p_username,
                                    emergency_type="Cardiac Emergency" if protocol_key=="heart_attack" else ("Neurological Emergency" if protocol_key=="stroke" else "Respiratory Emergency"),
                                    lat=p_lat,
                                    lon=p_lon,
                                    address="Visakhapatnam Center",
                                    severity="HIGH",
                                    status='PENDING',
                                    assigned_doctor=assigned_doc,
                                    first_aid=first_aid_inst
                                )
                                
                                success = save_referral_request(
                                    patient_name=p_username,
                                    hospital=receiving_hosp,
                                    symptoms=current_symptoms,
                                    result=f"EMERGENCY | Doctor: {assigned_doc} | Referral ID: {ref_id}",
                                    lat=p_lat,
                                    lon=p_lon,
                                    emergency_id=em_id,
                                    referral_id=ref_id,
                                    assigned_doctor=assigned_doc,
                                    patient_id=p_id
                                )
                                if success:
                                    st.success(f"✅ Automated referral package {ref_id} transmitted to {receiving_hosp} and ambulance requested!")
                                    st.rerun()
                                else:
                                    st.error("Failed to create referral record.")
                        else:
                            st.warning("No nearby hospitals found in the database to refer to.")
                else:
                    st.error("No patient profile found matching that Patient ID or Phone Number.")
                    
        elif action == "➕ Register New Patient":
            st.subheader("➕ Register New Emergency Patient Profile")
            new_name = st.text_input("Full Name")
            new_phone = st.text_input("Phone Number")
            new_age = st.number_input("Age", 1, 120, 30)
            new_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            new_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            new_address = st.text_area("Address")
            new_allergies = st.text_area("Allergies", value="None")
            new_chronic = st.text_area("Chronic Conditions", value="None")
            
            if st.button("Create Profile & Generate Patient ID"):
                if new_name and new_phone:
                    import random
                    new_pid = f"P-{random.randint(1000, 9999)}"
                    new_user = "p_" + new_phone[-4:] + str(random.randint(10, 99))
                    
                    from database import add_user
                    res = add_user(
                        username=new_user,
                        password="1234",
                        role="patient",
                        name=new_name,
                        age=int(new_age),
                        blood=new_blood,
                        phone=new_phone
                    )
                    
                    if res == "created":
                        from database import update_patient_clinical_data
                        update_patient_clinical_data(
                            username=new_user,
                            allergies=new_allergies,
                            chronic_diseases=new_chronic,
                            previous_diseases="None",
                            previous_medications="None",
                            previous_reports="None",
                            emergency_contact=new_phone,
                            gender=new_gender
                        )
                        import sqlite3
                        conn = sqlite3.connect("hospital.db")
                        c = conn.cursor()
                        c.execute("UPDATE users SET patient_id=?, address=?, city=? WHERE username=?", (new_pid, new_address, "visakhapatnam", new_user))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Successfully registered patient {new_name}! Generated Patient ID: **{new_pid}**")
                        st.info(f"Temporary credentials: Username: **{new_user}** | Password: **1234**")
                    else:
                        st.error(f"Failed to create account: {res}")
                else:
                    st.warning("Please fill in Name and Phone Number.")

        st.write("---")
        st.subheader("📡 Live Emergency Referral & Ambulance Tracking Dashboard")
        from database import get_prasad_referrals
        referrals = get_prasad_referrals()
        
        if referrals:
            for r in referrals:
                with st.expander(f"📋 Referral {r[10]} - Patient: {r[15]} ({r[3]})", expanded=False):
                    st.write(f"**Emergency ID:** {r[9]}")
                    st.write(f"**Receiving Hospital:** {r[2]}")
                    st.write(f"**Assigned Doctor:** {r[11]}")
                    st.write(f"**Ambulance Status / Vehicle:** {r[12]} / {r[13]}")
                    st.write(f"**Referral Timeline Stage:** {r[14]}")
                    st.write(f"**Last Updated:** {r[16]}")
                    
                    st.write("**Ambulance Tracking (Auto-Progression):**")
                    current_stage = r[12]
                    stages_seq = ["Requested", "Assigned", "Dispatched", "On The Way", "Arrived", "Completed"]
                    
                    next_stage = None
                    if current_stage in stages_seq:
                        curr_idx = stages_seq.index(current_stage)
                        if curr_idx < len(stages_seq) - 1:
                            next_stage = stages_seq[curr_idx + 1]
                            
                    st.info(f"Current Status: **{current_stage}** | Vehicle: **{r[13] or 'AMB-7788'}**")
                    
                    if next_stage:
                        if st.button(f"➡️ Advance Status to '{next_stage}'", key=f"btn_adv_{r[0]}"):
                            from database import update_referral_ambulance
                            update_referral_ambulance(r[0], next_stage, r[13] or "AMB-7788")
                            st.success(f"Status advanced to {next_stage}!")
                            st.rerun()
                    else:
                        st.success("✅ Ambulance Journey Completed.")
                            
                    st.write("**Referral Document Package:**")
                    from utils import generate_pdf_report
                    pdf_bytes = generate_pdf_report(r[1], r[4], r[5], 85)
                    st.download_button(
                        label="📥 Download Complete Referral PDF",
                        data=pdf_bytes,
                        file_name=f"Referral_{r[10]}.pdf",
                        mime="application/pdf",
                        key=f"dl_ref_pdf_{r[0]}"
                    )
        else:
            st.info("No emergency referral cases currently tracked.")

    elif menu == "📥 Received Referrals":
        st.subheader("📥 Received Emergency Referrals Packages")
        
        if not staff_hosp:
            st.warning("This account is not associated with a specific receiving hospital.")
        else:
            st.info(f"Incoming packages for: **{staff_hosp}**")
            from database import get_received_referrals
            incoming = get_received_referrals(staff_hosp)
            
            if incoming:
                for r in incoming:
                    r_id, p_user, hosp_name, status, symptoms, result, lat, lon, created, emerg_id, ref_id, doc_username, amb_status, amb_veh, ref_status, pat_id, updated = r
                    
                    with st.expander(f"🚨 Incoming Referral {ref_id} (Patient ID: {pat_id}) - Status: {status}", expanded=True):
                        st.write(f"**Emergency ID:** {emerg_id}")
                        st.write(f"**Reported Symptoms:** {symptoms}")
                        st.write(f"**Referral Sent At:** {created}")
                        st.write(f"**Assigned Doctor (Referral):** {doc_username}")
                        st.write(f"**Ambulance Status:** {amb_status} ({amb_veh})")
                        
                        from database import load_patient_clinical_data
                        p_details = load_patient_clinical_data(p_user)
                        
                        if p_details:
                            st.write(f"**Patient Name / Age / Gender:** {p_details.get('name')} / {p_details.get('age')} / {p_details.get('gender')}")
                            st.write(f"**Allergies:** {p_details.get('allergies')}")
                            st.write(f"**Chronic Diseases:** {p_details.get('chronic_diseases')}")
                        
                        st.write("**Referral Response Actions:**")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            if st.button("Accept Referral Package", key=f"acc_{r_id}"):
                                from database import update_referral_status
                                update_referral_status(r_id, "Accepted")
                                st.success("Referral Accepted!")
                                st.rerun()
                        with c2:
                            if st.button("Reject Referral Package", key=f"rej_{r_id}"):
                                from database import update_referral_status
                                update_referral_status(r_id, "Rejected")
                                st.warning("Referral Rejected!")
                                st.rerun()
                        with c3:
                            next_status = st.selectbox("Update Case Progress", ["Accepted", "Doctor Assigned", "Patient Arrived", "Treatment Started", "Completed"], index=["Accepted", "Doctor Assigned", "Patient Arrived", "Treatment Started", "Completed"].index(status) if status in ["Accepted", "Doctor Assigned", "Patient Arrived", "Treatment Started", "Completed"] else 0, key=f"prog_{r_id}")
                            if st.button("Update Progress", key=f"up_prog_{r_id}"):
                                from database import update_referral_status
                                update_referral_status(r_id, next_status)
                                st.success(f"Status updated to: {next_status}")
                                st.rerun()
                                
                        st.write("---")
                        from utils import generate_pdf_report
                        pdf_bytes = generate_pdf_report(p_user, symptoms, result, 85)
                        st.download_button(
                            label="📥 Download Transferred Referral PDF",
                            data=pdf_bytes,
                            file_name=f"Referral_Package_{ref_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_rec_pdf_{r_id}"
                        )
            else:
                st.info("No incoming referral packages found.")

    if "view_patient" in st.session_state:

        name = st.session_state["view_patient"]

        st.subheader(f"🧾 Patient Details: {name}")

        history = get_patient_full_history(name)

        if history:
            df = pd.DataFrame(history, columns=[
                "Symptoms", "Result", "Date", "Time"
            ])
            st.dataframe(df, width="stretch")
        else:
            st.info("No history found")

        if st.button("🔙 Back"):
            del st.session_state["view_patient"]
            st.rerun()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    # Automatic Sync / Live Refresh every 8 seconds
    import time
    if "refresh_time" not in st.session_state:
        st.session_state.refresh_time = time.time()
    if time.time() - st.session_state.refresh_time > 8:
        st.session_state.refresh_time = time.time()
        st.rerun()