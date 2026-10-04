import json
import re
import requests
import math
import time


# ==============================
# 🧠 SYMPTOM → SPECIALIZATION
# ==============================
def map_symptom_to_specialization(symptoms):

    if not symptoms:
        return "General Physician"

    s = str(symptoms).lower()

    # ❤️ CARDIOLOGY
    if (
        "chest" in s
        or "heart" in s
        or "bp" in s
        or "cardiac" in s
        or "heart attack" in s
    ):
        return "Cardiologist"

    # 🧠 NEUROLOGY
    elif (
        "head" in s
        or "brain" in s
        or "migraine" in s
        or "headache" in s
        or "headhech" in s
        or "stroke" in s
        or "seizure" in s
    ):
        return "Neurologist"

    # 🦴 ORTHOPEDIC
    elif (
        "bone" in s
        or "joint" in s
        or "fracture" in s
        or "leg pain" in s
        or "back pain" in s
    ):
        return "Orthopedic"

    # 🧴 DERMATOLOGY
    elif (
        "skin" in s
        or "rash" in s
        or "itch" in s
        or "allergy" in s
    ):
        return "Dermatologist"

    # 👁️ OPHTHALMOLOGY
    elif (
        "eye" in s
        or "vision" in s
        or "blur" in s
    ):
        return "Ophthalmologist"

    # 👂 ENT
    elif (
        "ear" in s
        or "nose" in s
        or "throat" in s
        or "sinus" in s
    ):
        return "ENT Specialist"

    # 🦷 DENTIST
    elif (
        "tooth" in s
        or "teeth" in s
        or "gum" in s
    ):
        return "Dentist"

    # 👶 PEDIATRIC
    elif (
        "child" in s
        or "baby" in s
        or "kids" in s
    ):
        return "Pediatrician"

    # 🤰 GYNECOLOGY
    elif (
        "pregnancy" in s
        or "women" in s
        or "period" in s
    ):
        return "Gynecologist"

    # 🫁 PULMONOLOGY
    elif (
        "breathing" in s
        or "lungs" in s
        or "asthma" in s
        or "shortness of breath" in s
        or "cough" in s
    ):
        return "Pulmonologist"

    # 🧪 NEPHROLOGY
    elif (
        "kidney" in s
        or "urine" in s
    ):
        return "Nephrologist"

    # 🍬 DIABETOLOGY
    elif (
        "diabetes" in s
        or "sugar" in s
    ):
        return "Diabetologist"

    # 🧬 ONCOLOGY
    elif (
        "cancer" in s
        or "tumor" in s
    ):
        return "Oncologist"

    # 🍽️ GASTRO
    elif (
        "stomach" in s
        or "vomiting" in s
        or "gastric" in s
        or "ulcer" in s
    ):
        return "Gastroenterologist"

    # 🧠 PSYCHIATRY
    elif (
        "mental" in s
        or "depression" in s
        or "stress" in s
        or "anxiety" in s
    ):
        return "Psychiatrist"

    # 🚑 EMERGENCY
    elif (
        "accident" in s
        or "bleeding" in s
        or "critical" in s
        or "emergency" in s
    ):
        return "Emergency Medicine"

    # 🤒 GENERAL
    elif (
        "fever" in s
        or "cold" in s
        or "viral" in s
    ):
        return "General Physician"

    return "General Physician"


# ==============================
# 🚨 STATUS DETECTION
# ==============================
def detect_status(text):

    if not text:
        return "NORMAL"

    t = str(text).lower()

    if (
        "emergency" in t
        or "critical" in t
        or "chest pain" in t
        or "breathing" in t
        or "high" in t
        or "stroke" in t
        or "accident" in t
    ):
        return "EMERGENCY"

    elif "severe" in t:
        return "HIGH"

    elif "mild" in t or "low" in t:
        return "LOW"

    return "NORMAL"


# ==============================
# 📝 FORMAT OUTPUT
# ==============================
def format_output(text):

    if not text:
        return "No result"

    if isinstance(text, dict):

        return f"""
Condition: {text.get('condition', 'Unknown')}

Severity: {text.get('severity', 'medium')}

Specialization: {text.get('specialization', 'General Physician')}

Medicine: {text.get('medicine', 'Paracetamol')}

Advice: {text.get('advice', 'Drink more water')}
""".strip()

    raw = str(text).strip()

    try:

        match = re.search(
            r"\{.*\}",
            raw,
            re.DOTALL
        )

        if match:

            raw_json = match.group(0)

            data = json.loads(raw_json)

            return f"""
Condition: {data.get('condition', 'Unknown')}

Severity: {data.get('severity', 'medium')}

Specialization: {data.get('specialization', 'General Physician')}

Medicine: {data.get('medicine', 'Paracetamol')}

Advice: {data.get('advice', 'Drink more water')}
""".strip()

    except:
        pass

    return raw.strip()


# ==============================
# 📍 LOCATION
# ==============================
def get_location():
    return "Chennai"


# ==============================
# 🌍 LIVE LOCATION
# ==============================
def get_live_location():

    try:

        res = requests.get(
            "https://ipinfo.io/json",
            timeout=5
        ).json()

        loc = res.get("loc")

        if loc:

            lat, lon = map(
                float,
                loc.split(",")
            )

            return lat, lon

    except Exception as e:
        print("Location Error:", e)

    return 13.0827, 80.2707


# ==============================
# 📏 DISTANCE
# ==============================
def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return round(R * c, 2)


# ==============================
# ⭐ SMART HOSPITAL SELECT
# ==============================
def select_best_hospital(hospitals):

    best = None
    score = -999

    for h in hospitals:

        rating = h.get("rating", 3)
        dist = h.get("distance", 10)

        score_now = (rating * 2) - dist

        if score_now > score:
            score = score_now
            best = h

    return best


# ==============================
# 🗺️ MAP EMBED
# ==============================
def get_map_embed(lat, lon):

    return f"""
    <iframe
        width="100%"
        height="300"
        style="border:0"
        loading="lazy"
        allowfullscreen
        src="https://www.google.com/maps?q={lat},{lon}&z=15&output=embed">
    </iframe>
    """


# ==============================
# 💬 HOSPITAL CHAT
# ==============================
def hospital_chat_response(msg):

    if not msg:
        return "Please enter message"

    msg = msg.lower()

    if "bed" in msg:
        return "Beds available. Please come quickly."

    elif "doctor" in msg:
        return "Doctor available in 10 minutes."

    elif "emergency" in msg:
        return "Emergency team ready."

    elif "time" in msg:
        return "Hospital is open 24/7."

    return "Hospital support will respond soon."


# ==============================
# 🚑 AMBULANCE TRACK
# ==============================
def simulate_ambulance():

    steps = [
        "🚑 Dispatched",
        "🚑 On the way",
        "🚑 2 KM away",
        "🚑 Arrived"
    ]

    for step in steps:
        yield step
        time.sleep(1)


def generate_emergency_qr_card(username):
    try:
        import qrcode
        import io
        import json
        from database import load_patient_clinical_data
        
        data = load_patient_clinical_data(username)
        if not data:
            return None
            
        qr_payload = {
            "patient_id": data.get("patient_id", "N/A"),
            "name": data.get("name", username),
            "blood_group": data.get("blood_group", "N/A"),
            "allergies": data.get("allergies", "None"),
            "existing_diseases": data.get("chronic_diseases", "None"),
            "emergency_contact": data.get("emergency_contact", "N/A"),
            "medical_reference_id": f"REF-{data.get('patient_id', 'PAT-0000')[-4:] if data.get('patient_id') else '0000'}"
        }
        
        qr_text = json.dumps(qr_payload)
        qr = qrcode.QRCode(version=1, box_size=10, border=3)
        qr.add_data(qr_text)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print("Error generating QR:", e)
        return None


def generate_pdf_report(patient_username, symptoms, result_data, risk_score, report_type="Referral"):
    try:
        from fpdf import FPDF
        from datetime import datetime
        import json
        import os
        import sqlite3
        from database import load_patient_clinical_data
        
        # Load detailed clinical profile
        p_details = load_patient_clinical_data(patient_username)
        if not p_details:
            p_details = {
                "name": patient_username,
                "age": "Not Available",
                "gender": "Not Available",
                "blood_group": "Not Available",
                "allergies": "Not Available",
                "chronic_diseases": "Not Available",
                "previous_diseases": "Not Available",
                "previous_medications": "Not Available",
                "previous_reports": "Not Available",
                "emergency_contact": "Not Available",
                "patient_id": "Not Available",
                "phone": "Not Available"
            }
            
        # Retrieve extra location fields
        address_val = "Not Available"
        city_val = "Not Available"
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT address, city FROM users WHERE username=?", (patient_username,))
            row_u = c.fetchone()
            if row_u:
                address_val = row_u[0] or "Not Available"
                city_val = row_u[1] or "Not Available"
            conn.close()
        except Exception as e:
            print("PDF address/city retrieve error:", e)

        # Retrieve Medical History (history table)
        history_events = []
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT symptoms, result, date, time FROM history WHERE name=? ORDER BY date ASC, time ASC", (patient_username,))
            history_events = c.fetchall()
            conn.close()
        except Exception as e:
            print("PDF history retrieve error:", e)

        # Retrieve Emergency History (hospital_requests table)
        emergency_events = []
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT id, hospital, status, symptoms, result, lat, lon, created_at FROM hospital_requests WHERE patient_name=? ORDER BY created_at ASC", (patient_username,))
            emergency_events = c.fetchall()
            conn.close()
        except Exception as e:
            print("PDF emergency retrieve error:", e)

        # Retrieve Shared History logs (shared_history table)
        shared_history_logs = []
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT hospital_name, doctor_username, shared_data, timestamp FROM shared_history WHERE patient_username=? ORDER BY timestamp ASC", (patient_username,))
            shared_history_logs = c.fetchall()
            conn.close()
        except Exception as e:
            print("PDF shared history retrieve error:", e)

        # Build patient timeline list
        timeline = []
        for h in history_events:
            t_str = f"{h[2]} {h[3]}"
            timeline.append({
                "datetime_obj": t_str,
                "type": "Consultation",
                "details": f"Symptoms: {h[0]} | Diagnosis & Advice: {h[1]}"
            })
        for em in emergency_events:
            timeline.append({
                "datetime_obj": em[7] or "N/A",
                "type": "Emergency Referral",
                "details": f"Hospital: {em[1]} | Symptoms: {em[3]} | Outcome/Status: {em[2]}"
            })
        
        # Sort timeline chronologically
        try:
            timeline.sort(key=lambda x: x["datetime_obj"])
        except Exception as e:
            print("Timeline sorting error:", e)

        # Define custom PDF subclass to ensure Patient ID on every page and confidential footer
        pat_id_str = str(p_details.get('patient_id', 'Not Available'))
        class MedicalPDF(FPDF):
            def __init__(self, patient_id):
                super().__init__()
                self.patient_id = patient_id
                
            def header(self):
                if self.page_no() > 1:
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(150, 150, 150)
                    self.cell(0, 5, f"Patient Medical History & Referral Report | Patient ID: {self.patient_id}", ln=True, align='R')
                    self.ln(2)
                    
            def footer(self):
                self.set_y(-15)
                self.set_font('Helvetica', 'I', 8)
                self.set_text_color(180, 50, 50)
                self.cell(0, 5, "CONFIDENTIAL - MEDICAL RECORD ONLY FOR RECEIVING HOSPITAL & ASSIGNED DOCTOR", ln=False, align='C')
                self.set_text_color(150, 150, 150)
                self.cell(0, 5, f"Page {self.page_no()}", ln=True, align='R')

        pdf = MedicalPDF(pat_id_str)
        pdf.add_page()
        
        # 1. Main Title
        pdf.set_text_color(15, 31, 77) # deep blue
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, "PRASAD MEDICAL PORTAL", ln=True, align='C')
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 6, "COMPLETE MEDICAL HISTORY & REFERRAL REPORT", ln=True, align='C')
        pdf.set_draw_color(15, 98, 254) # bright blue
        pdf.line(10, 28, 200, 28)
        pdf.ln(8)
        
        # Metadata
        pdf.set_font("Helvetica", '', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(3)
        
        # 2. Section 1: Patient Demographics & Profile
        pdf.set_text_color(15, 31, 77)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_fill_color(238, 245, 255)
        pdf.cell(0, 7, "1. PATIENT DEMOGRAPHICS & PROFILE", ln=True, fill=True)
        pdf.set_font("Helvetica", '', 9)
        pdf.set_text_color(0, 0, 0)
        
        # Demographic grid
        pdf.cell(95, 6, f"Patient Name: {p_details.get('name', 'Not Available')}", border=1)
        pdf.cell(95, 6, f"Patient ID: {pat_id_str}", border=1, ln=True)
        pdf.cell(95, 6, f"Age / Gender: {p_details.get('age', 'Not Available')} / {p_details.get('gender', 'Not Available')}", border=1)
        pdf.cell(95, 6, f"Blood Group: {p_details.get('blood_group', 'Not Available')}", border=1, ln=True)
        pdf.cell(95, 6, f"Contact Number: {p_details.get('phone', 'Not Available')}", border=1)
        pdf.cell(95, 6, f"Emergency Contact: {p_details.get('emergency_contact', 'Not Available')}", border=1, ln=True)
        pdf.cell(95, 6, f"City: {city_val}", border=1)
        pdf.cell(95, 6, f"Address: {address_val}", border=1, ln=True)
        pdf.ln(4)
        
        # 3. Section 2: Complete Clinical Profile
        pdf.set_text_color(15, 31, 77)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 7, "2. CLINICAL PROFILE", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("Helvetica", 'B', 9)
        pdf.write(5, "Known Allergies: ")
        pdf.set_font("Helvetica", '', 9)
        pdf.write(5, str(p_details.get('allergies', 'Not Available')) + "\n")
        pdf.ln(1)
        
        pdf.set_font("Helvetica", 'B', 9)
        pdf.write(5, "Chronic Conditions: ")
        pdf.set_font("Helvetica", '', 9)
        pdf.write(5, str(p_details.get('chronic_diseases', 'Not Available')) + "\n")
        pdf.ln(1)

        pdf.set_font("Helvetica", 'B', 9)
        pdf.write(5, "Current Medications: ")
        pdf.set_font("Helvetica", '', 9)
        pdf.write(5, str(p_details.get('previous_medications', 'Not Available')) + "\n")
        pdf.ln(1)
        
        pdf.set_font("Helvetica", 'B', 9)
        pdf.write(5, "Previous Diagnoses: ")
        pdf.set_font("Helvetica", '', 9)
        pdf.write(5, str(p_details.get('previous_diseases', 'Not Available')) + "\n")
        pdf.ln(4)
        
        # 4. Section 3: Complete Medical History
        pdf.set_text_color(15, 31, 77)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 7, "3. COMPLETE MEDICAL CONSULTATION HISTORY", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        if history_events:
            for h in history_events:
                pdf.set_fill_color(245, 248, 255)
                pdf.set_font("Helvetica", 'B', 9)
                pdf.cell(0, 6, f"Visit Date: {h[2]} at {h[3]}", border=1, ln=True, fill=True)
                pdf.set_font("Helvetica", 'B', 8.5)
                pdf.write(5, "  Symptoms: ")
                pdf.set_font("Helvetica", '', 8.5)
                pdf.write(5, str(h[0]) + "\n")
                pdf.set_font("Helvetica", 'B', 8.5)
                pdf.write(5, "  Diagnosis & Advice: ")
                pdf.set_font("Helvetica", '', 8.5)
                pdf.write(5, str(h[1]) + "\n")
                pdf.ln(3)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", 'I', 9)
            pdf.cell(0, 5, "No previous medical consultation records available.", ln=True)
            pdf.ln(4)

        # 5. Section 4: All Medical Reports
        pdf.set_text_color(15, 31, 77)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 7, "4. MEDICAL DIAGNOSTIC REPORTS & SHARED DOCUMENTS", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        has_reports = False
        prev_rep_str = str(p_details.get('previous_reports', '')).strip()
        if prev_rep_str and prev_rep_str.lower() != "none" and prev_rep_str.lower() != "not assigned":
            pdf.set_font("Helvetica", 'B', 9)
            pdf.cell(0, 5, "Patient Uploaded Reports Summary:", ln=True)
            pdf.set_font("Helvetica", '', 9)
            pdf.multi_cell(0, 5, prev_rep_str)
            pdf.ln(2)
            has_reports = True
            
        if shared_history_logs:
            pdf.set_font("Helvetica", 'B', 9)
            pdf.set_fill_color(225, 235, 255)
            pdf.cell(35, 6, "Shared At", border=1, fill=True)
            pdf.cell(50, 6, "Hospital Name", border=1, fill=True)
            pdf.cell(35, 6, "Assigned Doctor", border=1, fill=True)
            pdf.cell(70, 6, "Report Details / Payload Summary", border=1, fill=True, ln=True)
            
            pdf.set_font("Helvetica", '', 8)
            for sh in shared_history_logs:
                # Try parsing shared_data JSON
                try:
                    payload = json.loads(sh[2])
                    details = f"Diag: {payload.get('predicted_disease', 'N/A')} | Risk: {payload.get('risk_score', 'N/A')}"
                except:
                    details = str(sh[2])[:60]
                
                pdf.cell(35, 6, str(sh[3]), border=1)
                pdf.cell(50, 6, str(sh[0])[:25], border=1)
                pdf.cell(35, 6, str(sh[1])[:20], border=1)
                pdf.cell(70, 6, details, border=1, ln=True)
            pdf.ln(4)
            has_reports = True
            
        if not has_reports:
            pdf.set_font("Helvetica", 'I', 9)
            pdf.cell(0, 5, "No diagnostic reports or shared documents available.", ln=True)
            pdf.ln(4)

        # 6. Section 5: Complete Emergency Referral History
        pdf.set_text_color(15, 31, 77)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 7, "5. EMERGENCY REFERRAL HISTORY", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        if emergency_events:
            pdf.set_font("Helvetica", 'B', 9)
            pdf.set_fill_color(225, 235, 255)
            pdf.cell(35, 6, "Date & Time", border=1, fill=True)
            pdf.cell(60, 6, "Selected Hospital", border=1, fill=True)
            pdf.cell(55, 6, "Reported Symptoms", border=1, fill=True)
            pdf.cell(40, 6, "Final Status", border=1, fill=True, ln=True)
            
            pdf.set_font("Helvetica", '', 8.5)
            for em in emergency_events:
                pdf.cell(35, 6, str(em[7]), border=1)
                pdf.cell(60, 6, str(em[1])[:30], border=1)
                pdf.cell(55, 6, str(em[3])[:25], border=1)
                pdf.cell(40, 6, str(em[2]), border=1, ln=True)
            pdf.ln(4)
        else:
            pdf.set_font("Helvetica", 'I', 9)
            pdf.cell(0, 5, "No previous emergency referral history.", ln=True)
            pdf.ln(4)

        # 7. Section 6: Current Emergency / Referral / Consultation
        if report_type == "Clinical":
            pdf.set_text_color(15, 31, 77)
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 7, "6. CLINICAL MEDICAL REPORT & CONSULTATION DETAILS", ln=True, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", '', 9)
        else:
            pdf.set_text_color(180, 50, 50) # red alert color
            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(0, 7, "6. CURRENT ACTIVE EMERGENCY / REFERRAL DETAILS", ln=True, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", '', 9)
        
        cond_str = "Undiagnosed"
        risk_str = f"{risk_score}%"
        first_aid_str = "Take rest immediately."
        hosp_str = "Not Assigned"
        doc_str = "Not Assigned"
        
        if isinstance(result_data, dict):
            cond_str = result_data.get("condition", cond_str)
            risk_str = result_data.get("risk_score", risk_str)
            first_aid_str = result_data.get("first_aid", first_aid_str)
            hosp_str = result_data.get("hospitals", hosp_str)
            doc_str = result_data.get("doctors", doc_str)
        else:
            # Parse from plain string
            for line in str(result_data).split("\n"):
                if "Condition:" in line or "Diagnosis:" in line:
                    cond_str = line.split(":")[-1].strip()
                elif "Hospital:" in line:
                    hosp_str = line.split(":")[-1].strip()
                elif "Doctor:" in line or "Medicine:" in line:
                    doc_str = line.split(":")[-1].strip()

        pdf.cell(95, 6, f"Referral From: Prasad Hospital", border=1)
        pdf.cell(95, 6, f"Referral To: {hosp_str}", border=1, ln=True)
        pdf.cell(95, 6, f"Current Symptom: {symptoms[:40]}", border=1)
        pdf.cell(95, 6, f"AI Predicted Condition: {cond_str}", border=1, ln=True)
        pdf.cell(95, 6, f"Risk Level: {risk_str}", border=1)
        pdf.cell(95, 6, f"Assigned Doctor: {doc_str}", border=1, ln=True)
        pdf.cell(95, 6, f"Current Location: Lat: {p_details.get('latitude', '17.3850')}, Lon: {p_details.get('longitude', '78.4867')}", border=1)
        
        if report_type != "Clinical":
            # Query referral and emergency IDs from database
            import sqlite3
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT emergency_id, referral_id, ambulance_status, ambulance_vehicle FROM hospital_requests WHERE patient_name=? ORDER BY id DESC LIMIT 1", (patient_username,))
            ref_meta = c.fetchone()
            conn.close()
            
            ref_id_str = "Not Available"
            emerg_id_str = "Not Available"
            amb_status_str = "Not Available"
            
            if ref_meta:
                emerg_id_str = ref_meta[0] or "Not Available"
                ref_id_str = ref_meta[1] or "Not Available"
                amb_status_str = f"{ref_meta[2]} ({ref_meta[3]})" if ref_meta[2] else "Not Available"
                
            pdf.cell(95, 6, f"Referral ID: {ref_id_str}", border=1, ln=True)
            pdf.cell(95, 6, f"Emergency ID: {emerg_id_str}", border=1)
            pdf.cell(95, 6, f"Ambulance Details: {amb_status_str}", border=1, ln=True)
            pdf.ln(2)
            
            pdf.set_font("Helvetica", 'B', 9)
            pdf.cell(0, 5, "Emergency First Aid Protocol:", ln=True)
            pdf.set_font("Helvetica", '', 9)
            pdf.multi_cell(0, 5, first_aid_str)
            pdf.ln(4)

        # 8. Section 7: Complete Patient Timeline (Chronological)
        pdf.set_text_color(15, 31, 77)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 7, "7. COMPLETE CHRONOLOGICAL MEDICAL TIMELINE", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        
        if timeline:
            for event in timeline:
                event_time = event["datetime_obj"]
                event_type = event["type"]
                event_details = event["details"]
                
                pdf.set_font("Helvetica", 'B', 8.5)
                pdf.write(5, f"[{event_time}] ")
                pdf.set_text_color(15, 98, 254)
                pdf.write(5, f"({event_type}): ")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", '', 8.5)
                pdf.write(5, f"{event_details}\n")
                pdf.ln(2)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", 'I', 9)
            pdf.cell(0, 5, "No timeline events recorded.", ln=True)
            pdf.ln(4)

        # Append QR Code Card
        qr_bytes = generate_emergency_qr_card(patient_username)
        if qr_bytes:
            temp_qr_path = f"temp_qr_{patient_username}.png"
            with open(temp_qr_path, "wb") as f_qr:
                f_qr.write(qr_bytes)
                
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 6, "EMERGENCY QUICK-ACCESS QR CARD", ln=True)
            pdf.image(temp_qr_path, x=150, y=pdf.get_y(), w=32, h=32)
            pdf.ln(32)
            
            try:
                os.remove(temp_qr_path)
            except:
                pass
                
        pdf.ln(2)
        pdf.set_font("Helvetica", 'I', 7.5)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 4, "Disclaimer: This is a compiled medical history report generated by the Prasad Medical Portal. All diagnostic history and emergency referral details have been fetched from the database using the unique Patient ID. It is meant only for immediate reference by the clinical staff.")
        
        pdf_bytes = pdf.output()
        if isinstance(pdf_bytes, bytearray):
            pdf_bytes = bytes(pdf_bytes)
        return pdf_bytes
    except Exception as e:
        print("PDF Gen Error:", e)
        from datetime import datetime
        report = f"PRASAD CLINICAL PORTAL REPORT\n\nGenerated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nPatient Name: {patient_username}\n\nSymptoms:\n{symptoms}\n\nEvaluation:\n{str(result_data)}"
        return report.encode('utf-8')


def generate_referral_pdf(
    patient_username,
    symptoms,
    specialization,
    severity,
    from_hospital,
    to_hospital,
    doctor_name,
    doctor_specialization,
    doctor_qualification,
    doctor_experience,
    referral_id,
    emergency_id,
    risk_score,
    first_aid_text="Keep the patient calm and comfortable.",
    additional_notes=""
):
    """
    Generate a complete, standalone Referral Letter PDF.
    Includes:
      - Patient demographics & full clinical profile
      - Referring hospital → Referred hospital (explicit)
      - Assigned doctor details
      - Current health issue & symptoms
      - Complete medical history (consultations + emergencies)
      - Referral ID, Emergency ID, date/time stamp
    """
    try:
        from fpdf import FPDF
        from datetime import datetime
        import json, os, sqlite3
        from database import load_patient_clinical_data

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now_date = datetime.now().strftime("%d %B %Y")

        # ── Load patient profile ──────────────────────────────────────────────
        p = load_patient_clinical_data(patient_username) or {}
        pat_name   = p.get("name", patient_username)
        pat_id     = p.get("patient_id", "N/A")
        pat_age    = p.get("age", "N/A")
        pat_gender = p.get("gender", "N/A")
        pat_blood  = p.get("blood_group", "N/A")
        pat_phone  = p.get("phone", "N/A")
        pat_emrcon = p.get("emergency_contact", "N/A")
        pat_allerg = p.get("allergies", "None")
        pat_chron  = p.get("chronic_diseases", "None")
        pat_prev_d = p.get("previous_diseases", "None")
        pat_prev_m = p.get("previous_medications", "None")
        pat_prev_r = p.get("previous_reports", "None")

        # ── Load address / city ───────────────────────────────────────────────
        address_val = "N/A"
        city_val    = "N/A"
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT address, city FROM users WHERE username=?", (patient_username,))
            row = c.fetchone()
            if row:
                address_val = row[0] or "N/A"
                city_val    = row[1] or "N/A"
            conn.close()
        except: pass

        # ── Load consultation history ─────────────────────────────────────────
        history_rows = []
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("SELECT symptoms, result, date, time FROM history WHERE name=? ORDER BY id DESC LIMIT 15", (patient_username,))
            history_rows = c.fetchall()
            conn.close()
        except: pass

        # ── Load past emergency referrals ────────────────────────────────────
        past_referrals = []
        try:
            conn = sqlite3.connect("hospital.db")
            c = conn.cursor()
            c.execute("""SELECT hospital, status, symptoms, created_at, referral_id
                         FROM hospital_requests WHERE patient_name=?
                         ORDER BY id DESC LIMIT 10""", (patient_username,))
            past_referrals = c.fetchall()
            conn.close()
        except: pass

        # ──────────────────────────────────────────────────────────────────────
        # PDF Layout
        # ──────────────────────────────────────────────────────────────────────
        DEEP_BLUE  = (15, 31, 77)
        ACCENT     = (15, 98, 254)
        RED_ALERT  = (180, 40, 40)
        GREEN_OK   = (39, 174, 96)
        LIGHT_BLUE = (238, 245, 255)
        LIGHT_GREEN= (240, 255, 244)
        WHITE      = (255, 255, 255)
        GRAY_TEXT  = (110, 110, 110)

        class ReferralPDF(FPDF):
            def header(self):
                if self.page_no() > 1:
                    self.set_font("Helvetica", "I", 7.5)
                    self.set_text_color(*GRAY_TEXT)
                    self.cell(0, 5,
                        f"REFERRAL LETTER  |  {from_hospital} → {to_hospital}  |  Ref ID: {referral_id}  |  Patient: {pat_name}",
                        ln=True, align="R")
                    self.ln(1)
            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 7)
                self.set_text_color(*RED_ALERT)
                self.cell(0, 5, "CONFIDENTIAL — FOR RECEIVING HOSPITAL & ASSIGNED DOCTOR ONLY", align="C")
                self.set_text_color(*GRAY_TEXT)
                self.ln(4)
                self.cell(0, 4, f"Page {self.page_no()}  |  Prasad Medical Portal  |  {now_str}", align="C")

        pdf = ReferralPDF()
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 0 — LETTERHEAD
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_text_color(*DEEP_BLUE)
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "PRASAD MEDICAL PORTAL", ln=True, align="C")
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 7, "OFFICIAL PATIENT REFERRAL LETTER", ln=True, align="C")
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.7)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # Date + Referral ID strip
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DEEP_BLUE)
        pdf.cell(0, 7,
            f"   Date: {now_date}     Referral ID: {referral_id}     Emergency ID: {emergency_id}     Risk Score: {risk_score}%",
            ln=True, fill=True, border=0)
        pdf.ln(3)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 1 — REFERRAL ROUTE (FROM → TO)
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*RED_ALERT)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  REFERRAL ROUTE", ln=True, fill=True)
        pdf.ln(1)

        # Two-column FROM → TO layout
        col_w = 88
        arrow_w = 14

        # FROM box
        pdf.set_fill_color(255, 240, 240)
        pdf.set_text_color(*RED_ALERT)
        pdf.set_font("Helvetica", "B", 10)
        x_from = pdf.get_x()
        y_row  = pdf.get_y()
        pdf.set_xy(x_from, y_row)
        pdf.multi_cell(col_w, 6,
            f"REFERRING HOSPITAL\n{from_hospital}\n(Prasad Medical Portal)",
            border=1, fill=True, align="C")
        h_from = pdf.get_y() - y_row

        # Arrow
        pdf.set_xy(x_from + col_w, y_row + h_from / 2 - 3)
        pdf.set_text_color(*DEEP_BLUE)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(arrow_w, 6, "→", align="C")

        # TO box
        pdf.set_xy(x_from + col_w + arrow_w, y_row)
        pdf.set_fill_color(*LIGHT_GREEN)
        pdf.set_text_color(*GREEN_OK)
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(col_w, 6,
            f"RECEIVING HOSPITAL\n{to_hospital}",
            border=1, fill=True, align="C")

        pdf.set_xy(10, y_row + h_from + 2)
        pdf.ln(2)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 2 — PATIENT DEMOGRAPHICS
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_text_color(*DEEP_BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  1. PATIENT DEMOGRAPHICS", ln=True, fill=True)
        pdf.ln(1)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 6, f"Full Name: {pat_name}", border=1)
        pdf.cell(95, 6, f"Patient ID: {pat_id}", border=1, ln=True)
        pdf.cell(95, 6, f"Age / Gender: {pat_age} / {pat_gender}", border=1)
        pdf.cell(95, 6, f"Blood Group: {pat_blood}", border=1, ln=True)
        pdf.cell(95, 6, f"Contact: {pat_phone}", border=1)
        pdf.cell(95, 6, f"Emergency Contact: {pat_emrcon}", border=1, ln=True)
        pdf.cell(95, 6, f"City: {city_val}", border=1)
        pdf.cell(95, 6, f"Address: {str(address_val)[:40]}", border=1, ln=True)
        pdf.ln(3)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 3 — CURRENT HEALTH ISSUE
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*RED_ALERT)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  2. CURRENT HEALTH ISSUE (REASON FOR REFERRAL)", ln=True, fill=True)
        pdf.ln(1)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        sev_color = RED_ALERT if severity.upper() in ["HIGH","CRITICAL"] else ((200,120,0) if severity.upper()=="MEDIUM" else GREEN_OK)
        pdf.cell(95, 6, f"Presenting Symptoms: {str(symptoms)[:50]}", border=1)
        pdf.set_text_color(*sev_color)
        pdf.cell(95, 6, f"Severity Level: {severity.upper()}", border=1, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 6, f"Required Specialization: {specialization}", border=1)
        pdf.cell(95, 6, f"Risk Score: {risk_score}%", border=1, ln=True)
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, "Full Symptom Description:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, str(symptoms))
        if first_aid_text:
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, "Immediate First Aid / Instructions Given:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, str(first_aid_text)[:400])
        pdf.ln(3)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 4 — ASSIGNED DOCTOR
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*LIGHT_GREEN)
        pdf.set_text_color(*GREEN_OK)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  3. ASSIGNED DOCTOR AT RECEIVING HOSPITAL", ln=True, fill=True)
        pdf.ln(1)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(95, 6, f"Doctor Name: {doctor_name}", border=1)
        pdf.cell(95, 6, f"Specialization: {doctor_specialization}", border=1, ln=True)
        pdf.cell(95, 6, f"Qualification: {doctor_qualification}", border=1)
        pdf.cell(95, 6, f"Experience: {doctor_experience}", border=1, ln=True)
        pdf.cell(95, 6, f"Assigned Hospital: {to_hospital}", border=1)
        pdf.cell(95, 6, f"Referral ID: {referral_id}", border=1, ln=True)
        pdf.ln(3)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 5 — COMPLETE CLINICAL PROFILE
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_text_color(*DEEP_BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  4. COMPLETE CLINICAL PROFILE", ln=True, fill=True)
        pdf.ln(1)

        def write_field(label, value):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*DEEP_BLUE)
            pdf.write(5, f"{label}: ")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 0, 0)
            val_str = str(value) if value and str(value).lower() not in ["none","null","n/a",""] else "None reported"
            pdf.write(5, val_str + "\n")
            pdf.ln(1)

        write_field("Known Allergies", pat_allerg)
        write_field("Chronic / Existing Conditions", pat_chron)
        write_field("Previous Diseases", pat_prev_d)
        write_field("Current / Previous Medications", pat_prev_m)
        write_field("Previous Reports / Lab Results", pat_prev_r)
        pdf.ln(2)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 6 — FULL CONSULTATION HISTORY
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_text_color(*DEEP_BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  5. COMPLETE MEDICAL CONSULTATION HISTORY", ln=True, fill=True)
        pdf.ln(1)

        if history_rows:
            for i, h in enumerate(history_rows, 1):
                pdf.set_fill_color(245, 248, 255)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*DEEP_BLUE)
                pdf.cell(0, 6, f"  Visit {i}:  {h[2]}  at  {h[3]}", border=1, ln=True, fill=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "B", 8.5)
                pdf.write(5, "    Symptoms: ")
                pdf.set_font("Helvetica", "", 8.5)
                pdf.write(5, str(h[0])[:200] + "\n")
                pdf.set_font("Helvetica", "B", 8.5)
                pdf.write(5, "    Diagnosis & Advice: ")
                pdf.set_font("Helvetica", "", 8.5)
                pdf.write(5, str(h[1])[:200] + "\n")
                pdf.ln(2)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*GRAY_TEXT)
            pdf.cell(0, 5, "No previous consultation records available.", ln=True)
            pdf.ln(3)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 7 — PAST EMERGENCY REFERRALS
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_text_color(*DEEP_BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  6. PAST EMERGENCY REFERRAL HISTORY", ln=True, fill=True)
        pdf.ln(1)

        if past_referrals:
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_fill_color(225, 235, 255)
            pdf.set_text_color(*DEEP_BLUE)
            pdf.cell(38, 6, "Date & Time", border=1, fill=True)
            pdf.cell(55, 6, "Hospital Referred To", border=1, fill=True)
            pdf.cell(45, 6, "Symptoms", border=1, fill=True)
            pdf.cell(25, 6, "Status", border=1, fill=True)
            pdf.cell(27, 6, "Referral ID", border=1, fill=True, ln=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(0, 0, 0)
            for em in past_referrals:
                pdf.cell(38, 6, str(em[3] or "N/A")[:18], border=1)
                pdf.cell(55, 6, str(em[0] or "N/A")[:28], border=1)
                pdf.cell(45, 6, str(em[2] or "N/A")[:22], border=1)
                pdf.cell(25, 6, str(em[1] or "N/A")[:12], border=1)
                pdf.cell(27, 6, str(em[4] or "N/A")[:13], border=1, ln=True)
            pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*GRAY_TEXT)
            pdf.cell(0, 5, "No prior emergency referral history.", ln=True)
            pdf.ln(3)

        # ══════════════════════════════════════════════════════════════════════
        # SECTION 8 — REFERRAL SUMMARY BOX
        # ══════════════════════════════════════════════════════════════════════
        pdf.set_fill_color(*RED_ALERT)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "  7. REFERRAL SUMMARY", ln=True, fill=True)
        pdf.ln(1)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(95, 6, f"Referring Hospital: {from_hospital}", border=1)
        pdf.cell(95, 6, f"Receiving Hospital: {to_hospital}", border=1, ln=True)
        pdf.cell(95, 6, f"Patient Name: {pat_name}  (ID: {pat_id})", border=1)
        pdf.cell(95, 6, f"Referral ID: {referral_id}", border=1, ln=True)
        pdf.cell(95, 6, f"Emergency ID: {emergency_id}", border=1)
        pdf.cell(95, 6, f"Referral Date & Time: {now_str}", border=1, ln=True)
        pdf.cell(95, 6, f"Assigned Doctor: {doctor_name}", border=1)
        pdf.cell(95, 6, f"Doctor Specialization: {doctor_specialization}", border=1, ln=True)
        pdf.cell(95, 6, f"Reason for Referral: {specialization} — {severity.upper()} Severity", border=1)
        pdf.cell(95, 6, f"Medical History Transferred: YES (Auto)", border=1, ln=True)
        pdf.ln(3)

        if additional_notes:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(0, 5, "Additional Clinical Notes:", ln=True)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, str(additional_notes)[:500])
            pdf.ln(2)

        # ── Signature area ────────────────────────────────────────────────────
        pdf.ln(4)
        pdf.set_draw_color(*DEEP_BLUE)
        pdf.line(10, pdf.get_y(), 90, pdf.get_y())
        pdf.set_x(10)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.cell(80, 4, "Authorized Signatory — Prasad Medical Portal", ln=False)
        pdf.set_x(120)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())
        pdf.set_x(120)
        pdf.cell(80, 4, f"Date: {now_date}", ln=True)
        pdf.ln(5)

        # ── QR Code ───────────────────────────────────────────────────────────
        qr_bytes = generate_emergency_qr_card(patient_username)
        if qr_bytes:
            temp_qr = f"temp_ref_qr_{patient_username}.png"
            with open(temp_qr, "wb") as fq:
                fq.write(qr_bytes)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*DEEP_BLUE)
            pdf.cell(0, 5, "Emergency QR Card (scan to access patient record):", ln=True)
            pdf.image(temp_qr, x=10, y=pdf.get_y(), w=35, h=35)
            pdf.ln(37)
            try:
                os.remove(temp_qr)
            except: pass

        # ── Disclaimer ────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*GRAY_TEXT)
        pdf.multi_cell(0, 4,
            "DISCLAIMER: This referral letter is generated automatically by Prasad Medical Portal. "
            "It contains patient-consented medical history transferred to the receiving hospital and assigned doctor. "
            "All information is confidential and for clinical use only. "
            f"Generated on {now_str}.")

        pdf_bytes = pdf.output()
        if isinstance(pdf_bytes, bytearray):
            pdf_bytes = bytes(pdf_bytes)
        return pdf_bytes

    except Exception as e:
        print("generate_referral_pdf error:", e)
        from datetime import datetime
        fallback = (
            f"PRASAD MEDICAL PORTAL — REFERRAL LETTER\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Referral ID: {referral_id}\n"
            f"Patient: {patient_username}\n"
            f"From: {from_hospital}\n"
            f"To: {to_hospital}\n"
            f"Doctor: {doctor_name} ({doctor_specialization})\n"
            f"Symptoms: {symptoms}\n"
            f"Severity: {severity}\n"
        )
        return fallback.encode("utf-8")


def process_profile_image(uploaded_file, max_size_mb=5):
    from PIL import Image
    import io
    
    # 1. Validate size
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(f"Image size exceeds the maximum limit of {max_size_mb} MB.")
        
    # 2. Open and validate format
    img = Image.open(uploaded_file)
    # Check format in uppercase
    fmt = str(img.format).upper() if img.format else "PNG"
    if fmt not in ["JPEG", "JPG", "PNG"]:
        img = img.convert("RGB")
        
    # 3. Resize and optimize
    img.thumbnail((300, 300))
    
    # Save to bytes
    out_io = io.BytesIO()
    img.save(out_io, format="PNG", optimize=True)
    optimized_bytes = out_io.getvalue()
    return optimized_bytes