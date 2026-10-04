import streamlit as st
import streamlit.components.v1 as components
from ai import get_ai_response, detect_issue, full_ai_analysis
from database import (
    save_patient, get_history, get_doctors_by_specialization, save_request, share_patient_history,
    search_emergency_dataset, save_symptom_submission, save_emergency, save_referral_request, save_consultation, get_hospitals,
    auto_assign_doctor_for_hospital, check_medication_safety, get_doctor_details,
    save_medical_report, get_medical_report_by_referral
)
from utils import (
    format_output, detect_status, get_location,
    get_live_location, calculate_distance,
    map_symptom_to_specialization
)
from emergency import check_emergency, get_issue_type, get_emergency_level
from first_aid import get_first_aid
from hospitals import get_hospitals
from voice import get_voice
from alerts import send_alert
from PIL import Image
import pandas as pd
from datetime import datetime


def get_hospital_id(name):
    clean = "".join([c for c in name if c.isalnum()]).upper()
    words = name.split()
    last_word = words[-1] if words else ""
    last_clean = "".join([c for c in last_word if c.isalnum()]).upper()
    
    prefix = clean[:12]
    if last_clean and last_clean not in prefix:
        return f"HOSP_{prefix[:10]}_{last_clean}"
    else:
        import hashlib
        h = hashlib.md5(name.encode('utf-8')).hexdigest().upper()[:4]
        return f"HOSP_{prefix[:10]}_{h}"

def get_hospital_coordinates(row):
    lat_keys = ["latitude", "lat", "hospital_latitude"]
    lon_keys = ["longitude", "lon", "lng", "hospital_longitude"]
    
    lat_val = None
    lon_val = None
    
    if hasattr(row, "get"):
        for k in lat_keys:
            if row.get(k) is not None:
                lat_val = row.get(k)
                break
        for k in lon_keys:
            if row.get(k) is not None:
                lon_val = row.get(k)
                break
    else:
        for k in lat_keys:
            if k in row:
                lat_val = row[k]
                break
        for k in lon_keys:
            if k in row:
                lon_val = row[k]
                break
                
    if lat_val is None or lon_val is None:
        return None, None
        
    try:
        lat = float(lat_val)
        lon = float(lon_val)
        return lat, lon
    except:
        return None, None

def get_city_center_coordinates(city_name):
    default_lat, default_lon = 17.6868, 83.2185
    city_clean = city_name.strip().lower()
    try:
        import pandas as pd
        df = pd.read_csv("hospitals.csv")
        df["city_lower"] = df["city"].astype(str).str.strip().str.lower()
        city_hospitals = df[df["city_lower"] == city_clean]
        if not city_hospitals.empty:
            first_row = city_hospitals.iloc[0]
            lat, lon = get_hospital_coordinates(first_row)
            if lat is not None and lon is not None:
                return lat, lon
    except Exception as e:
        print("Error getting city center coordinates:", e)
    return default_lat, default_lon

def auto_generate_referral_report(user, patient_id, emergency_id, ref_id, h_id, doc_id, symptoms, result_text, risk_score):
    try:
        import os
        import random
        from utils import generate_pdf_report
        from database import get_medical_report_by_referral, save_medical_report
        
        os.makedirs("medical_reports", exist_ok=True)
        
        existing = get_medical_report_by_referral(ref_id)
        if existing and existing.get("status") == "REPORT_READY":
            return existing.get("report_id")
            
        report_id = f"REP-{random.randint(10000, 99999)}"
        file_path = f"medical_reports/report_{ref_id}_v1.pdf"
        save_medical_report(
            report_id=report_id,
            referral_id=ref_id,
            patient_id=patient_id,
            emergency_id=emergency_id,
            hospital_id=h_id,
            doctor_id=doc_id,
            report_file_path=file_path,
            status="REPORT_GENERATING"
        )
        
        pdf_bytes = generate_pdf_report(
            patient_username=user,
            symptoms=symptoms,
            result_data=result_text,
            risk_score=risk_score,
            report_type="Referral"
        )
        
        with open(file_path, "wb") as f_pdf:
            f_pdf.write(pdf_bytes)
            
        save_medical_report(
            report_id=report_id,
            referral_id=ref_id,
            patient_id=patient_id,
            emergency_id=emergency_id,
            hospital_id=h_id,
            doctor_id=doc_id,
            report_file_path=file_path,
            status="REPORT_READY"
        )
        return report_id
    except Exception as e:
        print("Error auto-generating PDF report:", e)
        try:
            save_medical_report(
                report_id=report_id,
                referral_id=ref_id,
                patient_id=patient_id,
                emergency_id=emergency_id,
                hospital_id=h_id,
                doctor_id=doc_id,
                report_file_path="",
                status="REPORT_FAILED"
            )
        except:
            pass
        return None

import time
import os


def execute_patient_history_share(user, hospital_name, doctor_username, symptoms, prediction_text, severity_level, lat=None, lon=None):
    import json
    from database import load_patient_clinical_data, share_patient_history, get_patient_risk_score
    from emergency import get_issue_type
    from first_aid import get_first_aid
    
    p_details = load_patient_clinical_data(user)
    if not p_details:
        return
        
    issue = get_issue_type(symptoms)
    first_aid = get_first_aid(issue, "en")
    risk_score = get_patient_risk_score(symptoms)
    
    shared_payload = {
        "patient_id": p_details.get("patient_id"),
        "patient_name": p_details.get("name"),
        "age": p_details.get("age"),
        "gender": p_details.get("gender"),
        "phone": p_details.get("phone"),
        "emergency_contact": p_details.get("emergency_contact"),
        "current_symptoms": symptoms,
        "predicted_disease": prediction_text,
        "confidence_score": "85%",
        "risk_score": risk_score,
        "emergency_severity": severity_level,
        "first_aid_recommendations": first_aid,
        "medication_recommendations": "Prescribed at consultation",
        "previous_diseases": p_details.get("previous_diseases"),
        "previous_medications": p_details.get("previous_medications"),
        "previous_reports": p_details.get("previous_reports"),
        "allergies": p_details.get("allergies"),
        "existing_diseases": p_details.get("chronic_diseases"),
        "location": f"Latitude: {lat}, Longitude: {lon}" if (lat and lon) else "Latitude: 17.3850, Longitude: 78.4867",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    shared_json = json.dumps(shared_payload)
    share_patient_history(
        patient_username=user,
        hospital_name=hospital_name,
        doctor_username=doctor_username,
        shared_data=shared_json
    )


@st.cache_data
def cached_dataset():
    try:
        return pd.read_csv("diseases.csv")
    except:
        return None


def normalize_symptoms(symptoms):
    text = str(symptoms).lower().strip()

    corrections = {
        "breeting": "breathing",
        "breeth": "breath",
        "breath problem": "breathing problem",
        "breathing problm": "breathing problem",
        "brething": "breathing",
        "brething problem": "breathing problem",
        "stomac": "stomach",
        "stamac": "stomach",
        "head pain": "headache",
        "head ach": "headache"
    }

    for wrong, right in corrections.items():
        text = text.replace(wrong, right)

    return text


def smart_severity(symptoms):
    symptoms = normalize_symptoms(symptoms)
    severity = "low"

    if "chest pain" in symptoms:
        severity = "medium"
        if (
            "breathing problem" in symptoms
            or "shortness of breath" in symptoms
            or "sweating" in symptoms
            or "left arm pain" in symptoms
            or "jaw pain" in symptoms
            or "unconscious" in symptoms
            or "low oxygen" in symptoms
            or "dizziness" in symptoms
        ):
            severity = "high"

    elif "fever" in symptoms:
        severity = "low"
        if "high fever" in symptoms or "continuous fever" in symptoms:
            severity = "medium"
        if "unconscious" in symptoms or "seizure" in symptoms:
            severity = "high"

    elif "headache" in symptoms or "head pain" in symptoms:
        severity = "low"
        if "dizziness" in symptoms or "blurred vision" in symptoms:
            severity = "medium"
        if "unconscious" in symptoms or "stroke" in symptoms or "seizure" in symptoms:
            severity = "high"

    elif "stomach pain" in symptoms or "abdominal pain" in symptoms:
        severity = "low"
        if "vomiting" in symptoms or "diarrhea" in symptoms or "nausea" in symptoms:
            severity = "medium"
        if "blood vomiting" in symptoms or "vomiting blood" in symptoms:
            severity = "high"

    elif (
        "breathing problem" in symptoms
        or "shortness of breath" in symptoms
        or "low oxygen" in symptoms
        or "cannot breathe" in symptoms
    ):
        severity = "high"

    elif (
        "heavy bleeding" in symptoms
        or "severe bleeding" in symptoms
        or "accident" in symptoms
        or "snake bite" in symptoms
        or "stroke" in symptoms
        or "heart attack" in symptoms
        or "unconscious" in symptoms
        or "seizure" in symptoms
    ):
        severity = "high"

    elif "fracture" in symptoms or "burn" in symptoms or "dog bite" in symptoms:
        severity = "medium"

    elif "vomiting" in symptoms:
        severity = "low"
        if "weakness" in symptoms or "dehydration" in symptoms:
            severity = "medium"
        if "blood" in symptoms:
            severity = "high"

    elif "dizziness" in symptoms or "weakness" in symptoms:
        severity = "medium"

    return severity


def force_medical_result(symptoms):
    text = normalize_symptoms(symptoms)

    if (
        "chest pain" in text
        and (
            "breathing problem" in text
            or "shortness of breath" in text
            or "sweating" in text
            or "left arm pain" in text
            or "jaw pain" in text
            or "low oxygen" in text
            or "dizziness" in text
            or "unconscious" in text
        )
    ):
        return """
Condition: Possible Cardiac Emergency

Severity: HIGH

Specialization: Cardiologist

Medicine: Immediate Emergency Care Required

Advice: Visit nearest hospital immediately.
"""

    if (
        "chest pain" in text
        and (
            "right side" in text
            or "right chest" in text
            or "right side pain" in text
            or "with right side" in text
        )
    ):
        return """
Condition: Right Side Chest Pain - Needs Evaluation

Severity: MEDIUM

Specialization: General Physician

Medicine: Pain Relief / Consult Doctor

Advice: Right side chest pain may be caused by muscle strain, rib pain, acidity, or lung-related problems. Consult doctor if pain continues or breathing problem starts.
"""

    if (
        "chest pain" in text
        and (
            "left side" in text
            or "left chest" in text
            or "left side pain" in text
            or "with left side" in text
        )
    ):
        return """
Condition: Left Side Chest Pain - Needs Evaluation

Severity: MEDIUM

Specialization: Cardiologist

Medicine: Consult Doctor

Advice: Left side chest pain may need cardiac evaluation. Consult doctor for proper diagnosis.
"""

    if "chest pain" in text:
        return """
Condition: Chest Pain - Needs Further Evaluation

Severity: MEDIUM

Specialization: Cardiologist

Medicine: Consult Doctor

Advice: Chest pain can occur due to acidity, anxiety, muscle strain, lung issues, or heart-related causes. Proper medical evaluation is recommended.
"""

    if "nausea" in text and "stomach pain" in text:
        return """
Condition: Gastritis / Food Poisoning

Severity: MEDIUM

Specialization: Gastroenterologist

Medicine: Antacid / ORS

Advice: Drink water, avoid oily food and take rest. Consult doctor if vomiting or pain continues.
"""

    if "stomach pain" in text or "abdominal pain" in text:
        return """
Condition: Gastritis

Severity: LOW

Specialization: Gastroenterologist

Medicine: Antacid

Advice: Avoid spicy and oily food. Eat light food and drink water.
"""

    if "headache" in text:
        return """
Condition: Headache

Severity: LOW

Specialization: Neurologist

Medicine: Paracetamol

Advice: Take rest, drink water, avoid stress and sleep properly.
"""

    if "fever" in text:
        if "high fever" in text or "continuous fever" in text:
            return """
Condition: High Fever

Severity: MEDIUM

Specialization: General Physician

Medicine: Paracetamol

Advice: Drink fluids, monitor temperature and consult doctor if fever continues.
"""
        return """
Condition: Viral Fever

Severity: LOW

Specialization: General Physician

Medicine: Paracetamol

Advice: Take rest and drink enough fluids.
"""

    if "vomiting" in text:
        return """
Condition: Vomiting / Gastric Issue

Severity: MEDIUM

Specialization: Gastroenterologist

Medicine: ORS / Antacid

Advice: Drink fluids and avoid outside food.
"""

    return None


def dataset_match(symptoms):
    try:
        df = cached_dataset()
        if df is None:
            return None

        symptoms = normalize_symptoms(symptoms)
        input_words = [w.strip() for w in symptoms.split() if len(w.strip()) > 2]

        if not input_words:
            return None

        best_score = 0
        best_row = None

        for _, row in df.iterrows():
            db_symptoms = str(row["symptoms"]).lower().strip()
            db_words = db_symptoms.split()
            score = 0
            matched_words = 0

            for word in input_words:
                if word in db_words:
                    score += 5
                    matched_words += 1
                elif word in db_symptoms:
                    score += 2

            score += matched_words * 3

            if symptoms == db_symptoms:
                score += 30
            elif symptoms in db_symptoms:
                score += 15

            if score > best_score:
                best_score = score
                best_row = row

        if best_row is None or best_score < 8:
            return None

        disease = str(best_row.get("disease", "Unknown"))
        medicine = str(best_row.get("Medicines", "Consult doctor"))
        advice = str(best_row.get("Advice", "Take rest"))
        severity = smart_severity(symptoms)
        specialization = map_symptom_to_specialization(symptoms)

        return f"""
Condition: {disease}

Severity: {severity}

Specialization: {specialization}

Medicine: {medicine}

Advice: {advice}
"""

    except Exception as e:
        print("Dataset Match Error:", e)
        return None


def get_priority(symptoms):
    severity = smart_severity(symptoms)
    if severity == "high":
        return "CRITICAL"
    if severity == "medium":
        return "MEDIUM"
    return "LOW"


def auto_assign_doctor(symptoms):
    specialization = map_symptom_to_specialization(symptoms)
    spec_lower = specialization.lower()
    if "cardio" in spec_lower or "heart" in spec_lower:
        return "random3"
    elif "psych" in spec_lower or "neuro" in spec_lower or "brain" in spec_lower:
        return "random2"
    else:
        return "random1"


def send_alert_once(user, symptoms):
    if "alert_sent" not in st.session_state:
        st.session_state.alert_sent = False
    if not st.session_state.alert_sent:
        send_alert("doctor", f"Emergency: {user} - {symptoms}")
        send_alert("staff", f"Emergency: {user} - {symptoms}")
        send_alert("admin", f"Emergency: {user} - {symptoms}")
        st.session_state.alert_sent = True


def history_match(history, symptoms):
    for h in history:
        if str(symptoms).lower() in str(h[2]).lower():
            return h[3]
    return None


def prevent_duplicate(symptoms):
    if "last_input" not in st.session_state:
        st.session_state.last_input = ""
    st.session_state.last_input = str(symptoms).strip().lower()
    return False


def confidence_score(text):
    text = str(text)
    if len(text) > 200:
        return "High"
    elif len(text) > 100:
        return "Medium"
    return "Low"


def calculate_eta(distance):
    if distance == "N/A":
        return "Unknown"
    return f"{round((distance / 45) * 60, 1)} mins"


def show_ultra_summary(symptoms, result, user="Patient"):
    st.subheader("Smart Summary & Diagnosis Report")
    
    from database import get_patient_risk_score
    risk_score = get_patient_risk_score(symptoms)
    
    st.info(f"""
📋 Symptoms: {symptoms}

📌 Priority: {get_priority(symptoms)}

🩺 Specialization: {map_symptom_to_specialization(symptoms)}

👨‍⚕️ Assigned Doctor: {auto_assign_doctor(symptoms)}
""")

    st.metric("🚨 Calculated Patient Risk Score", f"{risk_score}%")
    if risk_score >= 50:
        st.error("⚠️ Critical Risk! Immediate medical checkup or hospital transfer advised.")
    elif risk_score >= 30:
        st.warning("⚠️ High Risk. Please schedule a consultation soon.")
    else:
        st.success("🟢 Low/Medium Risk. Follow general precautions.")

    # PDF Download
    from utils import generate_pdf_report
    pdf_bytes = generate_pdf_report(user, symptoms, result, risk_score)
    st.download_button(
        label="📥 Generate Referral PDF",
        data=pdf_bytes,
        file_name=f"Medical_Report_{user}.pdf",
        mime="application/pdf",
        key=f"pdf_download_{hash(result)}"
    )


def smooth_tracking():
    box = st.empty()
    progress = st.progress(0)
    steps = [
        "Ambulance request created",
        "Ambulance tracking enabled",
        "Waiting for hospital/staff confirmation"
    ]
    for idx, step in enumerate(steps):
        box.info(step)
        progress.progress((idx + 1) / len(steps))
        time.sleep(0.6)


def get_assigned_doctor_name(symptoms):
    specialization = map_symptom_to_specialization(symptoms)
    spec_lower = specialization.lower()
    if "cardio" in spec_lower or "heart" in spec_lower:
        assigned_doctor = "prasadd2"
    elif "psych" in spec_lower or "neuro" in spec_lower or "brain" in spec_lower:
        assigned_doctor = "prasadd1"
    else:
        assigned_doctor = "prasad1"
    return specialization, assigned_doctor


def show_request_process(user, symptoms, hospital_name, assigned_doctor, city, lat, lon):
    st.subheader("📡 Patient Emergency Status")
    if "patient_updates" not in st.session_state:
        st.session_state.patient_updates = []
    if not st.session_state.patient_updates:
        try:
            save_request(
                patient_name=user,
                hospital=hospital_name,
                symptoms=symptoms,
                result=f"EMERGENCY CASE | Doctor: {assigned_doctor} | Location: {city}",
                lat=lat,
                lon=lon
            )
            st.session_state.patient_updates = [
                "Hospital request sent successfully",
                f"Assigned doctor: {assigned_doctor}",
                f"Selected hospital: {hospital_name}",
                f"Location shared: {city}",
                "Hospital can contact patient",
                "Ambulance request created"
            ]
        except Exception as e:
            st.error(f"Request failed: {e}")
            return
    for update in st.session_state.patient_updates:
        st.success(update)
    st.info("""
⏳ Waiting for hospital/staff response...

Real updates will come from:
• Doctor Panel
• Staff Panel
• Hospital System
""")

    # Generate Referral PDF button
    from utils import generate_pdf_report
    from database import get_patient_risk_score
    risk_score = get_patient_risk_score(symptoms)
    
    current_result = {
        "condition": "Emergency Case",
        "risk_score": f"{risk_score}%",
        "first_aid": "Please consult the assigned doctor immediately.",
        "hospitals": hospital_name,
        "doctors": assigned_doctor
    }
    
    pdf_bytes = generate_pdf_report(user, symptoms, current_result, risk_score)
    st.download_button(
        label="📥 Generate Referral PDF",
        data=pdf_bytes,
        file_name=f"Emergency_Referral_{user}.pdf",
        mime="application/pdf",
        key=f"emergency_referral_pdf_{user}"
    )


def normalize_city_name(city):
    city = str(city).lower().strip()
    city_alias = {
        "vizag": "visakhapatnam",
        "vskp": "visakhapatnam",
        "visaka": "visakhapatnam",
        "vizag city": "visakhapatnam",
        "hyd": "hyderabad",
        "blr": "bengaluru",
        "bangalore": "bengaluru",
        "new delhi": "delhi"
    }
    return city_alias.get(city, city)


def show(user, emergency_mode=False):
    if "active_emergency" not in st.session_state:
        st.session_state.active_emergency = ""
    if "symptoms" not in st.session_state:
        st.session_state.symptoms = ""
    if "specialization" not in st.session_state:
        st.session_state.specialization = ""

    st.markdown("""
<style>
section[data-testid="stSidebar"]{
    min-width:260px !important;
    max-width:260px !important;
}
.main .block-container{
    max-width:100% !important;
    padding-top:1rem !important;
    padding-left:2rem !important;
    padding-right:2rem !important;
}
button[data-baseweb="tab"]{
    font-size:20px !important;
    padding:10px 18px !important;
    border-radius:10px !important;
}
@media (max-width:768px){
    section[data-testid="stSidebar"]{
        min-width:220px !important;
        max-width:220px !important;
    }
    button[data-baseweb="tab"]{
        font-size:16px !important;
        padding:8px 12px !important;
    }
}
</style>
""", unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center'>AI Patient Dashboard</h2>", unsafe_allow_html=True)
    
    if emergency_mode:
        st.error("🚨 EMERGENCY ACCESS ACTIVE (Restricted View). Patient data is read-only. Edits, appointments, and password changes are disabled.")

    defaults = {
        "symptoms": "",
        "chat": [],
        "hospital_updates": [],
        "patient_updates": [],
        "my_medicines": [],
        "location_confirmed_v4": False,
        "saved_city_v4": "",
        "saved_lat_v4": None,
        "saved_lon_v4": None,
        "request_sent": False,
        "selected_hospital": "",
        "analyzed": False,
        "emerg_detected": "NO",
        "emerg_level": "LOW",
        "assigned_doctor": "—",
        "specialization": "—",
        "location_confirmed": "—",
        "first_aid_protocol": "—",
        "first_aid_key": "heart_attack"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load user profile fields
    import sqlite3
    import random
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("SELECT patient_id, name, age, gender, phone, blood_group, allergies, chronic_diseases, latitude, longitude, address FROM users WHERE username=?", (user,))
    p_profile = c.fetchone()
    conn.close()
    
    patient_id = p_profile[0] if p_profile else f"P-{random.randint(1000, 9999)}"

    st.subheader(f"👤 Patient Profile: {user}")
    
    # Render Emergency Medical QR Card
    from utils import generate_emergency_qr_card
    qr_bytes = generate_emergency_qr_card(user)
    if qr_bytes:
        with st.expander("📸 View Emergency Medical QR Card", expanded=False):
            st.image(qr_bytes, width=200, caption="Scan this QR code during emergencies to retrieve this Clinical Profile.")

    tabs = st.tabs(["AI Analysis", "My History", "My Medicines", "Hospital Updates"])

    with tabs[0]:
        st.subheader("🩺 Enter Symptoms")
        symptom_text = st.text_area("Type Symptoms", value=st.session_state.get("symptom_input_text", ""), placeholder="e.g. Chest pain, difficulty breathing, sweating")
        st.session_state.symptom_input_text = symptom_text
        
        col_mic1, col_mic2 = st.columns([4, 1])
        with col_mic2:
            if st.button("🎤 Speak Symptoms"):
                voice_text = get_voice()
                if voice_text:
                    st.session_state.symptom_input_text = voice_text
                    st.rerun()
                    
        st.subheader("🖼️ Upload Injury Image")
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "png"])
        if uploaded_image:
            from PIL import Image
            img = Image.open(uploaded_image)
            st.image(img, caption="Uploaded Image", use_column_width=True)
            
        analyze_btn = st.button("Analyze")
        
        if analyze_btn:
            if symptom_text.strip():

                
                matched_case = search_emergency_dataset(symptom_text)
                
                from ai import full_ai_analysis
                ai_assess = full_ai_analysis(symptom_text)
                
                is_emerg = False
                severity = "LOW"
                required_spec = "General Medicine"
                first_aid_key = "heart_attack"
                ambulance_required = 0
                
                if matched_case:
                    is_emerg = True
                    severity = matched_case["severity_level"]
                    required_spec = matched_case["required_specialization"]
                    first_aid_key = matched_case["emergency_protocol_id"]
                    ambulance_required = matched_case["ambulance_required"]
                else:
                    severity = ai_assess.get("severity", "LOW").upper()
                    if severity in ["HIGH", "CRITICAL"]:
                        is_emerg = True
                    required_spec = map_symptom_to_specialization(symptom_text)
                    first_aid_key = "heart_attack"
                    ambulance_required = 1 if is_emerg else 0
                    
                em_id = f"EMERG-{random.randint(1000, 9999)}"
                ai_id = f"AI-{random.randint(1000, 9999)}"
                
                if is_emerg:
                    # Save initial triage state to session, referral happens AFTER selection
                    st.session_state.active_emergency = em_id
                    st.session_state.symptoms = symptom_text
                    st.session_state.emerg_detected = "YES"
                    st.session_state.emerg_level = severity
                    st.session_state.specialization = required_spec
                    st.session_state.first_aid_key = first_aid_key
                    st.session_state.ambulance_required_flag = ambulance_required
                    st.session_state.selected_hospital = ""
                    st.session_state.assigned_doctor = "—"
                    st.session_state.analyzed = True
                    
                    # Store immediate triage status update
                    st.session_state.hospital_updates = [
                        f"Symptoms triage completed: {symptom_text}",
                        f"Clinical emergency level determined: {severity}"
                    ]
                else:
                    doc_id = auto_assign_doctor(symptom_text)
                    save_consultation(
                        consultation_id=em_id,
                        patient_id=patient_id,
                        patient_name=user,
                        symptoms=symptom_text,
                        observations="OP Triage: BP/Pulse TBD",
                        diagnosis=ai_assess.get("condition", "Pending Outpatient Review"),
                        treatment_plan="Pending Doctor Outpatient Review",
                        follow_up="TBD",
                        doctor_id=doc_id,
                        hospital_id="Prasad Hospital"
                    )
                    st.session_state.emerg_detected = "NO"
                    st.session_state.emerg_level = "LOW"
                    st.session_state.assigned_doctor = doc_id
                    st.session_state.specialization = required_spec
                    st.session_state.selected_hospital = "Prasad Hospital"
                    st.session_state.analyzed = True
                    
                save_symptom_submission(
                    patient_id=patient_id,
                    symptoms=symptom_text,
                    emerg_result="Emergency Flow" if is_emerg else "Normal OP Flow",
                    em_id=em_id,
                    ai_id=ai_id,
                    dataset_ver="v1.0-Validated",
                    risk=severity,
                    protocol_id=first_aid_key,
                    amb_id="None",
                    ref_id="None",
                    doc_id="None"
                )
                st.session_state.symptom_input_text = ""
                st.rerun()
            else:
                st.warning("Please enter symptoms before submitting.")
                
        if st.session_state.get("analyzed", False):
            st.write("---")
            st.markdown("### 📊 AI-Assisted Triage & Referral Assessment Results")
            st.info("💡 AI-assisted emergency assessment. Do not present it as a confirmed medical diagnosis.")
            
            st.write(f"**Emergency Detected:** {st.session_state.get('emerg_detected', 'NO')}")
            st.write(f"**Level:** {st.session_state.get('emerg_level', 'LOW')}")
            st.write(f"**Department/Specialization:** {st.session_state.get('specialization', '—')}")
            
            first_aid_content = ""
            emerg_val = st.session_state.get('emerg_detected', 'NO')
            if emerg_val == "NO":
                st.write("---")
                st.success("✅ **No acute emergency detected.** We recommend scheduling a routine outpatient consultation.")
                st.info(f"👨‍⚕️ **Assigned Doctor:** {st.session_state.get('assigned_doctor', 'General Physician')}")
                st.info("💊 You can review your suggested medications and run safety checklists in the **My Medicines** tab above.")
            else:
                st.write("---")
                st.write("### First Aid / ప్రథమ చికిత్స / प्राथमिक उपचार")
                lang_opt = st.radio("Language / భాష / भाषा", ["English", "Telugu", "Hindi"], horizontal=True, key="first_aid_lang")
                
                from database import get_medical_knowledge
                p_protocol = get_medical_knowledge("protocol", st.session_state.get("first_aid_key", "heart_attack"))
                
                symptoms_search = st.session_state.get("symptoms", "").strip()
                matched_case = search_emergency_dataset(symptoms_search) if symptoms_search else None
                
                immediate_care_text = "Keep the patient resting and calm. Call ambulance."
                avoid_text = "Do not exert the patient. Do not leave them alone."
                seek_care_text = "Seek immediate care if the patient has breathing issues, severe chest pressure, or loss of consciousness."
                escalation_text = "If unresponsive, perform CPR immediately and contact the emergency services."
                
                if matched_case:
                    import json
                    try:
                        fa_dict = json.loads(matched_case["first_aid_protocol"])
                        lang_key = "en" if lang_opt == "English" else ("te" if lang_opt == "Telugu" else "hi")
                        immediate_care_text = fa_dict.get(lang_key, fa_dict.get("en"))
                    except:
                        pass
                    avoid_text = matched_case.get("red_flag_symptoms", avoid_text)
                    
                elif p_protocol:
                    immediate_care_text = p_protocol.get("immediate_response", immediate_care_text)
                    avoid_text = p_protocol.get("warnings", avoid_text)
                    escalation_text = p_protocol.get("ambulance_action", escalation_text)
                    
                st.markdown(f"""
                <div style='background:#fcf8e3; padding:15px; border-radius:8px; border-left:5px solid #f0ad4e; margin-bottom:10px;'>
                    <strong>🚨 Immediate Care / What to Do:</strong><br>{immediate_care_text}<br><br>
                    <strong>🚫 Avoid / What NOT to Do:</strong><br>{avoid_text}<br><br>
                    <strong>⚠️ Warning Signs / Seek Immediate Hospital Care if:</strong><br>{seek_care_text}<br><br>
                    <strong>📞 Emergency Escalation:</strong><br>{escalation_text}
                </div>
                """, unsafe_allow_html=True)
                    
                # Perform location lookup ONLY after emergency detection
                st.write("---")
                st.write("### 📍 Location Triage & Coordination")
                
                saved_lat = st.session_state.get("saved_lat_v4")
                saved_lon = st.session_state.get("saved_lon_v4")
                saved_city = st.session_state.get("saved_city_v4", "")
                
                manual_city = st.text_input("City Name", value=saved_city or "Visakhapatnam", placeholder="Enter city name", key="manual_city_input")
                
                use_loc_click = st.button("Use This Location")
                    
                if use_loc_click:
                    if not manual_city.strip():
                        st.error("Please enter a valid latitude and longitude.")
                    else:
                        # Lookup coordinates internally
                        lat, lon = get_city_center_coordinates(manual_city)
                        
                        st.session_state.saved_lat_v4 = lat
                        st.session_state.saved_lon_v4 = lon
                        st.session_state.saved_city_v4 = manual_city
                        st.session_state.location_confirmed_v4 = True
                        
                        conn_loc = sqlite3.connect("hospital.db")
                        c_loc = conn_loc.cursor()
                        c_loc.execute("""
                            CREATE TABLE IF NOT EXISTS user_locations (
                                patient_id TEXT PRIMARY KEY,
                                city TEXT,
                                latitude REAL,
                                longitude REAL,
                                timestamp TEXT
                            )
                        """)
                        now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c_loc.execute("""
                            INSERT OR REPLACE INTO user_locations (patient_id, city, latitude, longitude, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        """, (patient_id, manual_city, lat, lon, now_timestamp))
                        conn_loc.commit()
                        conn_loc.close()
                        
                        st.success("Triage location coordinates override saved!")
                        st.rerun()
                
                if st.session_state.get("location_confirmed_v4", False):
                    saved_city = st.session_state.saved_city_v4
                    st.write(f"**Location Confirmed:** {saved_city}")
                        
                # Hospital selection choice
                if st.session_state.get("location_confirmed_v4", False):
                    st.write("---")
                    st.write(f"**Recommended Hospitals Near:** {saved_city}")

                    # ── Interactive Leaflet Map ──
                    st.write("### 🗺️ Hospital Triage Map")
                    from database import get_nearest_hospitals_sorted, smart_assign_doctor, auto_share_patient_history

                    h_list = get_nearest_hospitals_sorted(
                        user_lat=saved_lat,
                        user_lon=saved_lon,
                        specialization=st.session_state.get("specialization", ""),
                        limit=10
                    )

                    markers_js = []
                    for h in h_list:
                        h_lat_m = h["lat"]
                        h_lon_m = h["lon"]
                        h_name_m = h["name"]
                        h_dist_m = h["distance"]
                        h_spec_m = h["specialization"]
                        h_phone_m = h["phone"]
                        h_addr_m = h["address"]
                        is_nearest = (h == h_list[0]) if h_list else False
                        marker_color = "red" if is_nearest else "blue"
                        import json as _json
                        popup_html = (
                            f"<b>{'📍 NEAREST — ' if is_nearest else ''}🏥 {h_name_m}</b><br>"
                            f"Address: {h_addr_m}<br>Phone: {h_phone_m}<br>"
                            f"Specialization: {h_spec_m}<br>Distance: {h_dist_m} km"
                        )
                        markers_js.append(f"""
                        L.marker([{h_lat_m}, {h_lon_m}], {{
                            icon: L.icon({{
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{marker_color}.png',
                                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
                            }})
                        }}).addTo(map).bindPopup({_json.dumps(popup_html)});
                        """)

                    markers_js_code = "\n".join(markers_js)
                    leaflet_html = f"""<!DOCTYPE html><html><head>
                    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
                    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
                    <style>#map{{height:350px;width:100%;border-radius:8px;border:1px solid #ddd;}} body{{margin:0;padding:0;}}</style>
                    </head><body><div id="map"></div><script>
                    var map = L.map('map').setView([{saved_lat},{saved_lon}],12);
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'© OpenStreetMap contributors'}}).addTo(map);
                    L.marker([{saved_lat},{saved_lon}],{{icon:L.icon({{
                        iconUrl:'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                        shadowUrl:'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize:[25,41],iconAnchor:[12,41],popupAnchor:[1,-34],shadowSize:[41,41]
                    }})}}).addTo(map).bindPopup('<b>📍 Your Location</b>').openPopup();
                    {markers_js_code}
                    </script></body></html>"""
                    components.html(leaflet_html, height=360)

                if not st.session_state.get("location_confirmed_v4", False):
                    st.info("Please enter your location (City) above and click 'Use This Location' to discover nearby hospitals.")

                else:
                    from database import get_nearest_hospitals_sorted, smart_assign_doctor, auto_share_patient_history

                    h_list = get_nearest_hospitals_sorted(
                        user_lat=saved_lat,
                        user_lon=saved_lon,
                        specialization=st.session_state.get("specialization", ""),
                        limit=10
                    )

                    if not h_list:
                        st.warning("No hospitals found near your location. Please try a different city.")
                    else:
                        st.markdown(f"""
                        <div style='background:linear-gradient(90deg,#e3f9e5,#c3f0ca);
                             border-left:5px solid #27ae60;border-radius:10px;
                             padding:12px 18px;margin-bottom:14px;'>
                          <h4 style='margin:0;color:#1a7a34;'>
                            📍 Nearest Hospital: {h_list[0]['name']}
                            &nbsp;<span style='font-size:13px;background:#27ae60;color:white;
                            border-radius:20px;padding:2px 10px;'>
                            {h_list[0]['distance']} km away</span>
                          </h4>
                          <div style='color:#2d6a4f;margin-top:4px;font-size:14px;'>
                            🏥 {h_list[0]['address']} &nbsp;|&nbsp; 📞 {h_list[0]['phone']}
                            &nbsp;|&nbsp; 🩺 {h_list[0]['specialization'][:60]}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # ── Check if a hospital is already selected for this emergency ──
                        conn_any = sqlite3.connect("hospital.db")
                        c_any = conn_any.cursor()
                        c_any.execute(
                            "SELECT 1 FROM hospital_requests WHERE patient_id=? AND emergency_id=? LIMIT 1",
                            (patient_id, st.session_state.get("active_emergency"))
                        )
                        any_selected = c_any.fetchone() is not None
                        conn_any.close()

                        st.write(f"### 🏥 Nearest Hospitals ({len(h_list)} found)")

                        for idx, h in enumerate(h_list):
                            h_name    = h["name"]
                            h_addr    = h["address"]
                            h_phone   = h["phone"]
                            h_spec    = h["specialization"]
                            h_dist    = h["distance"]
                            h_emerg   = h.get("emergency_support", h.get("emergency_available", "No"))
                            h_beds    = h.get("available_beds", "?")
                            h_icu     = h.get("available_icu", "?")
                            h_id      = h.get("hospital_id") or get_hospital_id(h_name)
                            is_nearest = (idx == 0)
                            spec_match = h.get("spec_match", False)

                            # Check if this hospital already has a referral
                            conn_ref = sqlite3.connect("hospital.db")
                            c_ref = conn_ref.cursor()
                            c_ref.execute("""
                                SELECT referral_id, referral_status, assigned_doctor, transfer_status
                                FROM hospital_requests
                                WHERE patient_id=? AND emergency_id=? AND to_hospital_id=?
                                ORDER BY id DESC LIMIT 1
                            """, (patient_id, st.session_state.get("active_emergency"), h_id))
                            ref_row = c_ref.fetchone()
                            conn_ref.close()
                            is_selected_hosp = (ref_row is not None)

                            badge = ""
                            if is_nearest:
                                badge = "🏆 Nearest"
                            if spec_match:
                                badge += (" · " if badge else "") + "✅ Specialization Match"

                            label = f"🏥 {h_name}"
                            if badge:
                                label += f" — {badge}"
                            if is_selected_hosp:
                                label += " ⭐ (Selected)"

                            border_color = "#27ae60" if is_nearest else ("#2563eb" if spec_match else "#cbd5e1")
                            bg_color = "#f0fff4" if is_nearest else ("#eff6ff" if spec_match else "#f9fafb")

                            with st.expander(label, expanded=(is_selected_hosp or is_nearest)):
                                st.markdown(f"""
                                <div style='background:{bg_color};border-left:4px solid {border_color};
                                     border-radius:8px;padding:12px;margin-bottom:8px;'>
                                  <div style='display:flex;flex-wrap:wrap;gap:10px;align-items:center;'>
                                    <div style='flex:1;min-width:200px;'>
                                      <b>📍 Address:</b> {h_addr}<br>
                                      <b>📞 Phone:</b> {h_phone}<br>
                                      <b>🩺 Specialization:</b> {h_spec[:80]}<br>
                                    </div>
                                    <div style='flex:1;min-width:180px;'>
                                      <b>📏 Distance:</b> {h_dist} km<br>
                                      <b>🛏️ Available Beds:</b> {h_beds}<br>
                                      <b>🏥 ICU Beds:</b> {h_icu}<br>
                                      <b>🚨 Emergency Support:</b> {h_emerg}
                                    </div>
                                  </div>
                                </div>
                                """, unsafe_allow_html=True)

                                if is_selected_hosp and ref_row:
                                    # ── Already selected — show doctor card + referral info ──
                                    ref_id_val      = ref_row[0]
                                    ref_status_val  = ref_row[1]
                                    doc_username_val = ref_row[2]
                                    transfer_status_val = ref_row[3]

                                    doc_info = get_doctor_details(doc_username_val)
                                    doc_name_val = doc_info["name"] if doc_info else doc_username_val
                                    doc_spec_val = doc_info["specialization"] if doc_info else "Emergency Medicine"

                                    # Doctor Card
                                    doc_img_path = f"doctor_images/{doc_username_val}.png"
                                    col_doc_img, col_doc_info = st.columns([1, 4])
                                    with col_doc_img:
                                        if os.path.exists(doc_img_path):
                                            st.image(doc_img_path, width=90)
                                        else:
                                            st.markdown("👨‍⚕️", unsafe_allow_html=False)
                                    with col_doc_info:
                                        st.markdown(f"""
                                        <div style='background:#eef2ff;border-left:4px solid #4f46e5;
                                             border-radius:8px;padding:10px;'>
                                          <b style='font-size:16px;color:#1e1b4b;'>👨‍⚕️ {doc_name_val}</b><br>
                                          <span style='color:#4f46e5;font-weight:700;'>🩺 {doc_spec_val}</span><br>
                                          <b>Referral ID:</b> {ref_id_val} &nbsp;|&nbsp;
                                          <b>Status:</b> {ref_status_val} &nbsp;|&nbsp;
                                          <b>Profile Transfer:</b> {transfer_status_val}
                                        </div>
                                        """, unsafe_allow_html=True)

                                    report_record = get_medical_report_by_referral(ref_id_val)
                                    if not report_record and ref_status_val.upper() in ["SENT", "ACCEPTED"]:
                                        auto_generate_referral_report(
                                            user=user, patient_id=patient_id,
                                            emergency_id=st.session_state.get("active_emergency"),
                                            ref_id=ref_id_val, h_id=h_id, doc_id=doc_username_val,
                                            symptoms=st.session_state.get("symptoms", ""),
                                            result_text=f"EMERGENCY REFERRAL | Doctor: {doc_name_val}",
                                            risk_score=85
                                        )
                                        report_record = get_medical_report_by_referral(ref_id_val)

                                    report_status_val = report_record.get("status") if report_record else "REPORT_PENDING"

                                    # ── Always generate the dedicated referral PDF ──
                                    try:
                                        from utils import generate_referral_pdf
                                        _doc_info_v = get_doctor_details(doc_username_val) or {}
                                        _first_aid_v = st.session_state.get("first_aid_content", "Keep the patient calm and comfortable.")
                                        ref_pdf_v = generate_referral_pdf(
                                            patient_username=user,
                                            symptoms=st.session_state.get("symptoms", ""),
                                            specialization=st.session_state.get("specialization", "Emergency Medicine"),
                                            severity=str(st.session_state.get("emerg_level", "High")),
                                            from_hospital="Prasad Hospital",
                                            to_hospital=h_name,
                                            doctor_name=_doc_info_v.get("name", doc_username_val),
                                            doctor_specialization=_doc_info_v.get("specialization", "Emergency Medicine"),
                                            doctor_qualification=_doc_info_v.get("qualification", "MBBS"),
                                            doctor_experience=_doc_info_v.get("experience", "N/A"),
                                            referral_id=ref_id_val,
                                            emergency_id=str(st.session_state.get("active_emergency", "N/A")),
                                            risk_score=85,
                                            first_aid_text=_first_aid_v,
                                        )
                                    except Exception as _pdf_err:
                                        print("Referral PDF view error:", _pdf_err)
                                        ref_pdf_v = None

                                    st.markdown("""
                                    <div style='background:linear-gradient(90deg,#e3f9e5,#c3f0ca);
                                         border-left:5px solid #27ae60;border-radius:10px;
                                         padding:10px 14px;margin:8px 0;'>
                                      <b style='color:#1a7a34;font-size:15px;'>📄 Official Referral Letter</b><br>
                                      <span style='color:#2d6a4f;font-size:13px;'>Download your complete referral letter with full medical history, referring hospital, receiving hospital, and assigned doctor details.</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    _col_ref1, _col_ref2 = st.columns(2)
                                    with _col_ref1:
                                        if ref_pdf_v:
                                            st.download_button(
                                                label="📥 Download Referral Letter PDF",
                                                data=ref_pdf_v,
                                                file_name=f"Referral_{ref_id_val}_{user}.pdf",
                                                mime="application/pdf",
                                                key=f"dl_refpdf_{idx}"
                                            )
                                        else:
                                            st.warning("Referral PDF not available.")
                                    with _col_ref2:
                                        if report_status_val == "REPORT_READY":
                                            pdf_bytes = None
                                            f_path = report_record.get("report_file_path", "") if report_record else ""
                                            if f_path and os.path.exists(f_path):
                                                with open(f_path, "rb") as f_r:
                                                    pdf_bytes = f_r.read()
                                            if pdf_bytes is None:
                                                from utils import generate_pdf_report
                                                pdf_bytes = generate_pdf_report(user, st.session_state.get("symptoms"), f"Referral | Doctor: {doc_name_val}", 85, report_type="Referral")
                                            st.download_button(
                                                label="📥 Download Full Medical Report PDF",
                                                data=pdf_bytes,
                                                file_name=f"MedicalReport_{user}.pdf",
                                                mime="application/pdf",
                                                key=f"dl_pdf_hosp_{idx}"
                                            )
                                        else:
                                            st.info("📄 Full Medical Report is generating...")

                                elif not any_selected:
                                    # ── Select Hospital button ──
                                    if st.button(f"✅ Select {h_name}", key=f"select_hosp_{idx}",
                                                 type="primary" if is_nearest else "secondary"):

                                        # 1. Smart doctor assignment
                                        doc_info = smart_assign_doctor(h_name, st.session_state.specialization)
                                        doc_id = doc_info["username"]

                                        ref_id = f"REF-{random.randint(1000, 9999)}"
                                        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                        save_referral_request(
                                            patient_name=user,
                                            hospital=h_name,
                                            symptoms=st.session_state.symptoms,
                                            result=f"EMERGENCY REFERRAL | Doctor: {doc_id} | Referral ID: {ref_id}",
                                            lat=saved_lat, lon=saved_lon,
                                            emergency_id=st.session_state.get("active_emergency"),
                                            referral_id=ref_id,
                                            assigned_doctor=doc_id,
                                            patient_id=patient_id,
                                            transfer_status='PENDING',
                                            to_hospital_id=h_id,
                                            from_hospital_id='HOSP_PRASAD',
                                            selected_hospital_id=h_id,
                                            selection_timestamp=now_ts
                                        )

                                        # 2. Auto-share complete medical history
                                        history_shared = auto_share_patient_history(
                                            patient_username=user,
                                            hospital_name=h_name,
                                            doctor_username=doc_id
                                        )

                                        # 3. Update transfer status
                                        try:
                                            conn_tr = sqlite3.connect("hospital.db")
                                            c_tr = conn_tr.cursor()
                                            c_tr.execute("""
                                                UPDATE hospital_requests
                                                SET transfer_status='SENT', referral_status='SENT'
                                                WHERE referral_id=?
                                            """, (ref_id,))
                                            conn_tr.commit()
                                            conn_tr.close()

                                            auto_generate_referral_report(
                                                user=user, patient_id=patient_id,
                                                emergency_id=st.session_state.get("active_emergency"),
                                                ref_id=ref_id, h_id=h_id, doc_id=doc_id,
                                                symptoms=st.session_state.symptoms,
                                                result_text=f"EMERGENCY REFERRAL | Doctor: {doc_id}",
                                                risk_score=85
                                            )
                                        except Exception as e:
                                            st.error(f"Referral update failed: {e}")

                                        save_emergency(
                                            emergency_id=st.session_state.get("active_emergency"),
                                            patient_id=patient_id,
                                            patient_name=user,
                                            emergency_type="Cardiac Emergency" if st.session_state.first_aid_key == "heart_attack" else "General Emergency",
                                            lat=saved_lat, lon=saved_lon,
                                            address=f"{saved_city} Center",
                                            severity=st.session_state.emerg_level,
                                            status='PENDING',
                                            assigned_doctor=doc_id
                                        )

                                        if st.session_state.get("ambulance_required_flag", 0) == 1:
                                            conn_amb = sqlite3.connect("hospital.db")
                                            c_amb = conn_amb.cursor()
                                            c_amb.execute("UPDATE emergencies SET ambulance_status='Requested', ambulance_vehicle='AMB-108' WHERE emergency_id=?", (st.session_state.get("active_emergency"),))
                                            conn_amb.commit()
                                            conn_amb.close()

                                        st.session_state.selected_hospital = h_name
                                        st.session_state.assigned_doctor   = doc_id
                                        st.session_state.active_referral   = ref_id

                                        # 4. Generate referral PDF and store in session
                                        try:
                                            from utils import generate_referral_pdf
                                            _first_aid_txt = st.session_state.get("first_aid_content", "Keep the patient calm and comfortable.")
                                            ref_pdf_bytes = generate_referral_pdf(
                                                patient_username=user,
                                                symptoms=st.session_state.symptoms,
                                                specialization=st.session_state.get("specialization", "Emergency Medicine"),
                                                severity=str(st.session_state.get("emerg_level", "High")),
                                                from_hospital="Prasad Hospital",
                                                to_hospital=h_name,
                                                doctor_name=doc_info["name"],
                                                doctor_specialization=doc_info["specialization"],
                                                doctor_qualification=doc_info.get("qualification", "MBBS"),
                                                doctor_experience=doc_info.get("experience", "N/A"),
                                                referral_id=ref_id,
                                                emergency_id=str(st.session_state.get("active_emergency", "N/A")),
                                                risk_score=85,
                                                first_aid_text=_first_aid_txt,
                                            )
                                            st.session_state["referral_pdf_bytes"] = ref_pdf_bytes
                                            st.session_state["referral_pdf_name"]  = f"Referral_{ref_id}_{user}.pdf"
                                        except Exception as pdf_err:
                                            print("Referral PDF generation error:", pdf_err)
                                            st.session_state["referral_pdf_bytes"] = None

                                        # Success banner
                                        st.success(f"✅ **{h_name}** selected! Referral ID: **{ref_id}**")
                                        st.info(f"👨‍⚕️ **Assigned Doctor:** {doc_info['name']} ({doc_info['specialization']})")
                                        if history_shared:
                                            st.success("📋 **Medical history automatically shared** with hospital & assigned doctor.")

                                        # Show download button before rerun so user can download
                                        if st.session_state.get("referral_pdf_bytes"):
                                            st.markdown("""
                                            <div style='background:linear-gradient(90deg,#e3f9e5,#c3f0ca);
                                                 border-left:5px solid #27ae60;border-radius:10px;
                                                 padding:10px 14px;margin:8px 0;'>
                                              <b style='color:#1a7a34;font-size:15px;'>📄 Referral Letter Ready!</b><br>
                                              <span style='color:#2d6a4f;font-size:13px;'>Your official referral PDF has been generated. Click below to download.</span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            st.download_button(
                                                label="📥 Download Official Referral Letter PDF",
                                                data=st.session_state["referral_pdf_bytes"],
                                                file_name=st.session_state["referral_pdf_name"],
                                                mime="application/pdf",
                                                key=f"dl_ref_select_{idx}"
                                            )
                                        st.rerun()
                                else:
                                    if not is_selected_hosp:
                                        st.info("Another hospital has already been selected for this emergency.")

                # Patient Emergency Status Panel loaded dynamically
                if st.session_state.get("emerg_detected") == "YES":
                    conn_st = sqlite3.connect("hospital.db")
                    c_st = conn_st.cursor()
                    c_st.execute("SELECT status, ambulance_status, ambulance_vehicle, assigned_doctor FROM emergencies WHERE patient_name=? AND status != 'Completed' ORDER BY id DESC LIMIT 1", (user,))
                    active_emerg_db = c_st.fetchone()
                    
                    # Fetch referral details including referral_id
                    c_st.execute("SELECT hospital, referral_status, lat, lon, status, transfer_status, referral_id FROM hospital_requests WHERE patient_name=? AND emergency_id=? ORDER BY id DESC LIMIT 1", (user, st.session_state.get("active_emergency")))
                    active_ref_db = c_st.fetchone()
                    conn_st.close()
                    
                    if active_emerg_db:
                        doc_name_st = active_emerg_db[3]
                        if doc_name_st:
                            doc_info_st = get_doctor_details(doc_name_st)
                            doc_disp_st = doc_info_st["name"] if doc_info_st else doc_name_st
                        else:
                            doc_disp_st = "—"
                            
                        hosp_disp_st = active_ref_db[0] if active_ref_db else "—"
                        ref_status_st = active_ref_db[1] if active_ref_db else "—"
                        loc_disp_st = saved_city if saved_city else "—"
                        resp_disp_st = active_ref_db[4] if active_ref_db else "—"
                        trans_status_st = active_ref_db[5] if active_ref_db else "—"
                        active_ref_id = active_ref_db[6] if active_ref_db else None
                        
                        # Fetch report status
                        report_st_val = "—"
                        if active_ref_id:
                            rep_rec = get_medical_report_by_referral(active_ref_id)
                            if rep_rec:
                                status_str = rep_rec.get("status")
                                report_st_val = "READY" if status_str == "REPORT_READY" else ("Generation Failed" if status_str == "REPORT_FAILED" else status_str)
                        
                        st.write("---")
                        st.write("### 🚨 Patient Emergency Status")
                        st.markdown(f"""
                        <div style='background:#fff0f0; padding:15px; border-radius:8px; border-left:5px solid red; color: #333;'>
                            <strong>Emergency Status:</strong> {active_emerg_db[0]}<br>
                            <strong>Ambulance Status:</strong> {active_emerg_db[1]} (Vehicle: {active_emerg_db[2]})<br>
                            <strong>Ambulance ID:</strong> {active_emerg_db[2] if active_emerg_db[2] else 'Not available'}<br>
                            <strong>Ambulance Location:</strong> Not available<br>
                            <strong>Selected Hospital:</strong> {hosp_disp_st}<br>
                            <strong>Assigned Doctor:</strong> {doc_disp_st}<br>
                            <strong>Referral Status:</strong> {ref_status_st}<br>
                            <strong>Clinical Profile Transfer:</strong> {trans_status_st}<br>
                            <strong>Medical Report:</strong> {report_st_val}<br>
                            <strong>Hospital Response:</strong> {resp_disp_st}<br>
                            <strong>Hospital Location:</strong> {loc_disp_st}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if report_st_val == "READY" and active_ref_id:
                            pdf_bytes_st = None
                            rep_rec_st = get_medical_report_by_referral(active_ref_id)
                            if rep_rec_st and rep_rec_st.get("report_file_path"):
                                f_path_st = rep_rec_st.get("report_file_path")
                                if os.path.exists(f_path_st):
                                    with open(f_path_st, "rb") as f_r_st:
                                        pdf_bytes_st = f_r_st.read()
                            
                            if pdf_bytes_st is None:
                                from utils import generate_pdf_report
                                pdf_bytes_st = generate_pdf_report(user, st.session_state.get("symptoms", ""), f"Emergency Referral | Doctor: {doc_disp_st} | Referral ID: {active_ref_id}", 85, report_type="Referral")
                                if rep_rec_st and rep_rec_st.get("report_file_path"):
                                    with open(rep_rec_st.get("report_file_path"), "wb") as f_w_st:
                                        f_w_st.write(pdf_bytes_st)
                            
                            col_pdf_st1, col_pdf_st2 = st.columns(2)
                            with col_pdf_st1:
                                if st.button("📄 View Medical Report", key="btn_view_rep_status_panel"):
                                    from database import load_patient_clinical_data
                                    p_prof = load_patient_clinical_data(user)
                                    st.markdown(f"""
                                    <div style='background:#f4f9f4; padding:15px; border-radius:8px; border-left:5px solid green; color: #333; margin-top:10px;'>
                                        <h4 style='color:green; margin-top:0;'>📄 Emergency Medical Report</h4>
                                        <strong>Patient ID:</strong> {p_prof.get('patient_id', user) if p_prof else user}<br>
                                        <strong>Symptoms:</strong> {st.session_state.get('symptoms', '')}<br>
                                        <strong>Emergency Level:</strong> {st.session_state.get('emerg_level', 'High')}<br>
                                        <strong>Emergency Type:</strong> {st.session_state.get('specialization', 'Cardiology')}<br>
                                        <strong>Allergies:</strong> {p_prof.get('allergies', 'None') if p_prof else 'None'}<br>
                                        <strong>Chronic Conditions:</strong> {p_prof.get('chronic_diseases', 'None') if p_prof else 'None'}<br>
                                        <strong>Assigned Doctor:</strong> {doc_disp_st}<br>
                                        <strong>Referral Status:</strong> {ref_status_st}<br>
                                        <strong>Clinical Profile Transfer:</strong> {trans_status_st}<br>
                                        <strong>Medical Report Status:</strong> READY
                                    </div>
                                    """, unsafe_allow_html=True)
                            with col_pdf_st2:
                                st.download_button(
                                    label="📥 Download Medical Report PDF",
                                    data=pdf_bytes_st,
                                    file_name=f"Referral_Report_{user}.pdf",
                                    mime="application/pdf",
                                    key="dl_pdf_status_panel"
                                )

    with tabs[1]:
        st.subheader("📋 Demographic Profile & Clinical History")
        
        st.markdown(f"""
        <div style='background:#f9f9f9; padding:15px; border-radius:8px; border:1px solid #ddd;'>
            <strong>Patient ID:</strong> {patient_id}<br>
            <strong>Full Name:</strong> {p_profile[1] if p_profile else user}<br>
            <strong>Age / Gender:</strong> {p_profile[2] if p_profile else 30} / {p_profile[3] if p_profile else 'Male'}<br>
            <strong>Phone / Contact:</strong> {p_profile[4] if p_profile else ''}<br>
            <strong>Blood Group:</strong> {p_profile[5] if p_profile else 'O+'}<br>
            <strong>Allergies:</strong> {p_profile[6] if p_profile else 'None'}<br>
            <strong>Chronic Conditions:</strong> {p_profile[7] if p_profile else 'None'}
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.write("**📜 Chronological Medical History Timeline:**")
        
        from database import get_consultations, get_prescriptions, get_emergencies
        timeline_events = []
        
        cons_recs = get_consultations(patient_id)
        for r in cons_recs:
            timeline_events.append({
                "id": r.get("consultation_id", "CONS-N/A"),
                "date": r["created_at"],
                "type": "Outpatient Consultation",
                "symptoms": r["symptoms"],
                "details": f"Hospital: {r.get('hospital_id', 'Prasad Hospital')} | Symptoms: {r['symptoms']} | Diagnosis: {r['diagnosis']} | Doctor: {r.get('doctor_id', '—')} | Plan: {r['treatment_plan']}"
            })
            
        prescription_recs = get_prescriptions(patient_id)
        for r in prescription_recs:
            timeline_events.append({
                "id": r.get("drug_name", "DRUG-N/A"),
                "date": r["date_time"],
                "type": "Medication Prescribed",
                "symptoms": "Prescription Order",
                "details": f"Hospital: {r.get('hospital_id', 'Prasad Hospital')} | Drug: {r['drug_name']} {r['dose']}{r['unit']} | Dose: {r['frequency']} for {r['duration']} | Doctor: {r.get('doctor_id', '—')}"
            })
            
        emerg_recs = get_emergencies(patient_id)
        for r in emerg_recs:
            timeline_events.append({
                "id": r.get("emergency_id", "EMERG-N/A"),
                "date": r.get("detection_time", "N/A"),
                "type": "Emergency Incident",
                "symptoms": "Emergency Trigger",
                "details": f"Hospital: Prasad Hospital | Category: {r.get('emergency_type', '—')} | Severity: {r.get('severity', '—')} | Doctor: {r.get('assigned_doctor', '—')} | Status: {r.get('status', '—')}"
            })
            
        timeline_events = sorted(timeline_events, key=lambda x: x["date"], reverse=True)
        if timeline_events:
            for idx_ev, ev in enumerate(timeline_events):
                st.info(f"📅 {ev['date']} | **{ev['type']}** [ID: {ev['id']}]\n{ev['details']}")
                
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    if st.button("View Report", key=f"view_hist_rep_{idx_ev}"):
                        st.success(f"Clinical Report {ev['id']} details verified. Click Download to save PDF locally.")
                with col_h2:
                    from utils import generate_pdf_report
                    rep_pdf = generate_pdf_report(user, ev.get('symptoms', 'Triage Review'), ev['details'], 75, report_type="Clinical")
                    st.download_button(
                        label="Download PDF",
                        data=rep_pdf,
                        file_name=f"Report_{ev['id']}_{user}.pdf",
                        mime="application/pdf",
                        key=f"dl_hist_pdf_{idx_ev}"
                    )
        else:
            st.info("No prior medical history found.")

    with tabs[2]:
        st.subheader("💊 Prescription & Medication Safety Center")
        
        # 1. Authorized Emergency Protocol Medication
        st.markdown("### 🚨 Authorized Emergency Protocol Medication")
        if st.session_state.get("emerg_detected") == "YES":
            protocol_key = st.session_state.get("first_aid_key")
            if protocol_key == "heart_attack":
                st.warning("""
                **Authorized Emergency Medication:** Aspirin (325mg chewable)
                - **Generic Name:** Acetylsalicylic acid
                - **Class/Purpose:** Antiplatelet / Myocardial infarction prevention
                - **Dose/Amount:** 325mg (1 tablet)
                - **Route:** Oral (Chew & swallow)
                - **Frequency:** Immediate single dose
                - **Status:** Authorized under Cardiac Emergency Protocol
                - **Warnings:** Avoid if allergic or active GI bleed.
                """)
                safety = check_medication_safety(patient_id, "Aspirin")
                if safety["allergy_warning"] != "None": st.error(safety["allergy_warning"])
                if safety["interaction_warning"] != "None": st.error(safety["interaction_warning"])
                if safety["contraindication_warning"] != "None": st.error(safety["contraindication_warning"])
            elif protocol_key == "asthma":
                st.warning("""
                **Authorized Emergency Medication:** Albuterol Inhaler (Rescue Inhaler)
                - **Generic Name:** Albuterol sulfate
                - **Class/Purpose:** Bronchodilator / Relief of acute bronchospasm
                - **Dose/Amount:** 2 puffs (180mcg)
                - **Route:** Inhalation
                - **Frequency:** Immediate single dose
                - **Status:** Authorized under Pulmonology Emergency Protocol
                """)
                safety = check_medication_safety(patient_id, "Albuterol")
                if safety["allergy_warning"] != "None": st.error(safety["allergy_warning"])
                if safety["interaction_warning"] != "None": st.error(safety["interaction_warning"])
                if safety["contraindication_warning"] != "None": st.error(safety["contraindication_warning"])
            else:
                st.info("ℹ️ Clinical review required before medication. No pre-authorized protocol drugs matches this emergency condition.")
        else:
            st.info("No active emergency protocol medication required.")

        # 2. Doctor-Confirmed Prescriptions
        st.markdown("### 👨‍⚕️ Doctor-Confirmed Prescriptions")
        from database import get_prescriptions
        meds_list = get_prescriptions(patient_id)
        
        if meds_list:
            df_meds = pd.DataFrame(meds_list)
            df_meds = df_meds[["drug_name", "dose", "unit", "frequency", "route", "duration", "instructions", "doctor_id", "hospital_id", "date_time", "status"]]
            df_meds.columns = ["Medicine", "Dose", "Unit", "Frequency", "Route", "Duration", "Special Instructions", "Doctor", "Hospital", "Date Prescribed", "Status"]
            st.table(df_meds)
            
            for m in meds_list:
                safety = check_medication_safety(patient_id, m["drug_name"])
                if safety["allergy_warning"] != "None" or safety["interaction_warning"] != "None" or safety["contraindication_warning"] != "None":
                    with st.expander(f"⚠️ Safety Alerts for {m['drug_name']}"):
                        if safety["allergy_warning"] != "None": st.error(safety["allergy_warning"])
                        if safety["interaction_warning"] != "None": st.error(safety["interaction_warning"])
                        if safety["contraindication_warning"] != "None": st.error(safety["contraindication_warning"])
        else:
            st.info("No active doctor-confirmed prescription records found.")

        # 3. AI Medication Information (Clinical reference support)
        st.markdown("### 💡 AI Medication Information (Clinical Decision Support)")
        if st.session_state.get("analyzed", False) and st.session_state.get("symptoms"):
            symptom_in = st.session_state.get("symptoms")
            conn_sd = sqlite3.connect("hospital.db")
            c_sd = conn_sd.cursor()
            c_sd.execute("SELECT Disease, Medicines, Advice FROM symptoms_disease")
            sd_rows = c_sd.fetchall()
            conn_sd.close()
            
            matched_med = None
            matched_dis = None
            matched_adv = None
            for dis, med, adv in sd_rows:
                if dis.lower() in symptom_in.lower() or any(w in symptom_in.lower() for w in dis.lower().split()):
                    matched_med = med
                    matched_dis = dis
                    matched_adv = adv
                    break
            
            if not matched_med:
                matched_med = "Paracetamol"
                matched_dis = "General Indication"
                matched_adv = "Stay hydrated and rest."
                
            st.info(f"""
            **AI Suggested Safety Information:**
            - **Suggested Medicine:** {matched_med}
            - **Condition Indication:** {matched_dis}
            - **Clinical Advice:** {matched_adv}
            - **Disclaimer:** AI output is for decision-support reference only. Do not treat as a confirmed diagnosis or doctor prescription.
            """)
            
            safety = check_medication_safety(patient_id, matched_med)
            with st.expander(f"🔍 Safety Screen for AI Suggested {matched_med}"):
                if safety["allergy_warning"] != "None": st.error(safety["allergy_warning"])
                if safety["interaction_warning"] != "None": st.error(safety["interaction_warning"])
                if safety["contraindication_warning"] != "None": st.error(safety["contraindication_warning"])
                if safety["allergy_warning"] == "None" and safety["interaction_warning"] == "None" and safety["contraindication_warning"] == "None":
                    st.success("✅ No allergen, interaction or contraindication warnings detected.")
        else:
            st.write("Please describe your symptoms and run AI analysis first to fetch clinical drug references.")

    with tabs[3]:
        st.subheader("📡 Live Hospital Referral & Coordination Updates")
        
        conn_upd = sqlite3.connect("hospital.db")
        c_upd = conn_upd.cursor()
        c_upd.execute("""
            SELECT hospital, status, referral_status, last_updated, referral_id 
            FROM hospital_requests 
            WHERE patient_name=? 
            ORDER BY id DESC LIMIT 5
        """, (user,))
        reqs = c_upd.fetchall()
        conn_upd.close()
        
        if reqs:
            for r in reqs:
                st.success(f"🔔 Referred to **{r[0]}** [Referral ID: {r[4]}] | Status: **{r[2]}** (Last Updated: {r[3]})")
        else:
            st.info("No active referral request updates logged in the coordination system.")

    st.markdown("---")
    if st.button("Logout", width="stretch"):
        st.session_state.clear()
        st.rerun()
