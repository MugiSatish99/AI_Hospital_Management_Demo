# ai.py

import os
import json
import re
import sqlite3
from datetime import datetime

from groq import Groq
from dotenv import load_dotenv
from dataset import find_disease

from PIL import Image
import numpy as np
import cv2
import mediapipe as mp
import pandas as pd

from database import get_history
from emergency import check_emergency, get_issue_type, get_emergency_level
from utils import map_symptom_to_specialization

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    df = pd.read_csv("dataset.csv")
except:
    df = None

mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection()


def detect_body_part(image):
    try:
        img = np.array(image)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_detection.process(img_rgb)

        if results.detections:
            return "face"

        return "unknown"

    except:
        return "unknown"


def image_to_symptom(image):
    part = detect_body_part(image)

    if part == "face":
        return "skin rash"

    elif part == "unknown":
        return "body pain"

    return "general issue"


def clean_symptom_text(text):
    text = str(text).lower().strip()
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
        "head ach": "headache",
        "diaria": "diarrhea",
        "diarhea": "diarrhea",
        "feever": "fever",
        "feverr": "fever",
        "migrane": "migraine",
        "migran": "migraine",
        "vomitingg": "vomiting",
        "sweling": "swelling",
        "ches pain": "chest pain",
        "chestpain": "chest pain",
        "dizines": "dizziness",
        "dizzy": "dizziness"
    }
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    return text


def get_user_details(username):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT name, age, blood_group, phone FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "name": row[0],
                "age": row[1],
                "blood_group": row[2],
                "phone": row[3]
            }
    except Exception as e:
        print("Error getting user details:", e)
    return None


def get_ai_response(prompt, user=None, chat_history=[]):
    try:
        prompt = clean_symptom_text(prompt)

        # 1. System instruction with Patient Context
        system_content = "You are Aura, an advanced medical AI assistant for AI Hospital System. "
        
        if user:
            from database import load_patient_clinical_data
            details = load_patient_clinical_data(user)
            
            if details:
                system_content += (
                    f"You are consulting with Patient Name: {details['name']}, Age: {details['age']}, Gender: {details['gender']}, "
                    f"Blood Group: {details['blood_group']}. Known Allergies: {details['allergies']}. "
                    f"Chronic / Existing Diseases: {details['chronic_diseases']}. Previous Diagnosed Diseases: {details['previous_diseases']}. "
                    f"Previous Medications: {details['previous_medications']}. Past Medical Reports Summary: {details['previous_reports']}. "
                    f"Emergency Contact: {details['emergency_contact']}. "
                )
            
            if details and details.get("history") and details["history"] != "None":
                system_content += f"Patient's recent medical consultations: {details['history']}. "

        system_content += (
            "Provide helpful, clinical-grade, yet easily understandable answers. Support follow-up questions. "
            "IMPORTANT: If the user asks a general query completely unrelated to medicine, health, symptoms, first aid, "
            "or hospital services (e.g., programming questions, history, math, news), politely remind them that you are "
            "a clinical medical assistant and ask them to focus on their health concerns."
        )

        messages = [{"role": "system", "content": system_content}]

        # 2. Add Chat History (support tuple and dict formats)
        for msg in chat_history:
            if isinstance(msg, dict):
                messages.append(msg)
            elif isinstance(msg, (tuple, list)) and len(msg) >= 2:
                role = "user" if str(msg[0]).lower() in ["you", "user"] else "assistant"
                messages.append({"role": role, "content": msg[1]})

        # 3. Add current prompt
        messages.append({"role": "user", "content": prompt})

        chat = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.2
        )

        return chat.choices[0].message.content.strip()

    except Exception as e:
        return f"AI Chat Error: {str(e)}"


def detect_issue(image):
    try:
        if not isinstance(image, np.ndarray):
            image = np.array(image)

        avg_color = image.mean(axis=(0, 1))
        part = detect_body_part(image)

        if avg_color[0] > avg_color[1] and avg_color[0] > avg_color[2]:
            if part == "face":
                return "nose bleeding", 0.80

            return "bleeding wound", 0.75

        elif avg_color.mean() < 80:
            return "burn", 0.70

        return "skin issue", 0.65

    except:
        return "unknown", 0.50


def ask_groq(prompt):
    chat = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.1-8b-instant",
        temperature=0
    )
    return chat.choices[0].message.content.strip()


def parse_ai_json(res, text):
    try:
        res = str(res)
        res = res.replace("```json", "")
        res = res.replace("```", "")
        res = res.strip()

        try:
            parsed = json.loads(res)
        except:
            match = re.search(r"\{.*\}", res, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
            else:
                return None

        meds = parsed.get("medications", [])
        if not meds and parsed.get("medicine"):
            meds = [{
                "name": parsed.get("medicine", "Consult Doctor"),
                "dosage": parsed.get("dosage", "As prescribed"),
                "frequency": parsed.get("frequency", "Daily"),
                "duration": parsed.get("duration", "5 days"),
                "precautions": parsed.get("advice", "Take after meals")
            }]
            
        return {
            "condition": parsed.get("condition", "General illness"),
            "confidence_score": parsed.get("confidence_score", "85%"),
            "risk_score": parsed.get("risk_score", "35%"),
            "first_aid": parsed.get("first_aid", "Please rest and drink plenty of fluids."),
            "medications": meds,
            "specialization": parsed.get("specialization", map_symptom_to_specialization(text)),
            "hospitals": parsed.get("hospitals", "Hospital referral recommended for detailed assessment."),
            "doctors": parsed.get("doctors", "Specialist doctor consultation assigned."),
            "follow_up": parsed.get("follow_up", "Follow up in 3 to 5 days if symptoms persist."),
            "explanation": parsed.get("explanation", "Symptoms evaluated against general clinical patterns.")
        }
    except Exception as e:
        print("JSON Parse Error:", e)
    return None


def full_ai_analysis(text, user=None):
    try:
        s = clean_symptom_text(text)
        spec = map_symptom_to_specialization(s)

        from database import load_patient_clinical_data
        patient_data = load_patient_clinical_data(user) if user else None
        
        from first_aid import get_first_aid
        local_first_aid = get_first_aid(s, "en")
        
        is_emergency = check_emergency(s)
        severity_level = "low"
        if is_emergency:
            severity_level = "critical"
            from emergency import get_emergency_level
            severity_level = get_emergency_level(s)
        
        patient_context = ""
        if patient_data:
            patient_context = f"""
Patient Clinical Profile:
- Age: {patient_data.get('age', 30)}
- Gender: {patient_data.get('gender', 'Unknown')}
- Known Allergies: {patient_data.get('allergies', 'None')}
- Chronic / Existing Diseases: {patient_data.get('chronic_diseases', 'None')}
- Previous Diagnosed Diseases: {patient_data.get('previous_diseases', 'None')}
- Previous Medications: {patient_data.get('previous_medications', 'None')}
- Past Medical Reports Summary: {patient_data.get('previous_reports', 'None')}
- Recent Hospital Consultations: {patient_data.get('history', 'None')}
"""

        prompt = f"""
You are an advanced medical diagnostic AI. Analyze these symptoms carefully and return the diagnosis.

Symptoms:
{s}
{patient_context}

Return ONLY a valid JSON object. 

Format:
{{
  "condition": "predicted disease or condition name",
  "confidence_score": "estimated confidence percentage (e.g., 85%)",
  "risk_score": "estimated risk percentage based on severity and age (e.g., 40%)",
  "first_aid": "first aid suggestions and emergency precautions",
  "medications": [
    {{
      "name": "medicine name",
      "dosage": "dosage (e.g. 500mg or 1 tablet)",
      "frequency": "frequency (e.g. twice daily)",
      "duration": "duration (e.g. 5 days)",
      "precautions": "safety precautions"
    }}
  ],
  "specialization": "{spec}",
  "hospitals": "hospital department allocation and bed recommendations",
  "doctors": "specialist recommendation explanation",
  "follow_up": "follow-up recommendations (frequency, indicators to watch)",
  "explanation": "Safety evaluation and clinical explanation. Show how you cross-referenced patient's age, allergies, existing conditions, and past medicines to ensure no drug interactions or allergic reactions occur."
}}

Rules:
1. ONLY return the raw JSON object. Do not include markdown codeblocks (no ```json).
2. Suggest medicines that are completely safe. If the patient has allergies or is taking other medications, check for interactions and include the details in the explanation.
3. If the input is completely unrelated to health or medicine, return:
{{
  "condition": "Unrelated Input",
  "confidence_score": "0%",
  "risk_score": "0%",
  "first_aid": "Please enter a health-related query.",
  "medications": [],
  "specialization": "General Physician",
  "hospitals": "None",
  "doctors": "None",
  "follow_up": "None",
  "explanation": "The query is unrelated to health or medicine."
}}
"""

        try:
            res = ask_groq(prompt)
            parsed = parse_ai_json(res, text)
            if parsed:
                return parsed
        except Exception as groq_err:
            print("Groq API error, falling back to local dataset:", groq_err)

        from dataset import find_disease
        local_match = find_disease(s)
        
        disease_name = local_match.get("disease", "General Illness")
        med_name = local_match.get("medicine", "Consult Doctor")
        advice = local_match.get("advice", "Take rest and drink water.")
        
        fallback_res = {
            "condition": disease_name,
            "confidence_score": "75%",
            "risk_score": "75%" if is_emergency else "25%",
            "first_aid": local_first_aid if local_first_aid else advice,
            "medications": [
                {
                    "name": med_name,
                    "dosage": "As prescribed",
                    "frequency": "Daily",
                    "duration": "5 days",
                    "precautions": "Verify safety with pharmacist if you have drug allergies."
                }
            ],
            "specialization": spec,
            "hospitals": "AI Hospital System (General Emergency)" if is_emergency else "AI Outpatient Center",
            "doctors": f"Dr. Specialist ({spec})",
            "follow_up": "Follow-up consultation in 3 days.",
            "explanation": "Matched against verified local clinical database records."
        }
        return fallback_res

    except Exception as e:
        print("AI diagnostic exception:", e)
        return {
            "condition": "System Exception",
            "confidence_score": "0%",
            "risk_score": "0%",
            "first_aid": "Go to the emergency department.",
            "medications": [],
            "specialization": "General Physician",
            "hospitals": "Emergency Care",
            "doctors": "Duty Doctor",
            "follow_up": "Immediate",
            "explanation": f"System error occurred: {str(e)}"
        }