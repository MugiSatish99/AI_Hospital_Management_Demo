import streamlit as st
import pandas as pd
import time
import sqlite3
import os

from database import (
    get_patients, add_note, get_users,
    get_doctor_extra, get_messages, send_message,
    update_patient_status,
    get_requests,
    update_request_status,
    get_completed_cases,
    get_doctors_by_specialization
)

from ai import full_ai_analysis
from alerts import send_alert
from emergency import get_issue_type, get_emergency_level
from first_aid import get_first_aid
from utils import format_output, map_symptom_to_specialization


def clean_value(value):
    if value is None or str(value).lower() in ["none", "nan", ""]:
        return "Not Assigned"
    return value


def assign_doctor_by_symptoms(symptoms, users):
    specialization = map_symptom_to_specialization(symptoms)
    doctors = get_doctors_by_specialization(specialization)

    if doctors:
        return doctors[0]

    docs = [u[1] for u in users if len(u) > 3 and u[3] == "doctor"]
    return docs[0] if docs else "admin"


def create_case(message, doctor):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS cases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor TEXT,
        message TEXT,
        status TEXT
    )
    """)

    c.execute("""
    SELECT id FROM cases
    WHERE doctor=? AND message=?
    """, (doctor, message))

    if c.fetchone():
        conn.close()
        return

    c.execute("""
    INSERT INTO cases (doctor, message, status)
    VALUES (?, ?, ?)
    """, (doctor, message, "PENDING"))

    conn.commit()
    conn.close()


def get_cases(doctor):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, doctor, message, status
    FROM cases
    WHERE doctor=?
    ORDER BY id DESC
    """, (doctor,))

    data = c.fetchall()
    conn.close()

    return [
        {"id": d[0], "doctor": d[1], "message": d[2], "status": d[3]}
        for d in data
        if str(d[3]).upper() != "DONE"
    ]


def update_case(cid, status):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS completed_cases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor TEXT,
        message TEXT,
        completed_time TEXT
    )
    """)

    if str(status).upper() == "DONE":
        c.execute("""
        SELECT doctor, message
        FROM cases
        WHERE id=?
        """, (cid,))

        row = c.fetchone()

        if row:
            doctor = row[0]
            message = row[1]
            now = time.strftime("%Y-%m-%d %H:%M:%S")

            c.execute("""
            INSERT INTO completed_cases
            (doctor, message, completed_time)
            VALUES (?, ?, ?)
            """, (doctor, message, now))

            c.execute("""
            DELETE FROM cases
            WHERE id=?
            """, (cid,))

    else:
        c.execute("""
        UPDATE cases
        SET status=?
        WHERE id=?
        """, (status, cid))

    conn.commit()
    conn.close()


def get_doctor_load():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    try:
        c.execute("""
        SELECT assigned_doctor, COUNT(*)
        FROM patients
        GROUP BY assigned_doctor
        """)
        data = c.fetchall()
    except:
        data = []

    conn.close()
    return {d[0]: d[1] for d in data}


def smart_refresh():
    if "refresh_time" not in st.session_state:
        st.session_state.refresh_time = time.time()

    if time.time() - st.session_state.refresh_time > 8:
        st.session_state.refresh_time = time.time()
        st.rerun()


def push_notification(title, message):
    st.warning(f"{title} - {message}")


def detect_emergency(symptoms):
    danger = [
        "chest pain", "heart attack", "stroke",
        "breathing", "unconscious", "bleeding",
        "accident", "collapse", "critical"
    ]
    return any(d in str(symptoms).lower() for d in danger)


def transfer_patient(pid, doctor_name):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    UPDATE patients
    SET assigned_doctor=?, status=?
    WHERE id=?
    """, (doctor_name, "TRANSFERRED", pid))

    conn.commit()
    conn.close()

    send_alert("doctor", f"New patient assigned to {doctor_name}")


def show():

    if "last_emergency_count" not in st.session_state:
        st.session_state.last_emergency_count = 0

    st.markdown("""
    <style>
    .card {
        background:white;
        padding:14px;
        border-radius:12px;
        margin-bottom:12px;
        box-shadow:0px 2px 8px rgba(0,0,0,0.1);
    }
    .emergency {
        border-left:6px solid red;
        background:#ffe6e6;
    }
    .normal {
        border-left:6px solid green;
    }
    </style>
    """, unsafe_allow_html=True)

    user = st.session_state.user
    users = get_users()

    doctor = next((u for u in users if u[1] == user), None)

    if not doctor:
        st.error("Doctor not found ")
        return

    doctor_name = doctor[4] if len(doctor) > 4 and doctor[4] else user
    phone = doctor[6] if len(doctor) > 6 else "N/A"

    extra = get_doctor_extra(user)

    spec = extra[1] if extra and len(extra) > 1 and extra[1] else "General Physician"
    qualification = extra[2] if extra and len(extra) > 2 and extra[2] else "MBBS"
    experience = extra[3] if extra and len(extra) > 3 and extra[3] else "Fresher"
    availability = extra[4] if extra and len(extra) > 4 and extra[4] else "Available"

    image_path = f"doctor_images/{user}.png"
    db_image = extra[6] if (extra and len(extra) > 6) else None

    st.sidebar.title("Doctor Panel")

    if db_image:
        st.sidebar.image(db_image, width=90)
    elif os.path.exists(image_path):
        st.sidebar.image(image_path, width=90)
    else:
        st.sidebar.image(
            "https://cdn-icons-png.flaticon.com/512/3774/3774299.png",
            width=90
        )

    st.sidebar.markdown(f"###  Dr. {clean_value(doctor_name)}")
    st.sidebar.markdown(f"{clean_value(spec)}")
    st.sidebar.caption(f"{clean_value(qualification)}")
    st.sidebar.caption(f"{clean_value(experience)}")
    st.sidebar.caption(f"{clean_value(availability)}")
    st.sidebar.caption(f"{clean_value(phone)}")

    with st.sidebar.expander("⚙️ Update Photo"):
        new_pic = st.file_uploader("Upload Image (Max 5MB)", type=["jpg", "jpeg", "png"], key="doc_self_pic")
        if new_pic is not None:
            try:
                from utils import process_profile_image
                from database import update_doctor_image
                from datetime import datetime
                
                img_bytes = process_profile_image(new_pic)
                img_path = f"doctor_images/{user}.png"
                os.makedirs("doctor_images", exist_ok=True)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                update_doctor_image(user, img_bytes, img_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.sidebar.success("✅ Success!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    show_only_mine = st.sidebar.toggle("My Patients Only", value=True)

    menu = st.sidebar.radio("Navigation", [
        " Dashboard",
        "🩺 Normal consultations",
        "🚨 Assigned Emergencies",
        "Patients",
        "Emergency",
        "Appointments",
        "Shared Records",
        "Requests",
        "Completed Cases",
        "Chat",
        "AI"
    ])

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    data = get_patients()

    if not data:
        st.warning("No patients")
        return

    df = pd.DataFrame(data, columns=[
        "ID", "Name", "Symptoms", "Result", "Date", "Time",
        "Status", "assigned_doctor", "Hospital"
    ])

    df["assigned_doctor"] = df["assigned_doctor"].fillna("")
    df["Status"] = df["Status"].fillna("NORMAL")
    df["AUTO"] = df.apply(
        lambda row: "EMERGENCY"
        if detect_emergency(row["Symptoms"]) and str(row["Status"]).upper() != "COMPLETED"
        else "NORMAL",
        axis=1
    )
    
    df["sort_emergency"] = df["AUTO"].apply(lambda x: 0 if x == "EMERGENCY" else 1)
    df = df.sort_values(by=["sort_emergency", "ID"], ascending=[True, False])

    for _, row in df.iterrows():
        if not row.get("assigned_doctor"):
            assigned = assign_doctor_by_symptoms(row["Symptoms"], users)

            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()

            try:
                c.execute(
                    "UPDATE patients SET assigned_doctor=? WHERE id=?",
                    (assigned, row["ID"])
                )
                conn.commit()
            except:
                pass

            conn.close()

            msg = f"{row['Name']} - {row['Symptoms']}"
            completed = get_completed_cases(assigned)
            completed_msgs = [str(x[2]).strip().lower() for x in completed]

            if msg.strip().lower() not in completed_msgs:
                create_case(msg, assigned)

    if show_only_mine:
        df = df[
            (df["assigned_doctor"] == user)
            | (df["assigned_doctor"] == "")
            | (df["assigned_doctor"] == "Emergency Duty Doctor")
        ]

    emergency = len(df[df["AUTO"] == "EMERGENCY"])

    if emergency > st.session_state.last_emergency_count:
        push_notification("Emergency", "New case arrived!")

    st.session_state.last_emergency_count = emergency

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("My Patients", len(df[df["assigned_doctor"] == user]))
    c3.metric("Emergency", emergency)

    if menu == " Dashboard":

        st.dataframe(df, width="stretch")

        st.markdown("###  My Cases")

        cases = get_cases(user)

        if not cases:
            st.info("No Active Cases")

        for c in cases:
            st.info(f"{c['message']} ({c['status']})")

            col1, col2 = st.columns(2)

            with col1:
                if c["status"] == "PENDING":
                    if st.button(f"Accept Case {c['id']}", key=f"accept_case_{c['id']}"):
                        update_case(c["id"], "ACCEPTED")
                        st.rerun()

            with col2:
                if st.button(f"Complete Case {c['id']}", key=f"complete_case_{c['id']}"):
                    update_case(c["id"], "DONE")
                    st.success("Case Completed")
                    st.rerun()

        st.markdown("###  Doctor Load")
        loads = get_doctor_load()

        for d, l in loads.items():
            st.write(f"{clean_value(d)} → {l}")

    elif menu == "👥 Patients":

        doctors_list = [u[1] for u in users if len(u) > 3 and u[3] == "doctor"]

        for _, row in df.iterrows():

            cls = "emergency" if row["AUTO"] == "EMERGENCY" else "normal"
            st.markdown(f"<div class='card {cls}'>", unsafe_allow_html=True)

            st.subheader(row["Name"])
            st.write(f" Symptoms: {row['Symptoms']}")
            st.info(f" Hospital: {clean_value(row['Hospital'])}")
            st.info(f" Assigned: {row['assigned_doctor'] or 'Not Assigned'}")
            st.info(f" Status: {row['Status']}")

            recommended_spec = map_symptom_to_specialization(row["Symptoms"])
            st.success(f"Recommended Department: {recommended_spec}")

            if str(row["Status"]).upper() == "COMPLETED":
                st.success("Completed")
                st.markdown("</div>", unsafe_allow_html=True)
                continue

            # Auto-Accept case when viewing
            p_username = None
            for u in users:
                if u[4] == row["Name"] or u[1] == row["Name"]:
                    p_username = u[1]
                    break
            if not p_username:
                p_username = row["Name"]
                
            from database import check_doctor_patient_authorization
            if check_doctor_patient_authorization(doctor_username=user, patient_username=p_username):
                if row["Status"] in ["TRANSFERRED", "ASSIGNED", "PENDING"]:
                    transfer_patient(row["ID"], user)
                    update_patient_status(row["ID"], "IN_PROGRESS")
                    st.rerun()
                    
                st.success("✅ Treatment Authorized. Active Case Details:")
                
                from database import load_patient_clinical_data
                p_details = load_patient_clinical_data(p_username)
                if p_details:
                    st.write(f"**Patient ID:** {p_details.get('patient_id')} | **Age / Gender:** {p_details.get('age')} / {p_details.get('gender')}")
                    st.write(f"**Allergies:** {p_details.get('allergies')} | **Chronic Conditions:** {p_details.get('chronic_diseases')}")
                    st.write(f"**Previous Medications:** {p_details.get('previous_medications')}")
                    
                    st.write("---")
                    st.write("**🤖 Automated AI Clinical Support & Safety Warnings:**")
                    ai_res = full_ai_analysis(row["Symptoms"])
                    st.success(f"🤖 Suggested Diagnosis: {ai_res.get('condition', 'Under review')}\n🚨 Severity Triage: {ai_res.get('severity', 'Normal')}")
                    st.warning("⚠️ Warning: Verify all historical medication drug interactions before treatment.")
                    
                    st.write("---")
                    st.write("**👨‍⚕️ Emergency Clinical Treatment Desk:**")
                    with st.form(f"emerg_treatment_form_{row['ID']}"):
                        doc_diag = st.text_input("Enter Final Clinical Diagnosis", value=ai_res.get('condition', ''))
                        doc_treat_notes = st.text_area("Treatment / Case Advice Summary")
                        
                        confirm_treatment_btn = st.form_submit_button("📋 Confirm Treatment & Complete Case")
                        if confirm_treatment_btn:
                            if doc_diag and doc_treat_notes:
                                add_note(row["ID"], f"Diagnosis: {doc_diag} | Treatment: {doc_treat_notes}")
                                update_patient_status(row["ID"], "COMPLETED")
                                
                                from database import save_patient
                                save_patient(p_username, row["Symptoms"], f"EMERGENCY DIAGNOSIS: {doc_diag}\nTREATMENT: {doc_treat_notes}\nStatus: Completed")
                                
                                st.success("✅ Case completed. Treatment notes saved to patient longitudinal timeline.")
                                st.rerun()
                            else:
                                st.warning("Please fill in both Diagnosis and Treatment summary.")
                                
                    ref_id = row.get("referral_id")
                    from database import get_medical_report_by_referral
                    report_record = get_medical_report_by_referral(ref_id)
                    pdf_bytes = None
                    if report_record and report_record.get("status") == "REPORT_READY":
                        f_path = report_record.get("report_file_path")
                        if os.path.exists(f_path):
                            with open(f_path, "rb") as f_r:
                                pdf_bytes = f_r.read()
                    if pdf_bytes is None:
                        from utils import generate_pdf_report
                        pdf_bytes = generate_pdf_report(p_username, row["Symptoms"], row["Result"], 85)
                        
                    col_doc1, col_doc2 = st.columns(2)
                    with col_doc1:
                        if st.button("📄 View Medical Report", key=f"btn_doc_view_p_{row['ID']}"):
                            st.write("---")
                            st.markdown(f"""
                            <div style='background:#f4f9f4; padding:15px; border-radius:8px; border-left:5px solid green; color: #333;'>
                                <h4 style='color:green;'>📄 Emergency Medical Report</h4>
                                <strong>Patient ID:</strong> {p_details.get('patient_id', p_username)}<br>
                                <strong>Symptoms:</strong> {row['Symptoms']}<br>
                                <strong>Clinical Profile Transfer:</strong> SENT<br>
                                <strong>Medical Report Status:</strong> READY
                            </div>
                            """, unsafe_allow_html=True)
                    with col_doc2:
                        st.download_button(
                            label="📥 Download Medical Report PDF",
                            data=pdf_bytes,
                            file_name=f"Referral_Report_{p_username}.pdf",
                            mime="application/pdf",
                            key=f"dl_doc_ref_{row['ID']}"
                        )
            else:
                st.error("🚫 Access Denied: You are not authorized to view this patient's medical history.")

            st.markdown("</div>", unsafe_allow_html=True)

    elif menu == "🩺 Normal consultations":
        st.subheader("🩺 Outpatient Consultation & Clinical Work Desk")
        
        import sqlite3
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM consultations WHERE doctor_id=? ORDER BY id DESC", (user,))
        consultations_list = c.fetchall()
        conn.close()
        
        if not consultations_list:
            st.info("No active outpatient consultations assigned to you.")
        else:
            for cons in consultations_list:
                c_id = cons[1]
                p_id = cons[2]
                p_user = cons[3]
                symptoms = cons[4]
                observations = cons[5]
                diag = cons[6]
                treatment = cons[7]
                follow_up = cons[8]
                created = cons[11]
                
                with st.expander(f"📋 Consultation {c_id} - Patient: {p_id} ({created})", expanded=(diag == "Pending Doctor Evaluation")):
                    st.write(f"**Symptoms reported:** {symptoms}")
                    st.write(f"**Clinical Observations:** {observations}")
                    st.write(f"**Current Status:** {diag}")
                    
                    st.write("---")
                    st.write("**📜 Authorized Patient Medical History & Timeline:**")
                    from database import get_consultations, get_prescriptions, get_emergencies
                    timeline_events = []
                    
                    cons_recs = get_consultations(p_id)
                    for r in cons_recs:
                        if r["consultation_id"] != c_id:
                            timeline_events.append({
                                "date": r["created_at"],
                                "type": "Normal Consultation",
                                "details": f"Symptoms: {r['symptoms']} | Diagnosis: {r['diagnosis']}"
                            })
                    prescription_recs = get_prescriptions(p_id)
                    for r in prescription_recs:
                        timeline_events.append({
                            "date": r["date_time"],
                            "type": "Medication Prescribed",
                            "details": f"Drug: {r['drug_name']} {r['dose']}{r['unit']} | Dose: {r['frequency']} for {r['duration']}"
                        })
                    emerg_recs = get_emergencies(p_id)
                    for r in emerg_recs:
                        timeline_events.append({
                            "date": r["detection_time"],
                            "type": "Emergency Incident",
                            "details": f"Type: {r['emergency_type']} | Status: {r['status']}"
                        })
                        
                    timeline_events = sorted(timeline_events, key=lambda x: x["date"], reverse=True)
                    if timeline_events:
                        for ev in timeline_events[:5]:
                            st.text(f"📅 {ev['date']} | {ev['type']}: {ev['details']}")
                    else:
                        st.text("No prior history found.")
                        
                    st.write("---")
                    st.write("**🤖 AI Clinical Decision Support:**")
                    ai_res = full_ai_analysis(symptoms)
                    st.success(f"🤖 Suggested Diagnosis: {ai_res.get('condition', 'Under review')}\n🚨 Severity Triage: {ai_res.get('severity', 'Normal')}")
                    st.info("💡 Validated Decision Support Only - Doctor Consultation Required")
                    
                    st.write("---")
                    st.write("**👨‍⚕️ Clinical Diagnosis & Prescriptions Formulation:**")
                    with st.form(f"consultation_form_{c_id}"):
                        doc_diag = st.text_input("Enter Final Diagnosis", value=diag if diag != "Pending Doctor Evaluation" else "")
                        doc_treat = st.text_area("Treatment Plan / Guidance", value=treatment if treatment != "Pending Doctor Evaluation" else "")
                        doc_follow = st.text_input("Follow-up Directions", value=follow_up if follow_up != "TBD" else "")
                        
                        st.write("**💊 Medication / Prescription Form:**")
                        d_name = st.text_input("Drug Name", placeholder="e.g. Amoxicillin")
                        d_dose = st.text_input("Dose/Amount", placeholder="e.g. 500")
                        d_unit = st.selectbox("Unit", ["mg", "ml", "tablet", "capsule", "drops"])
                        d_freq = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times a day", "Every 4 hours", "As needed"])
                        d_route = st.selectbox("Route", ["Oral", "Intravenous", "Topical", "Inhalation"])
                        d_dur = st.text_input("Duration", placeholder="e.g. 5 days")
                        d_inst = st.text_input("Special Instructions", placeholder="e.g. Take after food")
                        
                        submit_btn = st.form_submit_button("Confirm Diagnosis & Save Prescription")
                        if submit_btn:
                            if doc_diag and doc_treat:
                                import sqlite3
                                conn_up = sqlite3.connect("hospital.db")
                                c_up = conn_up.cursor()
                                c_up.execute("""
                                UPDATE consultations 
                                SET diagnosis=?, treatment_plan=?, follow_up=? 
                                WHERE consultation_id=?
                                """, (doc_diag, doc_treat, doc_follow, c_id))
                                conn_up.commit()
                                conn_up.close()
                                
                                from database import save_patient
                                save_patient(p_user, symptoms, f"Diagnosis: {doc_diag}\nTreatment: {doc_treat}\nMedicine: {d_name} {d_dose}{d_unit} | Frequency: {d_freq}\nAdvice: {doc_follow}")
                                
                                if d_name:
                                    import random
                                    new_rx_id = f"RX-{random.randint(1000, 9999)}"
                                    from database import save_prescription
                                    save_prescription(
                                        prescription_id=new_rx_id,
                                        consultation_id=c_id,
                                        patient_id=p_id,
                                        drug_name=d_name,
                                        dose=d_dose,
                                        unit=d_unit,
                                        frequency=d_freq,
                                        route=d_route,
                                        duration=d_dur,
                                        instructions=d_inst,
                                        doctor_id=user,
                                        hospital_id="Prasad Hospital"
                                    )
                                    
                                st.success("✅ Consultation records, prescriptions, and diagnosis saved to longitudinal medical history!")
                                st.rerun()
                            else:
                                st.warning("Please fill in Diagnosis and Treatment Plan.")

    elif menu == "🚨 Assigned Emergencies":
        st.subheader("🚨 Assigned Emergency Referral Cases")
        
        import sqlite3
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM hospital_requests WHERE assigned_doctor=? ORDER BY id DESC", (user,))
        assigned_refs = c.fetchall()
        conn.close()
        
        if not assigned_refs:
            st.info("No active emergency referral cases assigned to you.")
        else:
            for r in assigned_refs:
                r_id, p_user, hosp_name, status, symptoms, result, lat, lon, created, emerg_id, ref_id, doc_username, amb_status, amb_veh, ref_status, pat_id, updated, *extra = r
                
                with st.expander(f"🚨 Case {emerg_id} - Referral {ref_id} (Patient ID: {pat_id})", expanded=True):
                    st.write(f"**Referral From:** Prasad Hospital")
                    st.write(f"**Referral To:** {hosp_name}")
                    st.write(f"**Timeline Status:** {status}")
                    st.write(f"**Ambulance Status:** {amb_status} ({amb_veh})")
                    st.write(f"**Symptom Complaint:** {symptoms}")
                    st.write(f"**Referral Date/Time:** {created}")
                    
                    from database import load_patient_clinical_data
                    p_details = load_patient_clinical_data(p_user)
                    if p_details:
                        st.write("### 👤 Patient Demographics & Profile")
                        st.write(f"**Full Name:** {p_details.get('name')}")
                        st.write(f"**Age / Gender:** {p_details.get('age')} / {p_details.get('gender')}")
                        st.write(f"**Phone / Emergency Contact:** {p_details.get('phone')} / {p_details.get('emergency_contact')}")
                        
                        st.write("### 🩺 Clinical Profile")
                        st.write(f"**Allergies:** {p_details.get('allergies')}")
                        st.write(f"**Chronic Diseases:** {p_details.get('chronic_diseases')}")
                        st.write(f"**Previous Diseases:** {p_details.get('previous_diseases')}")
                        st.write(f"**Previous Medications:** {p_details.get('previous_medications')}")
                        st.write(f"**Past Medical Reports Summary:** {p_details.get('previous_reports')}")
                        
                        from database import get_history
                        h_events = get_history(p_user)
                        if h_events:
                            st.write("### 📜 Previous Medical History")
                            for h in h_events:
                                st.info(f"📅 {h[3]} at {h[4]} | Symptoms: {h[1]} | Diagnosis & Advice: {h[2]}")
                                
                        st.write("---")
                        from database import get_medical_report_by_referral
                        report_record = get_medical_report_by_referral(ref_id)
                        pdf_bytes = None
                        if report_record and report_record.get("status") == "REPORT_READY":
                            f_path = report_record.get("report_file_path")
                            if os.path.exists(f_path):
                                with open(f_path, "rb") as f_r:
                                    pdf_bytes = f_r.read()
                        if pdf_bytes is None:
                            from utils import generate_pdf_report
                            pdf_bytes = generate_pdf_report(p_user, symptoms, result, 85)
                            
                        col_doc1, col_doc2 = st.columns(2)
                        with col_doc1:
                            if st.button("📄 View Medical Report", key=f"btn_doc_view_p_emerg_{r_id}"):
                                st.write("---")
                                st.markdown(f"""
                                <div style='background:#f4f9f4; padding:15px; border-radius:8px; border-left:5px solid green; color: #333;'>
                                    <h4 style='color:green;'>📄 Emergency Medical Report</h4>
                                    <strong>Patient ID:</strong> {p_details.get('patient_id', p_user)}<br>
                                    <strong>Symptoms:</strong> {symptoms}<br>
                                    <strong>Clinical Profile Transfer:</strong> SENT<br>
                                    <strong>Medical Report Status:</strong> READY
                                </div>
                                """, unsafe_allow_html=True)
                        with col_doc2:
                            st.download_button(
                                label="📥 Download Medical Report PDF",
                                data=pdf_bytes,
                                file_name=f"Referral_Report_{p_user}.pdf",
                                mime="application/pdf",
                                key=f"dl_doc_assigned_{r_id}"
                            )

    elif menu == "Emergency":

        em_df = df[(df["AUTO"] == "EMERGENCY") & (df["Status"] != "COMPLETED")]

        if em_df.empty:
            st.success("No emergency cases")

        for _, row in em_df.iterrows():
            st.error(f" {row['Name']} - {row['Symptoms']}")

            if st.button(f"Accept {row['ID']}", key=f"em_accept_{row['ID']}"):
                transfer_patient(row["ID"], user)
                update_patient_status(row["ID"], "IN_PROGRESS")
                st.success("Accepted ")
                st.rerun()

    elif menu == "Appointments":
        st.subheader("📅 Booked Consultations")
        from database import get_appointments, update_appointment_status
        apps = get_appointments(user, 'doctor')
        
        if not apps:
            st.info("No booked appointments found.")
        else:
            for ap in apps:
                st.markdown("---")
                pat_name = ap['patient_name']
                # Search for patient's full name
                pat_fullname = pat_name
                for u in users:
                    if u[1] == pat_name:
                        pat_fullname = u[4] if (len(u) > 4 and u[4]) else pat_name
                        break
                        
                st.write(f"👤 **Patient:** {pat_fullname} ({pat_name})")
                st.write(f"📅 **Date:** {ap['appointment_date']} | ⏰ **Time:** {ap['appointment_time']}")
                st.write(f"📌 **Status:** {ap['status']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if ap['status'] == "Pending":
                        if st.button(f"Confirm Appointment {ap['id']}", key=f"conf_app_{ap['id']}"):
                            update_appointment_status(ap['id'], "Confirmed")
                            st.success("Appointment Confirmed!")
                            st.rerun()
                with col2:
                    if ap['status'] in ["Pending", "Confirmed"]:
                        if st.button(f"Mark Completed {ap['id']}", key=f"comp_app_{ap['id']}"):
                            update_appointment_status(ap['id'], "Completed")
                            st.success("Appointment Completed!")
                            st.rerun()

    elif menu == "Shared Records":
        st.subheader("📋 Shared Clinical Patient Records")
        st.caption("These records are shared automatically when a patient experiences a Critical emergency or selects you for consultation.")
        
        from database import get_shared_history
        import json
        
        records = get_shared_history(doctor_username=user)
        if not records:
            st.info("No shared patient records found.")
        else:
            for r in records:
                try:
                    payload = json.loads(r['shared_data'])
                except Exception as e:
                    payload = {}
                    
                st.markdown("---")
                st.markdown(f"### 👤 Patient: {payload.get('patient_name')} ({payload.get('patient_id')})")
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Age:** {payload.get('age')} | **Gender:** {payload.get('gender')}")
                    st.write(f"**Phone:** {payload.get('phone')}")
                    st.write(f"**Emergency Contact:** {payload.get('emergency_contact')}")
                    st.write(f"**Location:** {payload.get('location')}")
                with c2:
                    st.write(f"**Emergency Severity:** :red[{payload.get('emergency_severity')}]")
                    st.write(f"**Calculated Risk Score:** {payload.get('risk_score')}%")
                    st.write(f"**Shared On:** {payload.get('timestamp')}")
                    
                st.info(f"📋 **Current Symptoms:** {payload.get('current_symptoms')}")
                st.success(f"🤖 **Predicted Condition:** {payload.get('predicted_disease')}")
                
                with st.expander("🩺 View Complete Clinical Profile"):
                    st.write(f"🚫 **Allergies:** {payload.get('allergies')}")
                    st.write(f"🩺 **Existing Diseases:** {payload.get('existing_diseases')}")
                    st.write(f"💊 **Previous Diseases:** {payload.get('previous_diseases')}")
                    st.write(f"💊 **Previous Medications:** {payload.get('previous_medications')}")
                    st.write(f"📋 **Past Medical Reports Summary:** {payload.get('previous_reports')}")
                    st.write(f"🚑 **First Aid Provided:** {payload.get('first_aid_recommendations')}")
                    st.write(f"💊 **Suggested Medications:** {payload.get('medication_recommendations')}")

                # Doctor recommendations form
                with st.expander("➕ Add Recommendations & Follow-up Directions"):
                    with st.form(f"recommendation_form_{r['id']}"):
                        rec_note = st.text_area("Recommendations / Follow-up Instructions", placeholder="e.g. Take medicine after food, schedule a physical exam in 3 days")
                        submit_rec = st.form_submit_button("Save Recommendation")
                        if submit_rec:
                            if rec_note:
                                from database import add_note
                                add_note(r['patient_username'], f"Doctor recommendation: {rec_note}")
                                st.success("Recommendation saved successfully!")
                                st.rerun()
                            else:
                                st.warning("Please enter a recommendation.")

    elif menu == "Requests":

        st.subheader(" Emergency Hospital Requests")

        requests = get_requests()

        if not requests:
            st.info("No requests available")

        else:
            for r in requests:
                req_id = r[0]

                st.markdown("---")
                st.write(f"Patient: {r[1]}")
                st.write(f"Hospital: {r[2]}")
                st.write(f"Symptoms: {r[3]}")
                st.write(f"Result: {r[4]}")
                st.write(f"Location: ({r[5]}, {r[6]})")
                st.write(f"Status: {r[7]}")
                st.write(f"Time: {r[8]}")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(f"Accept Request {req_id}", key=f"doctor_accept_req_{req_id}"):
                        update_request_status(req_id, "Accepted")
                        st.success("Request Accepted")
                        st.rerun()

                with col2:
                    if st.button(f"Reject Request {req_id}", key=f"doctor_reject_req_{req_id}"):
                        update_request_status(req_id, "Rejected")
                        st.error("Request Rejected")
                        st.rerun()

    elif menu == " Completed Cases":

        st.title(" Completed Cases")

        completed = get_completed_cases(user)

        if not completed:
            st.info("No completed cases")

        for c in completed:
            st.success(f"{c[2]}")
            st.write(f"Completed Time: {c[3]}")

    elif menu == " Chat":

        msgs = get_messages(user)

        for m in msgs:
            if m[1] == user:
                st.markdown(f" You: {m[3]}")
            else:
                st.markdown(f" {m[1]}: {m[3]}")

        msg = st.text_input("Message")

        if st.button("Send"):
            if msg:
                send_message(user, "admin", msg)
                st.success("Sent")
                st.rerun()
            else:
                st.warning("Enter message")

    elif menu == "AI":

        st.title("Smart Medical AI")

        q = st.text_area("Enter symptoms")

        if st.button("Analyze"):

            if not q:
                st.warning("Enter symptoms")
                st.stop()

            issue = get_issue_type(q)

            if issue != "general":

                level = get_emergency_level(q)
                spec = map_symptom_to_specialization(q)
                aid = get_first_aid(issue)

                st.error(" DATASET DETECTED")

                st.success(f"""
Condition: {issue}

Severity: {level}

Specialization: {spec}

First Aid:
{aid}
""")

            else:

                st.info(" Using Real AI Analysis")

                res = full_ai_analysis(q)
                clean = format_output(res)

                st.text_area(
                    "AI Result",
                    clean,
                    height=220
                )

    smart_refresh()
