import os
import streamlit as st
from dotenv import load_dotenv
from database import init_db, get_users, get_doctor_extra
from auth import login_user

st.set_page_config(
    page_title="AI Hospital",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

@st.cache_resource
def _init_db_once():
    init_db()
    return True

@st.cache_resource
def _init_datasets_once():
    import dataset_manager
    dataset_manager.initialize_datasets()
    return True

_init_db_once()
_init_datasets_once()

defaults = {
    "user": None,
    "role": None,
    "show_hospitals": False,
    "show_doctors": False,
    "selected_doctor": None,
    "active_emergency": "",
    "symptoms": "",
    "specialization": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clean_value(value):
    if value is None or str(value).lower() in ["none", "nan", ""]:
        return "Not Assigned"
    return value


if not st.session_state.user:

    st.markdown("""
<style>
header {visibility:hidden;height:0px;}
footer {visibility:hidden;}
#MainMenu {visibility:hidden;}

.stApp {
    background: linear-gradient(120deg, #eef7ff 0%, #eaf4ff 48%, #2f86ff 100%);
}

.main .block-container {
    padding-top: 1.5rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 100% !important;
}

.brand-row {
    display:flex;
    align-items:center;
    gap:14px;
    margin-bottom:45px;
}

.brand-icon {
    width:58px;
    height:58px;
    border-radius:18px;
    background:linear-gradient(135deg,#0f62fe,#003b95);
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:30px;
    box-shadow:0 12px 28px rgba(15,98,254,0.25);
}

.brand-title {
    font-size:27px;
    font-weight:900;
    color:#0b1f4d;
}

.brand-sub {
    font-size:15px;
    color:#38507a;
    margin-top:4px;
}

.hero-small {
    font-size:28px;
    color:#0f62fe;
    font-weight:900;
}

.hero-title {
    font-size:52px;
    line-height:1.1;
    font-weight:900;
    color:#071a44;
    margin-top:8px;
}

.hero-desc {
    font-size:17px;
    line-height:1.6;
    color:#23395d;
    max-width:540px;
    margin-top:20px;
    margin-bottom:28px;
}

.feature-row {
    display:flex;
    align-items:center;
    gap:16px;
    margin-bottom:14px;
}

.feature-icon {
    width:54px;
    height:54px;
    border-radius:16px;
    background:rgba(255,255,255,0.92);
    box-shadow:0 10px 24px rgba(18,54,100,0.08);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:24px;
}

.feature-title {
    font-size:16px;
    font-weight:900;
    color:#071a44;
}

.feature-sub {
    font-size:14px;
    color:#405982;
    margin-top:3px;
}

.stats-card {
    margin-top:25px;
    background:linear-gradient(135deg,#062b6f,#001d4f);
    color:white;
    border-radius:22px;
    padding:22px 26px;
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:10px;
    max-width:820px;
    box-shadow:0 18px 40px rgba(0,31,91,0.28);
}

.stat-num {
    font-size:28px;
    font-weight:900;
}

.stat-label {
    font-size:13px;
    opacity:0.9;
}

.login-shell {
    background: transparent !important;
    border:none !important;
    box-shadow:none !important;
    padding:0px !important;
    margin-top:12px;
    width:100%;
    max-width:520px;
    margin-left:auto;
    margin-right:auto;
}

.login-logo {
    width:78px;
    height:78px;
    margin:0 auto 18px auto;
    border-radius:50%;
    background:#eef5ff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:38px;
}

.login-heading {
    text-align:center;
    font-size:31px;
    font-weight:900;
    color:#071a44;
}

.login-sub {
    text-align:center;
    font-size:15px;
    color:#52688e;
    margin-bottom:24px;
}

.stTextInput label {
    color:#071a44 !important;
    font-weight:800 !important;
}

.stTextInput input {
    height:50px !important;
    border-radius:13px !important;
    border:1px solid #dce7f5 !important;
    font-size:15px !important;
}

.stButton > button {
    width:100%;
    height:50px;
    border-radius:13px;
    background:linear-gradient(90deg,#0969ff,#0057e7);
    color:white;
    border:none;
    font-size:16px;
    font-weight:900;
    margin-top:8px;
}

.stButton > button:hover {
    background:linear-gradient(90deg,#0057e7,#0047c2);
    color:white;
    border:none;
}

.role-title {
    text-align:center;
    color:#52688e;
    margin:22px 0 16px 0;
    font-size:14px;
}

.details-box {
    margin-top:16px;
    background:rgba(255,255,255,0.92);
    border:1px solid #dce7f5;
    border-radius:22px;
    padding:20px;
    color:#17345f;
    box-shadow:0 12px 28px rgba(0,0,0,0.08);
}

.details-box h4 {
    margin:0 0 10px 0;
    color:#071a44;
}

.doctor-name {
    font-size:20px;
    font-weight:900;
    color:#071a44;
}

.doctor-spec {
    font-size:15px;
    color:#2563eb;
    font-weight:700;
}

.profile-title {
    font-size:30px;
    font-weight:900;
    color:#071a44;
    margin-top:12px;
}

.profile-info {
    font-size:17px;
    margin-bottom:10px;
    color:#26456d;
}
</style>
""", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.15, 0.85], gap="medium")

    with col_left:
        st.markdown("""
<div class="brand-row">
<div class="brand-icon">✚</div>
<div>
<div class="brand-title">AI Hospital System</div>
<div class="brand-sub">Smart Healthcare. Better Decisions.</div>
</div>
</div>

<div class="hero-small">AI-Powered</div>

<div class="hero-title">
Hospital<br>
Management<br>
System
</div>

<div class="hero-desc">
Intelligent symptom analysis, smart hospital allocation,
emergency detection, doctor specialization matching and
advanced healthcare analytics.
</div>

<div class="feature-row">
<div class="feature-icon">🧠</div>
<div>
<div class="feature-title">AI Symptom Analysis</div>
<div class="feature-sub">Accurate AI based suggestions</div>
</div>
</div>

<div class="feature-row">
<div class="feature-icon">🏥</div>
<div>
<div class="feature-title">Smart Hospital Allocation</div>
<div class="feature-sub">Automatic emergency routing</div>
</div>
</div>

<div class="feature-row">
<div class="feature-icon">🚨</div>
<div>
<div class="feature-title">Emergency Detection</div>
<div class="feature-sub">Real-time risk identification</div>
</div>
</div>

<div class="feature-row">
<div class="feature-icon">📊</div>
<div>
<div class="feature-title">Analytics Dashboard</div>
<div class="feature-sub">Smart healthcare insights</div>
</div>
</div>

<div class="stats-card">
<div>
<div class="stat-num">20+</div>
<div class="stat-label">Hospitals</div>
</div>
<div>
<div class="stat-num">150+</div>
<div class="stat-label">Doctors</div>
</div>
<div>
<div class="stat-num">10K+</div>
<div class="stat-label">Patients</div>
</div>
<div>
<div class="stat-num">99%</div>
<div class="stat-label">Satisfaction</div>
</div>
</div>
""", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
<div class="login-shell">
<div class="login-logo">🛡️</div>
<div class="login-heading">Welcome Back!</div>
<div class="login-sub">Login to your account</div>
""", unsafe_allow_html=True)

        login_mode = st.radio("Login Method", ["Password Login", "Face Recognition", "Forgot Password", "Emergency Login"], horizontal=True)

        if login_mode == "Password Login":
            u = st.text_input("Username", placeholder="Enter your username")
            p = st.text_input("Password", type="password", placeholder="Enter your password")

            if st.button("Login"):
                if not u or not p:
                    st.warning("Enter username & password")
                else:
                    user = login_user(u, p)
                    if user:
                        from database import log_login_event
                        log_login_event(u, "Success")
                        st.session_state.user = u
                        st.session_state.role = user[3]
                        st.rerun()
                    else:
                        from database import log_login_event
                        log_login_event(u, "Failed")
                        st.error("Invalid credentials")

        elif login_mode == "Face Recognition":
            st.markdown("<p style='font-size:14px;color:#1d3557;'>Verify identity with dynamic liveness challenge (Blink, Smile, Identity checks).</p>", unsafe_allow_html=True)
            
            if "liveness_stage" not in st.session_state:
                st.session_state.liveness_stage = 1
                st.session_state.face_blink_passed = False
                st.session_state.face_smile_passed = False

            if st.session_state.liveness_stage == 1:
                st.info("📷 **Step 1: Blink Test**. Please close both eyes and capture.")
                img_data = st.camera_input("Capture Blink Frame", key="cam_blink")
                if img_data:
                    from PIL import Image
                    from face_auth import get_face_landmarks, calculate_ear
                    pil_img = Image.open(img_data).convert("RGB")
                    landmarks = get_face_landmarks(pil_img)
                    if landmarks:
                        left_ear, right_ear = calculate_ear(landmarks)
                        avg_ear = (left_ear + right_ear) / 2.0
                        if avg_ear < 0.20:
                            st.session_state.face_blink_passed = True
                            st.session_state.liveness_stage = 2
                            st.success("✅ Blink check passed!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Liveness check failed. Please close both eyes completely. (Detected EAR: {avg_ear:.2f})")
                    else:
                        st.error("No face detected. Look directly at the camera.")

            elif st.session_state.liveness_stage == 2:
                st.info("📷 **Step 2: Smile Test**. Please smile widely and capture.")
                img_data = st.camera_input("Capture Smile Frame", key="cam_smile")
                if img_data:
                    from PIL import Image
                    from face_auth import get_face_landmarks, calculate_smile_ratio
                    pil_img = Image.open(img_data).convert("RGB")
                    landmarks = get_face_landmarks(pil_img)
                    if landmarks:
                        smile_ratio = calculate_smile_ratio(landmarks)
                        if smile_ratio > 0.95:
                            st.session_state.face_smile_passed = True
                            st.session_state.liveness_stage = 3
                            st.success("✅ Smile check passed!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Liveness check failed. Please smile widely. (Detected Smile Ratio: {smile_ratio:.2f})")
                    else:
                        st.error("No face detected. Look directly at the camera.")

            elif st.session_state.liveness_stage == 3:
                st.info("📷 **Step 3: Identity Matching**. Look straight and capture.")
                img_data = st.camera_input("Capture Identity Frame", key="cam_match")
                if img_data:
                    from PIL import Image
                    from face_auth import get_face_landmarks, get_face_signature, verify_face
                    from database import log_login_event
                    import sqlite3
                    
                    pil_img = Image.open(img_data).convert("RGB")
                    landmarks = get_face_landmarks(pil_img)
                    if landmarks:
                        probe_sig = get_face_signature(landmarks)
                        
                        conn = sqlite3.connect("hospital.db")
                        c = conn.cursor()
                        c.execute("SELECT username, role, face_landmarks_signature FROM users WHERE face_landmarks_signature IS NOT NULL")
                        candidates = c.fetchall()
                        conn.close()
                        
                        matched_user = None
                        matched_role = None
                        
                        for username, role_db, sig_json in candidates:
                            is_match, dist_val = verify_face(probe_sig, sig_json)
                            if is_match:
                                matched_user = username
                                matched_role = role_db
                                break
                        
                        if matched_user:
                            st.success(f"✅ Identity Verified! Welcome {matched_user}")
                            log_login_event(matched_user, "Face Success")
                            st.session_state.user = matched_user
                            st.session_state.role = matched_role
                            st.session_state.liveness_stage = 1
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            log_login_event("unknown", "Face Match Failed")
                            st.error("Face not recognized. Please login using Username & Password.")
                            if st.button("Retry Liveness Checks"):
                                st.session_state.liveness_stage = 1
                                st.rerun()
                    else:
                        st.error("No face detected. Look directly at the camera.")

        elif login_mode == "Forgot Password":
            phone_input = st.text_input("Enter Registered Mobile Number")
            if st.button("Send OTP"):
                from database import check_mobile_number
                user_found = check_mobile_number(phone_input)
                if user_found:
                    st.session_state.forgot_username = user_found
                    st.session_state.forgot_otp_sent = True
                    st.session_state.forgot_otp_code = "123456"
                    st.success("🔒 Simulated OTP code '123456' sent to mobile contact.")
                else:
                    st.error("Mobile number not registered.")

            if st.session_state.get("forgot_otp_sent", False):
                otp_val = st.text_input("Enter 6-digit OTP code")
                new_pass = st.text_input("Enter New Password", type="password")
                if st.button("Reset Password"):
                    if otp_val == st.session_state.forgot_otp_code:
                        if new_pass:
                            from database import reset_user_password
                            if reset_user_password(st.session_state.forgot_username, new_pass):
                                st.success("✅ Password reset successfully! Please log in using Password Login.")
                                st.session_state.forgot_otp_sent = False
                                st.session_state.forgot_username = None
                            else:
                                st.error("Failed to reset password in database.")
                        else:
                            st.warning("Please enter a new password.")
                    else:
                        st.error("Incorrect OTP code. Try again.")

        elif login_mode == "Emergency Login":
            st.markdown("<p style='font-size:13px;color:#d90429;font-weight:bold;'>⚠️ FOR UNCONSCIOUS PATIENT EMERGENCY ACCESS ONLY</p>", unsafe_allow_html=True)
            pid_input = st.text_input("Enter Patient ID (e.g. PAT-1234)")
            phone_contact = st.text_input("Enter Registered Emergency Contact Mobile Number")
            
            if st.button("Verify Emergency Contact"):
                from database import verify_emergency_patient
                pat_row = verify_emergency_patient(pid_input, phone_contact)
                if pat_row:
                    st.session_state.emergency_pid = pid_input
                    st.session_state.emergency_username = pat_row[0]
                    st.session_state.emergency_name = pat_row[1]
                    st.session_state.emergency_otp_sent = True
                    st.session_state.emergency_otp_code = "999888"
                    st.success(f"🚨 Access Verification Code '999888' sent to Emergency Contact ({phone_contact}).")
                else:
                    st.error("Patient ID or Emergency Contact Number does not match.")
            
            if st.session_state.get("emergency_otp_sent", False):
                otp_code_in = st.text_input("Enter 6-digit Emergency OTP Code")
                if st.button("Log In Restricted Emergency Mode"):
                    if otp_code_in == st.session_state.emergency_otp_code:
                        from database import log_emergency_access
                        log_emergency_access(st.session_state.emergency_pid, "Emergency Room Access")
                        st.session_state.user = st.session_state.emergency_username
                        st.session_state.role = "emergency_access"
                        st.session_state.emergency_otp_sent = False
                        st.success(f"🔓 Logging in restricted emergency access mode for Patient: {st.session_state.emergency_name}")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Invalid OTP Code.")

        st.markdown('<div class="role-title">Contact Support</div>', unsafe_allow_html=True)
        if st.button("📞 Helpdesk Details"):
            st.info("Helpline: +1-800-555-0199\n\nSupport: support@aihospital.com")

        st.markdown('<div class="role-title">View details</div>', unsafe_allow_html=True)

        r1, r2 = st.columns(2)

        with r1:
            if st.button("🏥 Hospital", key="show_hospital_btn"):
                st.session_state.show_hospitals = not st.session_state.show_hospitals
                st.session_state.show_doctors = False
                st.session_state.selected_doctor = None

        with r2:
            if st.button("👨‍⚕️ Doctor", key="show_doctor_btn"):
                st.session_state.show_doctors = True
                st.session_state.show_hospitals = False
                st.session_state.selected_doctor = None

        if st.session_state.show_hospitals:
            st.markdown("""
<div class="details-box">
<h4>🏥 Hospital Details</h4>
<p><b>AI Hospital</b></p>
<p>24/7 Emergency Care</p>
<p>AI Symptom Analysis</p>
<p>Doctor Specialization Matching</p>
<p>Emergency Monitoring System</p>
<p>Patient Management Dashboard</p>
</div>
""", unsafe_allow_html=True)

        if st.session_state.show_doctors:
            doctors = [
                d for d in get_users()
                if len(d) > 3 and str(d[3]).lower() == "doctor"
            ]

            if st.session_state.selected_doctor is None:
                st.markdown("""
<div class="details-box">
<h4>👨‍⚕️ Doctor List</h4>
</div>
""", unsafe_allow_html=True)

                if not doctors:
                    st.info("No doctors available")
                else:
                    for d in doctors:
                        username = d[1] if len(d) > 1 else "N/A"
                        name = d[4] if len(d) > 4 and d[4] else username
                        phone = d[6] if len(d) > 6 and d[6] else "N/A"

                        extra = get_doctor_extra(username)

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

                        image_path = f"doctor_images/{username}.png"

                        with st.container():
                            col_img, col_info = st.columns([1, 3])

                            with col_img:
                                if os.path.exists(image_path):
                                    st.image(image_path, width=90)
                                else:
                                    st.image(
                                        "https://cdn-icons-png.flaticon.com/512/3774/3774299.png",
                                        width=90
                                    )

                            with col_info:
                                st.markdown(
                                    f"""
<div class="doctor-name">Dr. {clean_value(name)}</div>
<div class="doctor-spec">🩺 {clean_value(specialization)}</div>
<p><b>Qualification:</b> {clean_value(qualification)}</p>
<p><b>Experience:</b> {clean_value(experience)}</p>
""",
                                    unsafe_allow_html=True
                                )

                                if st.button(
                                    "View Full Details",
                                    key=f"view_doctor_{username}"
                                ):
                                    st.session_state.selected_doctor = username
                                    st.rerun()

                        st.markdown("---")

            else:
                username = st.session_state.selected_doctor

                doctor = None
                for d in doctors:
                    if len(d) > 1 and d[1] == username:
                        doctor = d
                        break

                if doctor:
                    name = doctor[4] if len(doctor) > 4 and doctor[4] else username
                    phone = doctor[6] if len(doctor) > 6 and doctor[6] else "Not Available"

                    extra = get_doctor_extra(username)

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

                    image_path = f"doctor_images/{username}.png"

                    st.markdown("<div class='details-box'>", unsafe_allow_html=True)

                    if os.path.exists(image_path):
                        st.image(image_path, width=160)
                    else:
                        st.image(
                            "https://cdn-icons-png.flaticon.com/512/3774/3774299.png",
                            width=160
                        )

                    st.markdown(
                        f"""
<div class="profile-title">Dr. {clean_value(name)}</div>
<div class="profile-info"><b>Specialization:</b> {clean_value(specialization)}</div>
<div class="profile-info"><b>Qualification:</b> {clean_value(qualification)}</div>
<div class="profile-info"><b>Experience:</b> {clean_value(experience)}</div>
<div class="profile-info"><b>Phone:</b> {clean_value(phone)}</div>
""",
                        unsafe_allow_html=True
                    )

                    if st.button("Back to Doctor List"):
                        st.session_state.selected_doctor = None
                        st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
<p style='text-align:center;color:#6c7f9f;margin-top:18px;font-size:13px;'>
© 2024 AI Hospital System
</p>
</div>
""", unsafe_allow_html=True)

    st.stop()

else:

    st.sidebar.title("AI Hospital")
    st.sidebar.success(f"👤 {st.session_state.user}")

    role = st.session_state.role

    if role == "admin":
        from ui import admin_ui
        admin_ui.show()

    elif role == "doctor":
        from ui import doctor_ui
        doctor_ui.show()

    elif role == "staff":
        from ui import staff_ui
        staff_ui.show()


    elif role == "patient":
        from ui import patient_ui
        patient_ui.show(st.session_state.user, emergency_mode=False)

    elif role == "emergency_access":
        from ui import patient_ui
        patient_ui.show(st.session_state.user, emergency_mode=True)