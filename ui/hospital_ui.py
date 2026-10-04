import streamlit as st
import pandas as pd
import sqlite3
import json
import time
from datetime import datetime
from database import get_shared_history, get_users, get_doctor_extra

def get_hospital_details(username):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        SELECT name, hospital_id, city, address, phone, total_beds, available_beds, icu_beds, departments, available_doctors
        FROM users WHERE username=? AND role='hospital'
        """, (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "name": row[0] or username,
                "hospital_id": row[1] or "HOS-N/A",
                "city": row[2] or "N/A",
                "address": row[3] or "N/A",
                "phone": row[4] or "N/A",
                "total_beds": row[5] or 50,
                "available_beds": row[6] or 15,
                "icu_beds": row[7] or 5,
                "departments": row[8] or "Cardiology, Neurology, Orthopedic, General",
                "available_doctors": row[9] or ""
            }
    except Exception as e:
        print("Error getting hospital details:", e)
    return {
        "name": username,
        "hospital_id": "HOS-N/A",
        "city": "N/A",
        "address": "N/A",
        "phone": "N/A",
        "total_beds": 50,
        "available_beds": 15,
        "icu_beds": 5,
        "departments": "Cardiology, Neurology, Orthopedic, General",
        "available_doctors": ""
    }

def update_hospital_beds(username, avail_beds, avail_icu):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        UPDATE users
        SET available_beds=?, icu_beds=?
        WHERE username=?
        """, (avail_beds, avail_icu, username))
        
        # Sync with hospital_beds table
        h_details = get_hospital_details(username)
        h_name = h_details.get("name")
        c.execute("""
        UPDATE hospital_beds
        SET available_beds=?, available_icu=?
        WHERE hospital_name=?
        """, (avail_beds, avail_icu, h_name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating hospital beds:", e)
        return False

def show():
    st.markdown("<h2 style='text-align:center;'>🏥 Hospital Management System</h2>", unsafe_allow_html=True)
    
    # Get logged in hospital info
    h_username = st.session_state.user
    h_details = get_hospital_details(h_username)
    h_name = h_details.get("name")
    
    st.sidebar.markdown(f"### 🏢 {h_name}")
    st.sidebar.info(f"Hospital ID: {h_details.get('hospital_id')}\n\nCity: {h_details.get('city')}")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.subheader(f"Hospital Center: {h_name}")
    
    tabs = st.tabs(["📋 Incoming Referral Cases", "🛏️ Bed & Resource Management", "👨‍⚕️ Patient Management & Status", "📊 Analytics"])

    # Load referral cases for this hospital dynamically from hospital_requests table
    conn_h = sqlite3.connect("hospital.db")
    c_h = conn_h.cursor()
    c_h.execute("""
        SELECT referral_id, patient_name, symptoms, created_at, assigned_doctor, referral_status, transfer_status, patient_id, emergency_id, lat, lon 
        FROM hospital_requests 
        WHERE LOWER(hospital) = LOWER(?)
        ORDER BY id DESC
    """, (h_name,))
    h_rows = c_h.fetchall()
    conn_h.close()
    
    referrals = []
    for r in h_rows:
        ref_id, p_name, symptoms, created_at, doc_username, ref_status, trans_status, pat_id, emerg_id, lat, lon = r
        
        from database import load_patient_clinical_data
        p_details = load_patient_clinical_data(p_name)
        if not p_details:
            p_details = {}
            
        p_data = {
            "patient_name": p_details.get("name", p_name),
            "patient_id": pat_id,
            "age": p_details.get("age", 30),
            "gender": p_details.get("gender", "Male"),
            "blood_group": p_details.get("blood_group", "O+"),
            "allergies": p_details.get("allergies", "None"),
            "existing_diseases": p_details.get("chronic_diseases", "None"),
            "previous_diseases": p_details.get("previous_diseases", "None"),
            "previous_medications": p_details.get("previous_medications", "None"),
            "phone": p_details.get("phone", ""),
            "emergency_contact": p_details.get("emergency_contact", ""),
            "current_symptoms": symptoms,
            "specialization": "Emergency Medicine",
            "emergency_severity": "HIGH",
            "first_aid_recommendations": "Keep patient immobilized and calm."
        }
        
        referrals.append({
            "id": ref_id,
            "patient_username": p_name,
            "timestamp": created_at,
            "shared_data": json.dumps(p_data)
        })

    with tabs[0]:
        st.write("Review patient clinical records and assign doctors and beds on acceptance.")
        if not referrals:
            st.info("No incoming referral cases registered at this time.")
        else:
            for ref in referrals:
                ref_id = ref.get("id")
                patient_user = ref.get("patient_username")
                timestamp = ref.get("timestamp")
                data_json = ref.get("shared_data")
                
                try:
                    p_data = json.loads(data_json)
                except:
                    p_data = {}
                
                severity = p_data.get("emergency_severity", "Normal").upper()
                cond = p_data.get("predicted_disease", "General evaluation")
                
                # Render case card
                severity_color = "#d90429" if severity in ["CRITICAL", "HIGH"] else "#f1a30f" if severity == "MEDIUM" else "#2a9d8f"
                
                with st.expander(f"Case #{ref_id} - Patient: {p_data.get('patient_name', patient_user)} | Disease: {cond} | Severity: {severity}", expanded=False):
                    st.markdown(f"<span style='color:{severity_color};font-weight:bold;font-size:16px;'>🚨 Severity: {severity}</span>", unsafe_allow_html=True)
                    st.write(f"**Patient ID:** {p_data.get('patient_id', 'N/A')} | **Age / Gender:** {p_data.get('age', 30)} / {p_data.get('gender', 'Other')} | **Blood Group:** {p_data.get('blood_group', 'N/A')}")
                    st.write(f"**Contact Number:** {p_data.get('phone')} | **Emergency Phone:** {p_data.get('emergency_contact')}")
                    
                    st.divider()
                    st.markdown("##### 🤒 Reported Symptoms")
                    st.info(p_data.get("current_symptoms", "No symptoms described"))
                    
                    st.markdown("##### 💊 AI Safety & Clinical Recommendations")
                    st.write(f"**Suggested Specialist Department:** {p_data.get('specialization', 'General Physician')}")
                    st.write(f"**First Aid Recommendations:** {p_data.get('first_aid_recommendations', 'None')}")
                    
                    st.markdown("##### 📋 Historical Medical Profile")
                    st.write(f"**Known Allergies:** {p_data.get('allergies', 'None')}")
                    st.write(f"**Existing Chronic Illnesses:** {p_data.get('existing_diseases', 'None')}")
                    st.write(f"**Previous Diseases:** {p_data.get('previous_diseases', 'None')}")
                    st.write(f"**Previous Medications:** {p_data.get('previous_medications', 'None')}")
                    
                    st.divider()
                    st.markdown("##### 🛠️ Referral Allocation")
                    
                    # Accept Form
                    with st.form(key=f"allocation_form_{ref_id}"):
                        c_alloc1, c_alloc2 = st.columns(2)
                        with c_alloc1:
                            bed_type = st.selectbox("Allocate Bed Category", ["General Bed", "ICU Bed"], key=f"bed_type_{ref_id}")
                        with c_alloc2:
                            # Load doctors lists
                            doctors_list = [u[1] for u in get_users() if len(u) > 3 and u[3] == "doctor"]
                            assigned_doc = st.selectbox("Assign Specialty Doctor", doctors_list, key=f"doc_assign_{ref_id}")
                            
                        appt_time = st.text_input("Schedule Appointment Time (e.g. 2026-07-13 10:00)", value=datetime.now().strftime("%Y-%m-%d %H:%M"), key=f"appt_time_{ref_id}")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            accept_btn = st.form_submit_button("✅ Accept & Allocate")
                        with col_btn2:
                            reject_btn = st.form_submit_button("❌ Reject Referral")
                            
                        if accept_btn:
                            # 1. Update beds
                            cur_beds = h_details.get("available_beds")
                            cur_icu = h_details.get("icu_beds")
                            
                            if bed_type == "ICU Bed":
                                if cur_icu <= 0:
                                    st.error("Cannot accept case. ICU Bed capacity full.")
                                    st.stop()
                                cur_icu -= 1
                            else:
                                if cur_beds <= 0:
                                    st.error("Cannot accept case. General Bed capacity full.")
                                    st.stop()
                                cur_beds -= 1
                                
                            update_hospital_beds(h_username, cur_beds, cur_icu)
                            
                            # 2. Add appointment in appointments table
                            try:
                                conn = sqlite3.connect("hospital.db")
                                c = conn.cursor()
                                # create appointment
                                c.execute("""
                                INSERT INTO appointments (patient_name, doctor, date, time, notes)
                                VALUES (?, ?, ?, ?, ?)
                                """, (p_data.get('patient_name', patient_user), assigned_doc, appt_time[:10], appt_time[11:], f"Emergency Bed Allocated: {bed_type} at {h_name}"))
                                
                                # update patient status in patients table
                                c.execute("""
                                UPDATE patients
                                SET status='ASSIGNED', hospital=?, assigned_doctor=?
                                WHERE name=?
                                """, (h_name, assigned_doc, p_data.get('patient_name', patient_user)))
                                
                                # Add system notification
                                c.execute("""
                                INSERT INTO notifications (username, message, is_read, created_at)
                                VALUES (?, ?, 0, ?)
                                """, (patient_user, f"Your emergency referral is accepted by {h_name}. Allocated {bed_type}. Appointment: {appt_time}.", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                
                                conn.commit()
                                conn.close()
                                
                                st.success("✅ Case accepted, bed allocated and notifications sent!")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error executing database updates: {e}")
                                
                        if reject_btn:
                            try:
                                conn = sqlite3.connect("hospital.db")
                                c = conn.cursor()
                                c.execute("""
                                UPDATE patients
                                SET status='REJECTED'
                                WHERE name=?
                                """, (p_data.get('patient_name', patient_user),))
                                
                                c.execute("""
                                INSERT INTO notifications (username, message, is_read, created_at)
                                VALUES (?, ?, 0, ?)
                                """, (patient_user, f"Your referral to {h_name} was rejected. Re-routing recommended.", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                conn.commit()
                                conn.close()
                                
                                st.warning("❌ Referral case rejected.")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error rejecting case: {e}")

    with tabs[1]:
        st.subheader("Resource Controls")
        
        # Interactive bed availability controllers
        st.write("Manually update available bed capacity in real-time.")
        
        with st.form("bed_management_form"):
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                new_avail_beds = st.number_input("Available General Beds", min_value=0, max_value=h_details.get("total_beds"), value=h_details.get("available_beds"))
            with col_b2:
                new_avail_icu = st.number_input("Available ICU Beds", min_value=0, max_value=20, value=h_details.get("icu_beds"))
                
            save_beds_btn = st.form_submit_button("💾 Save Bed Counts")
            if save_beds_btn:
                if update_hospital_beds(h_username, new_avail_beds, new_avail_icu):
                    st.success("✅ Bed availability updated successfully!")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Failed to update bed counts.")
                    
        # Capacity details display
        st.write("---")
        st.markdown("##### 📊 Live Facility Capacity Dashboard")
        cb1, cb2 = st.columns(2)
        cb1.metric("General Beds Availability", f"{h_details.get('available_beds')} / {h_details.get('total_beds')}")
        cb2.metric("ICU Beds Availability", f"{h_details.get('icu_beds')} Available")

    with tabs[2]:
        st.subheader("Manage Assigned Patient Cases")
        
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        SELECT id, name, symptoms, status, assigned_doctor, date, time
        FROM patients
        WHERE hospital=?
        ORDER BY id DESC
        """, (h_name,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            st.info("No patients currently assigned to your facility.")
        else:
            df_patients = pd.DataFrame(rows, columns=["Case ID", "Patient Name", "Symptoms", "Status", "Assigned Doctor", "Admission Date", "Admission Time"])
            st.dataframe(df_patients, width="stretch")
            
            st.write("---")
            st.markdown("##### 🛠️ Patient Status Actions")
            
            selected_pat_id = st.selectbox("Select Patient Case ID", df_patients["Case ID"])
            pat_row = df_patients[df_patients["Case ID"] == selected_pat_id].iloc[0]
            pat_name = pat_row["Patient Name"]
            
            status_options = ["ASSIGNED", "IN_PROGRESS", "COMPLETED", "DISCHARGED"]
            curr_index = status_options.index(pat_row["Status"]) if pat_row["Status"] in status_options else 0
            
            new_status = st.selectbox("Set New Status", status_options, index=curr_index)
            status_update_btn = st.button("Update Status")
            
            if status_update_btn:
                try:
                    conn = sqlite3.connect("hospital.db")
                    c = conn.cursor()
                    c.execute("UPDATE patients SET status=? WHERE id=?", (new_status, selected_pat_id))
                    
                    # If discharged, return a bed to capacity
                    if new_status == "DISCHARGED" and pat_row["Status"] != "DISCHARGED":
                        cur_beds = h_details.get("available_beds") + 1
                        update_hospital_beds(h_username, cur_beds, h_details.get("icu_beds"))
                        st.toast(f"🛏️ Bed capacity incremented on Patient {pat_name} discharge.")
                        
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Status updated successfully to: {new_status}")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating status: {e}")

    with tabs[3]:
        st.subheader("Hospital Insights & Referral Trends")
        
        total_p = len(rows)
        active_p = len([r for r in rows if r[3] in ["ASSIGNED", "IN_PROGRESS"]])
        discharged_p = len([r for r in rows if r[3] in ["DISCHARGED", "COMPLETED"]])
        
        c_an1, c_an2, c_an3 = st.columns(3)
        c_an1.metric("Total Referrals Accepted", total_p)
        c_an2.metric("Active Cases Admitted", active_p)
        c_an3.metric("Discharged Patients", discharged_p)
        
        st.divider()
        st.markdown("##### 📈 Specialist Cases Profile Chart")
        
        # Plot simple distribution
        departments = h_details.get("departments").split(",")
        counts = {}
        for dep in departments:
            dep_name = dep.strip()
            counts[dep_name] = 0
            
        for r in rows:
            symptom_text = r[2]
            from utils import map_symptom_to_specialization
            spec = map_symptom_to_specialization(symptom_text)
            if spec in counts:
                counts[spec] += 1
            else:
                counts["General"] = counts.get("General", 0) + 1
                
        df_chart = pd.DataFrame(list(counts.items()), columns=["Specialization", "Active Cases"])
        st.bar_chart(df_chart.set_index("Specialization"))
