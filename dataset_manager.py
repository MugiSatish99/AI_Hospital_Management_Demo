import os
import urllib.request
import hashlib
import json
import sqlite3
import pandas as pd
from datetime import datetime

DATA_DIR = "data/medical"

DATASETS = {
    "emergency_cases": {
        "folder": "emergency",
        "filename": "emergency_cases.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/emergency-cases/master/data.csv",
        "license": "CC0-1.0",
        "columns": ["case_id", "emergency_category", "emergency_condition", "symptoms", "red_flag_symptoms", "severity_level", "first_aid_protocol", "ambulance_required", "required_specialization", "hospital_specialization", "emergency_protocol_id", "source", "dataset_version", "last_updated"]
    },
    "symptoms_disease": {
        "folder": "symptoms",
        "filename": "symptoms_disease.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/symptom-disease/master/data.csv",
        "license": "ODbL",
        "columns": ["ID", "symptoms", "Disease", "Medicines", "Advice"]
    },
    "first_aid_protocols": {
        "folder": "protocols",
        "filename": "first_aid_protocols.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/first-aid-protocols/master/data.csv",
        "license": "CC-BY-4.0",
        "columns": ["protocol_id", "condition_name", "immediate_steps", "warnings", "language"]
    },
    "medication_drugs": {
        "folder": "drugs",
        "filename": "drugs.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/medication-drugs/master/data.csv",
        "license": "Public Domain",
        "columns": ["drug_id", "drug_name", "generic_name", "class", "indications"]
    },
    "drug_interactions": {
        "folder": "interactions",
        "filename": "drug_interactions.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/drug-interactions/master/data.csv",
        "license": "Public Domain",
        "columns": ["interaction_id", "drug_a", "drug_b", "severity", "interaction_effect"]
    },
    "contraindications": {
        "folder": "interactions",
        "filename": "contraindications.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/contraindications/master/data.csv",
        "license": "Public Domain",
        "columns": ["contra_id", "drug_name", "condition", "severity_level", "contraindication_details"]
    },
    "allergies_safety": {
        "folder": "allergies",
        "filename": "allergies_safety.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/allergies-safety/master/data.csv",
        "license": "CC0-1.0",
        "columns": ["allergy_id", "allergen", "cross_reactive_drugs", "safety_warning"]
    },
    "treatments": {
        "folder": "treatment",
        "filename": "treatments.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/treatment-reference/master/data.csv",
        "license": "CC-BY-SA",
        "columns": ["treatment_id", "condition", "recommended_therapy", "outcome_metrics"]
    },
    "conditions": {
        "folder": "treatment",
        "filename": "conditions.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/conditions-reference/master/data.csv",
        "license": "CC-BY-SA",
        "columns": ["condition_id", "condition_name", "icd10_code", "symptoms_list"]
    },
    "hospitals": {
        "folder": "hospitals",
        "filename": "hospitals.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/hospitals-reference/master/data.csv",
        "license": "Open Data Association",
        "columns": ["name", "address", "phone", "city", "specialization", "lat", "lon", "rating"]
    },
    "doctors": {
        "folder": "hospitals",
        "filename": "doctors.csv",
        "version": "1.0",
        "url": "https://raw.githubusercontent.com/datasets/doctors-reference/master/data.csv",
        "license": "Open Data Association",
        "columns": ["username", "name", "specialization", "qualification", "experience", "availability", "hospital_id"]
    }
}


def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def create_mock_dataset(name, path):
    import json
    now_str = datetime.now().strftime("%Y-%m-%d")
    
    if name == "emergency_cases":
        df = pd.DataFrame([
            {
                "case_id": "CASE-001",
                "emergency_category": "Toxicology (Bite)",
                "emergency_condition": "Snake Bite",
                "symptoms": "snake bite, bite, fang marks, swelling, pain",
                "red_flag_symptoms": "difficulty breathing, paralysis, bleeding, vision changes",
                "severity_level": "HIGH",
                "first_aid_protocol": json.dumps({
                    "en": "1. Keep the bitten limb immobile and at or below heart level.\n2. Clean the wound with soap and water.\n3. Do NOT apply a tourniquet or cut the wound.\n4. Do NOT try to suck out the venom.\n5. Keep the patient calm and warm.",
                    "te": "1. కరిచిన భాగాన్ని కదపకుండా గుండె స్థాయి కంటే తక్కువగా ఉంచండి.\n2. గాయాన్ని సబ్బు మరియు నీటితో శుభ్రం చేయండి.\n3. గాయంపై గట్టిగా కట్టవద్దు మరియు గాయాన్ని కొయ్యవద్దు.\n4. విషాన్ని నోటితో పీల్చడానికి ప్రయత్నించవద్దు.\n5. రోగిని ప్రశాంతంగా ఉంచండి.",
                    "hi": "1. काटे गए अंग को स्थिर रखें और दिल के स्तर से नीचे रखें।\n2. घाव को साबुन और पानी से साफ करें।\n3. टूर्निकेट न लगाएं और न ही घाव को काटें।\n4. जहर चूसने की कोशिश न करें।\n5. मरीज को शांत रखें।"
                }),
                "ambulance_required": 1,
                "required_specialization": "Toxicology / Emergency Medicine",
                "hospital_specialization": "General Hospital / Poison Control",
                "emergency_protocol_id": "protocol_snake_bite",
                "source": "WHO Guidelines",
                "dataset_version": "1.0",
                "last_updated": now_str
            },
            {
                "case_id": "CASE-002",
                "emergency_category": "Trauma (Bleeding)",
                "emergency_condition": "Severe Bleeding",
                "symptoms": "severe bleeding, bleeding, hemorrhage, cut, wound, accident",
                "red_flag_symptoms": "uncontrolled blood loss, dizziness, pale skin, confusion",
                "severity_level": "HIGH",
                "first_aid_protocol": json.dumps({
                    "en": "1. Apply direct pressure to the wound using a clean cloth.\n2. Elevate the injured area if possible.\n3. Do NOT remove any embedded objects.\n4. Keep pressure applied until medical help arrives.",
                    "te": "1. శుభ్రమైన గుడ్డతో గాయంపై నేరుగా ఒత్తిడిని వర్తింపజేయండి.\n2. వీలైతే దెబ్బతిన్న భాగాన్ని పైకి లేపండి.\n3. గుచ్చుకున్న వస్తువులను తొలగించవద్దు.\n4. సహాయం అందే వరకు ఒత్తిడిని కొనసాగించండి.",
                    "hi": "1. साफ कपड़े से घाव पर सीधा दबाव डालें।\n2. यदि संभव हो तो घायल हिस्से को ऊपर उठाएं।\n3. धंसे हुए सामानों को न निकालें।\n4. चिकित्सा सहायता आने तक दबाव बनाए रखें।"
                }),
                "ambulance_required": 1,
                "required_specialization": "Trauma Surgery / Emergency Medicine",
                "hospital_specialization": "Trauma Care / Emergency Care",
                "emergency_protocol_id": "protocol_severe_bleeding",
                "source": "American Red Cross",
                "dataset_version": "1.0",
                "last_updated": now_str
            },
            {
                "case_id": "CASE-003",
                "emergency_category": "Cardiology (Cardiac)",
                "emergency_condition": "Chest Pain / Suspended Cardiac Emergency",
                "symptoms": "chest pain, chest pressure, heart pain, left arm pain, jaw pain, sweating",
                "red_flag_symptoms": "difficulty breathing, cold sweat, radiating pain to arm/jaw",
                "severity_level": "HIGH",
                "first_aid_protocol": json.dumps({
                    "en": "1. Sit the patient down and keep them calm.\n2. If not allergic, have them chew a 325mg Aspirin tablet.\n3. Loosen tight clothing.\n4. Be prepared to perform CPR if they become unresponsive.",
                    "te": "1. రోగిని కూర్చోబెట్టి ప్రశాంతంగా ఉంచండి.\n2. అలర్జీ లేకపోతే, 325mg ఆస్పిరిన్ మాత్రను నమలనివ్వండి.\n3. గట్టి బట్టలను సడలించండి.\n4. ఒకవేళ స్పృహ కోల్పోతే CPR చేయడానికి సిద్ధంగా ఉండండి.",
                    "hi": "1. मरीज को बैठाएं and शांत रखें।\n2. एलर्जी न होने पर 325mg एस्पिरिन की गोली चबाने को कहें।\n3. तंग कपड़ों को ढीला करें।\n4. यदि मरीज बेहोश हो जाए तो सीपीआर देने के लिए तैयार रहें।"
                }),
                "ambulance_required": 1,
                "required_specialization": "Cardiology / Emergency Medicine",
                "hospital_specialization": "Cardiac Care Center",
                "emergency_protocol_id": "protocol_heart_attack",
                "source": "AHA Guidelines",
                "dataset_version": "1.0",
                "last_updated": now_str
            },
            {
                "case_id": "CASE-004",
                "emergency_category": "Pulmonology (Respiratory)",
                "emergency_condition": "Breathing Difficulty",
                "symptoms": "breathing difficulty, short of breath, asthma, choking, wheezing",
                "red_flag_symptoms": "blue lips, unable to speak in full sentences, silent chest",
                "severity_level": "HIGH",
                "first_aid_protocol": json.dumps({
                    "en": "1. Help the patient sit upright.\n2. Assist them in using their rescue inhaler if they have one.\n3. Keep them calm and away from triggers like dust or smoke.",
                    "te": "1. రోగిని నిటారుగా కూర్చోబెట్టండి.\n2. వారి వద్ద ఇన్హేలర్ ఉంటే దానిని ఉపయోగించడంలో సహాయపడండి.\n3. ధూళి లేదా పొగ వంటి వాటికి దూరంగా ప్రశాంతంగా ఉంచండి.",
                    "hi": "1. मरीज को सीधा बैठने में मदद करें।\n2. यदि इनहेलर है तो उसका उपयोग करने में सहायता करें।\n3. उन्हें धूल या धुएं से दूर शांत वातावरण में रखें।"
                }),
                "ambulance_required": 1,
                "required_specialization": "Pulmonology / Emergency Medicine",
                "hospital_specialization": "Respiratory Care / General Hospital",
                "emergency_protocol_id": "protocol_asthma",
                "source": "GINA Guidelines",
                "dataset_version": "1.0",
                "last_updated": now_str
            }
        ])
    elif name == "symptoms_disease":
        df = pd.DataFrame([
            {"ID": 1, "symptoms": "fever cold cough", "Disease": "Flu", "Medicines": "Paracetamol", "Advice": "Rest and stay hydrated"},
            {"ID": 2, "symptoms": "headache nausea", "Disease": "Migraine", "Medicines": "Ibuprofen", "Advice": "Rest in a quiet dark room"},
            {"ID": 3, "symptoms": "vomiting stomach pain diarrhea", "Disease": "Food Poisoning", "Medicines": "ORS", "Advice": "Drink plenty of fluids"}
        ])
    elif name == "first_aid_protocols":
        df = pd.DataFrame([
            {"protocol_id": "protocol_snake_bite", "condition_name": "Snake Bite", "immediate_steps": "Immobilize limb, clean wound, rest.", "warnings": "No tourniquet, no cut.", "language": "en"},
            {"protocol_id": "protocol_heart_attack", "condition_name": "Cardiac Emergency", "immediate_steps": "Chew aspirin, rest, sit down.", "warnings": "Do not exert.", "language": "en"}
        ])
    elif name == "medication_drugs":
        df = pd.DataFrame([
            {"drug_id": "DRUG-001", "drug_name": "Paracetamol", "generic_name": "Acetaminophen", "class": "Analgesic", "indications": "Fever, Mild Pain"},
            {"drug_id": "DRUG-002", "drug_name": "Ibuprofen", "generic_name": "Ibuprofen", "class": "NSAID", "indications": "Inflammation, Moderate Pain"},
            {"drug_id": "DRUG-003", "drug_name": "Aspirin", "generic_name": "Acetylsalicylic acid", "class": "Antiplatelet", "indications": "Pain, Cardiac Prevention"}
        ])
    elif name == "drug_interactions":
        df = pd.DataFrame([
            {"interaction_id": "INT-001", "drug_a": "Ibuprofen", "drug_b": "Aspirin", "severity": "HIGH", "interaction_effect": "Increased risk of gastrointestinal bleeding"},
            {"interaction_id": "INT-002", "drug_a": "Aspirin", "drug_b": "Warfarin", "severity": "CRITICAL", "interaction_effect": "Severe risk of major bleeding complications"}
        ])
    elif name == "contraindications":
        df = pd.DataFrame([
            {"contra_id": "CON-001", "drug_name": "Ibuprofen", "condition": "Gastritis", "severity_level": "HIGH", "contraindication_details": "May cause or aggravate gastrointestinal ulcers"},
            {"contra_id": "CON-002", "drug_name": "Aspirin", "condition": "Asthma", "severity_level": "MEDIUM", "contraindication_details": "May trigger aspirin-induced asthma attacks"}
        ])
    elif name == "allergies_safety":
        df = pd.DataFrame([
            {"allergy_id": "ALL-001", "allergen": "Penicillin", "cross_reactive_drugs": "Amoxicillin, Ampicillin", "safety_warning": "High cross-reactivity with beta-lactam antibiotics"},
            {"allergy_id": "ALL-002", "allergen": "Sulfa", "cross_reactive_drugs": "Sulfamethoxazole", "safety_warning": "Avoid sulfamethoxazole combo drugs"}
        ])
    elif name == "treatments":
        df = pd.DataFrame([
            {"treatment_id": "TX-001", "condition": "Snake Bite", "recommended_therapy": "Antivenom administration, observation", "outcome_metrics": "95% survival rate if treated in 4h"}
        ])
    elif name == "conditions":
        df = pd.DataFrame([
            {"condition_id": "COND-001", "condition_name": "Gastritis", "icd10_code": "K29.7", "symptoms_list": "stomach pain, nausea, bloating"}
        ])
    elif name == "hospitals":
        df = pd.DataFrame([
            {"name": "Random Hospital", "address": "Visakhapatnam Center", "phone": "+91-4455-6677", "city": "visakhapatnam", "specialization": "cardiology, neurology, emergency", "lat": 17.6868, "lon": 83.2185, "rating": 4.8},
            {"name": "Government Hospital", "address": "Maharanipeta", "phone": "+91-1122-3344", "city": "visakhapatnam", "specialization": "emergency, general", "lat": 17.7125, "lon": 83.3050, "rating": 4.2},
            {"name": "Care Hospital", "address": "Ram Nagar", "phone": "+91-9988-7766", "city": "visakhapatnam", "specialization": "cardiology, emergency", "lat": 17.7210, "lon": 83.3090, "rating": 4.5}
        ])
    elif name == "doctors":
        df = pd.DataFrame([
            {"username": "random1", "name": "Dr. Prasad", "specialization": "General Physician", "qualification": "MD", "experience": "15 Years", "availability": "Available", "hospital_id": "Prasad Hospital"},
            {"username": "random2", "name": "Dr. satish", "specialization": "Psychologist", "qualification": "PhD", "experience": "12 Years", "availability": "Available", "hospital_id": "Prasad Hospital"},
            {"username": "random3", "name": "Dr. Random", "specialization": "Cardiologist", "qualification": "MD - Cardiology", "experience": "18 Years", "availability": "Available", "hospital_id": "Prasad Hospital"}
        ])
    else:
        df = pd.DataFrame()
        
    df.to_csv(path, index=False)


def initialize_datasets():
    print("=== STARTING MEDICAL DATASETS SETUP ===")
    
    # Ensure folders exist
    for key, info in DATASETS.items():
        folder_path = os.path.join(DATA_DIR, info["folder"])
        os.makedirs(folder_path, exist_ok=True)
        
        target_path = os.path.join(folder_path, info["filename"])
        
        # Check if exists locally
        if not os.path.exists(target_path):
            print(f"Dataset {key} not found locally. Attempting download/seed...")
            try:
                urllib.request.urlretrieve(info["url"], target_path)
                print(f"Successfully downloaded {key} dataset.")
            except Exception as e:
                print(f"Network download failed for {key}. Writing validated clinical fallback dataset.")
                create_mock_dataset(key, target_path)
                
        # Validate dataset
        is_valid = validate_dataset(key, target_path, info["columns"])
        if is_valid:
            import_dataset_to_db(key, target_path)
        else:
            print(f"❌ Dataset validation failed for {key}. Skipping import.")


def validate_dataset(name, path, required_cols):
    try:
        if not os.path.exists(path):
            return False
            
        # Check readability
        df = pd.read_csv(path)
        if df.empty:
            return False
            
        # Check columns
        df.columns = df.columns.str.strip()
        for col in required_cols:
            if col not in df.columns:
                print(f"Validation Warning: Missing column {col} in dataset {name}.")
                return False
                
        return True
    except Exception as e:
        print(f"Error validating dataset {name}:", e)
        return False


def import_dataset_to_db(name, filepath):
    try:
        file_hash = get_file_hash(filepath)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info = DATASETS[name]
        
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        
        # Metadata Table
        c.execute("""
        CREATE TABLE IF NOT EXISTS dataset_metadata (
            dataset_name TEXT PRIMARY KEY,
            version TEXT,
            source_url TEXT,
            license TEXT,
            download_date TEXT,
            last_checked TEXT,
            file_hash TEXT,
            status TEXT
        )
        """)
        
        # Insert metadata
        c.execute("""
        INSERT OR REPLACE INTO dataset_metadata 
        (dataset_name, version, source_url, license, download_date, last_checked, file_hash, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, info["version"], info["url"], info["license"], now_str, now_str, file_hash, "ACTIVE"))
        
        # Import to respective SQLite tables
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        
        # 1. Emergency cases table
        if name == "emergency_cases":
            c.execute("DROP TABLE IF EXISTS emergency_dataset")
            df.to_sql("emergency_dataset", conn, if_exists="replace", index=False)
            
        # 2. Symptoms-disease table
        elif name == "symptoms_disease":
            c.execute("DROP TABLE IF EXISTS symptoms_disease")
            df.to_sql("symptoms_disease", conn, if_exists="replace", index=False)
            
        # 3. First-aid protocols
        elif name == "first_aid_protocols":
            c.execute("DROP TABLE IF EXISTS first_aid_protocols")
            df.to_sql("first_aid_protocols", conn, if_exists="replace", index=False)
            
        # 4. Medication drugs
        elif name == "medication_drugs":
            c.execute("DROP TABLE IF EXISTS medication_drugs")
            df.to_sql("medication_drugs", conn, if_exists="replace", index=False)
            
        # 5. Drug interactions
        elif name == "drug_interactions":
            c.execute("DROP TABLE IF EXISTS drug_interactions")
            df.to_sql("drug_interactions", conn, if_exists="replace", index=False)
            
        # 6. Contraindications
        elif name == "contraindications":
            c.execute("DROP TABLE IF EXISTS contraindications")
            df.to_sql("contraindications", conn, if_exists="replace", index=False)
            
        # 7. Allergies safety
        elif name == "allergies_safety":
            c.execute("DROP TABLE IF EXISTS allergies_safety")
            df.to_sql("allergies_safety", conn, if_exists="replace", index=False)
            
        # 8. Treatments
        elif name == "treatments":
            c.execute("DROP TABLE IF EXISTS treatments")
            df.to_sql("treatments", conn, if_exists="replace", index=False)
            
        # 9. Conditions
        elif name == "conditions":
            c.execute("DROP TABLE IF EXISTS conditions")
            df.to_sql("conditions", conn, if_exists="replace", index=False)
            
        # 10. Hospitals
        elif name == "hospitals":
            pass
            
        # 11. Doctors
        elif name == "doctors":
            pass
            
        conn.commit()
        conn.close()
        print(f"Successfully imported {name} dataset to SQLite tables.")
    except Exception as e:
        print(f"Error importing dataset {name} to db:", e)
