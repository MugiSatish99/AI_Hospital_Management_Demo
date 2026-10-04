import sqlite3
from datetime import datetime
import requests
import math


def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json").json()
        loc = res["loc"].split(",")
        return float(loc[0]), float(loc[1])
    except:
        return None, None


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def safe_add_column(cursor, table, column_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
    except:
        pass


def init_patient_updates():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS patient_updates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        update_text TEXT,
        created_time TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_patient_update(patient_name, update_text):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
    INSERT INTO patient_updates
    (patient_name, update_text, created_time)
    VALUES (?, ?, ?)
    """, (patient_name, update_text, now))

    conn.commit()
    conn.close()


def get_patient_updates(patient_name):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT update_text, created_time
    FROM patient_updates
    WHERE patient_name=?
    ORDER BY id DESC
    """, (patient_name,))

    data = c.fetchall()
    conn.close()
    return data


def init_cases():
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
    CREATE TABLE IF NOT EXISTS completed_cases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor TEXT,
        message TEXT,
        completed_time TEXT
    )
    """)

    conn.commit()
    conn.close()


def init_doctor_extra():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS doctor_extra (
        username TEXT UNIQUE,
        specialization TEXT,
        qualification TEXT,
        experience TEXT,
        availability TEXT,
        image BLOB
    )
    """)

    safe_add_column(c, "doctor_extra", "experience TEXT")
    safe_add_column(c, "doctor_extra", "availability TEXT")
    safe_add_column(c, "doctor_extra", "image BLOB")
    safe_add_column(c, "doctor_extra", "doctor_profile_image BLOB")
    safe_add_column(c, "doctor_extra", "image_path TEXT")
    safe_add_column(c, "doctor_extra", "image_updated_at TEXT")

    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        name TEXT,
        age INTEGER,
        phone TEXT
    )
    """)

    safe_add_column(c, "users", "blood_group TEXT")
    safe_add_column(c, "users", "image BLOB")
    safe_add_column(c, "users", "patient_id TEXT")
    safe_add_column(c, "users", "doctor_id TEXT")
    safe_add_column(c, "users", "staff_id TEXT")
    safe_add_column(c, "users", "emergency_contact TEXT")
    safe_add_column(c, "users", "allergies TEXT")
    safe_add_column(c, "users", "chronic_diseases TEXT")
    safe_add_column(c, "users", "previous_diseases TEXT")
    safe_add_column(c, "users", "previous_medications TEXT")
    safe_add_column(c, "users", "previous_reports TEXT")
    safe_add_column(c, "users", "gender TEXT")
    
    # Newly required columns for detailed profiles, Hospital role, and Face Login
    safe_add_column(c, "users", "email TEXT")
    safe_add_column(c, "users", "address TEXT")
    safe_add_column(c, "users", "city TEXT")
    safe_add_column(c, "users", "hospital_id TEXT")
    safe_add_column(c, "users", "qualification TEXT")
    safe_add_column(c, "users", "experience TEXT")
    safe_add_column(c, "users", "specialization TEXT")
    safe_add_column(c, "users", "department TEXT")
    safe_add_column(c, "users", "availability TEXT")
    safe_add_column(c, "users", "latitude REAL")
    safe_add_column(c, "users", "longitude REAL")
    safe_add_column(c, "users", "total_beds INTEGER")
    safe_add_column(c, "users", "available_beds INTEGER")
    safe_add_column(c, "users", "icu_beds INTEGER")
    safe_add_column(c, "users", "departments TEXT")
    safe_add_column(c, "users", "available_doctors TEXT")
    safe_add_column(c, "users", "status TEXT")
    safe_add_column(c, "users", "face_landmarks_signature TEXT")

    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        symptoms TEXT,
        result TEXT
    )
    """)

    safe_add_column(c, "patients", "date TEXT")
    safe_add_column(c, "patients", "time TEXT")
    safe_add_column(c, "patients", "status TEXT")
    safe_add_column(c, "patients", "note TEXT")
    safe_add_column(c, "patients", "assigned_doctor TEXT")
    safe_add_column(c, "patients", "hospital TEXT")
    safe_add_column(c, "patients", "lat REAL")
    safe_add_column(c, "patients", "lon REAL")

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        symptoms TEXT,
        result TEXT,
        date TEXT,
        time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS hospital_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        hospital TEXT,
        status TEXT
    )
    """)

    safe_add_column(c, "hospital_requests", "symptoms TEXT")
    safe_add_column(c, "hospital_requests", "result TEXT")
    safe_add_column(c, "hospital_requests", "lat REAL")
    safe_add_column(c, "hospital_requests", "lon REAL")
    safe_add_column(c, "hospital_requests", "created_at TEXT")
    safe_add_column(c, "hospital_requests", "emergency_id TEXT")
    safe_add_column(c, "hospital_requests", "referral_id TEXT")
    safe_add_column(c, "hospital_requests", "assigned_doctor TEXT")
    safe_add_column(c, "hospital_requests", "ambulance_status TEXT")
    safe_add_column(c, "hospital_requests", "ambulance_vehicle TEXT")
    safe_add_column(c, "hospital_requests", "referral_status TEXT")
    safe_add_column(c, "hospital_requests", "patient_id TEXT")
    safe_add_column(c, "hospital_requests", "last_updated TEXT")
    safe_add_column(c, "hospital_requests", "transfer_status TEXT")
    safe_add_column(c, "hospital_requests", "to_hospital_id TEXT")
    safe_add_column(c, "hospital_requests", "from_hospital_id TEXT")
    safe_add_column(c, "hospital_requests", "selected_hospital_id TEXT")
    safe_add_column(c, "hospital_requests", "selection_timestamp TEXT")

    # Medical Reports Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS medical_reports (
        report_id TEXT PRIMARY KEY,
        referral_id TEXT,
        patient_id TEXT,
        emergency_id TEXT,
        hospital_id TEXT,
        doctor_id TEXT,
        report_file_path TEXT,
        report_version INTEGER DEFAULT 1,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Logging Tables
    c.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        login_time TEXT,
        ip_address TEXT,
        status TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS emergency_access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        accessed_by TEXT,
        access_time TEXT,
        otp_verified TEXT
    )
    """)

    conn.commit()
    conn.close()

    init_doctor_extra()
    init_cases()
    init_patient_updates()
    init_hospital_beds()
    init_appointments()
    init_medication_reminders()
    init_notifications_table()
    init_shared_history()
    ensure_default_doctors()
    init_new_tables()


def ensure_default_doctors():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    docs = [
        ('random1', '1234', 'doctor', 'Dr. Prasad', 'General Physician', 'MBBS', '5', 'Available', 'Random Hospital'),
        ('random2', '1234', 'doctor', 'Dr. satish', 'Psychologist', 'mbbs', '2', 'Available', 'New Hospital'),
        ('random3', '1234', 'doctor', 'Dr. simba', 'Cardiologist', 'md', '7', 'Available', 'Old Hospital')
    ]

    for username, password, role, name, specialization, qualification, experience, availability, hospital_id in docs:
        c.execute("SELECT 1 FROM users WHERE username=?", (username,))
        if not c.fetchone():
            c.execute("""
            INSERT INTO users (username, password, role, name, specialization, qualification, experience, availability, hospital_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, password, role, name, specialization, qualification, experience, availability, hospital_id))
        else:
            c.execute("""
            UPDATE users 
            SET name=?, specialization=?, qualification=?, experience=?, availability=?, hospital_id=?
            WHERE username=?
            """, (name, specialization, qualification, experience, availability, hospital_id, username))
        
        c.execute("SELECT 1 FROM doctor_extra WHERE username=?", (username,))
        if not c.fetchone():
            c.execute("""
            INSERT INTO doctor_extra (username, specialization, qualification, experience, availability)
            VALUES (?, ?, ?, ?, ?)
            """, (username, specialization, qualification, experience, availability))
        else:
            c.execute("""
            UPDATE doctor_extra
            SET specialization=?, qualification=?, experience=?, availability=?
            WHERE username=?
            """, (specialization, qualification, experience, availability, username))

    conn.commit()
    conn.close()


def add_doctor_extra(
    username,
    specialization,
    qualification,
    experience=None,
    availability="Available",
    image=None
):
    init_doctor_extra()

    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    INSERT OR REPLACE INTO doctor_extra
    (
        username,
        specialization,
        qualification,
        experience,
        availability,
        image
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        username,
        specialization,
        qualification,
        experience,
        availability,
        image
    ))

    conn.commit()
    conn.close()


def get_doctor_extra(username):
    init_doctor_extra()

    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT
        username,
        specialization,
        qualification,
        experience,
        availability,
        image,
        doctor_profile_image,
        image_path,
        image_updated_at
    FROM doctor_extra
    WHERE username=?
    """, (username,))

    data = c.fetchone()
    conn.close()
    return data


def get_doctors_by_specialization(spec):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT username
    FROM doctor_extra
    WHERE LOWER(specialization)=LOWER(?)
    """, (spec,))

    doctors = [row[0] for row in c.fetchall()]
    conn.close()
    return doctors


def add_user(username, password, role, name=None, age=None, blood=None, phone=None, img=None,
             patient_id=None, doctor_id=None, staff_id=None, emergency_contact=None,
             allergies=None, chronic_diseases=None, previous_diseases=None,
             previous_medications=None, previous_reports=None, gender=None,
             email=None, address=None, city=None, hospital_id=None,
             qualification=None, experience=None, specialization=None, department=None, availability=None,
             latitude=None, longitude=None, total_beds=None, available_beds=None, icu_beds=None,
             departments=None, available_doctors=None, status=None, face_landmarks_signature=None):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    if username:
        c.execute("SELECT 1 FROM users WHERE username=?", (username,))
        if c.fetchone():
            conn.close()
            return "exists"

    if email:
        c.execute("SELECT 1 FROM users WHERE email=?", (email,))
        if c.fetchone():
            conn.close()
            return "email_exists"

    if phone:
        c.execute("SELECT 1 FROM users WHERE phone=?", (phone,))
        if c.fetchone():
            conn.close()
            return "phone_exists"

    if patient_id:
        c.execute("SELECT 1 FROM users WHERE patient_id=?", (patient_id,))
        if c.fetchone():
            conn.close()
            return "patient_exists"

    if doctor_id:
        c.execute("SELECT 1 FROM users WHERE doctor_id=?", (doctor_id,))
        if c.fetchone():
            conn.close()
            return "doctor_exists"

    if staff_id:
        c.execute("SELECT 1 FROM users WHERE staff_id=?", (staff_id,))
        if c.fetchone():
            conn.close()
            return "staff_exists"

    if hospital_id:
        c.execute("SELECT 1 FROM users WHERE hospital_id=?", (hospital_id,))
        if c.fetchone():
            conn.close()
            return "hospital_exists"

    c.execute("""
    INSERT INTO users
    (username, password, role, name, age, phone, blood_group, image,
     patient_id, doctor_id, staff_id, emergency_contact, allergies,
     chronic_diseases, previous_diseases, previous_medications, previous_reports, gender,
     email, address, city, hospital_id, qualification, experience, specialization, department, availability,
     latitude, longitude, total_beds, available_beds, icu_beds, departments, available_doctors, status, face_landmarks_signature)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, password, role, name, age, phone, blood, img,
          patient_id, doctor_id, staff_id, emergency_contact, allergies,
          chronic_diseases, previous_diseases, previous_medications, previous_reports, gender,
          email, address, city, hospital_id, qualification, experience, specialization, department, availability,
          latitude, longitude, total_beds, available_beds, icu_beds, departments, available_doctors, status, face_landmarks_signature))

    conn.commit()
    conn.close()
    return "created"



def delete_user(username):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()


def get_users():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, username, password, role, name, age, phone, blood_group
    FROM users
    """)

    data = c.fetchall()
    conn.close()
    return data


def check_emergency(symptoms):
    keywords = ["chest pain", "breathing", "unconscious", "heart"]

    for k in keywords:
        if k in str(symptoms).lower():
            return "EMERGENCY"

    return "NORMAL"


def symptom_to_specialization(symptoms):
    s = str(symptoms).lower()

    if "heart" in s or "chest" in s:
        return "Cardiologist"
    elif "brain" in s or "head" in s or "stroke" in s:
        return "Neurologist"
    elif "bone" in s or "fracture" in s:
        return "Orthopedic"
    elif "skin" in s or "rash" in s:
        return "Dermatologist"
    elif "eye" in s:
        return "Ophthalmologist"
    elif "ear" in s or "nose" in s or "throat" in s:
        return "ENT Specialist"
    elif "tooth" in s or "teeth" in s:
        return "Dentist"
    elif "child" in s or "baby" in s:
        return "Pediatrician"
    elif "pregnancy" in s or "women" in s:
        return "Gynecologist"
    elif "breathing" in s or "lungs" in s:
        return "Pulmonologist"
    elif "kidney" in s:
        return "Nephrologist"
    elif "urine" in s:
        return "Urologist"
    elif "diabetes" in s:
        return "Diabetologist"
    elif "cancer" in s:
        return "Oncologist"
    elif "stomach" in s or "vomiting" in s:
        return "Gastroenterologist"
    elif "mental" in s or "depression" in s:
        return "Psychiatrist"

    return "General Physician"


def save_request(patient_name, hospital, symptoms=None, result=None, lat=None, lon=None):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
    INSERT INTO hospital_requests (patient_name, hospital, symptoms, result, lat, lon, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (patient_name, hospital, symptoms, result, lat, lon, "Pending", now))

    conn.commit()
    conn.close()


def get_requests():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, patient_name, hospital, symptoms, result, lat, lon, status, created_at
    FROM hospital_requests
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def update_request_status(id, status):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    UPDATE hospital_requests
    SET status=?
    WHERE id=?
    """, (status, id))

    conn.commit()
    conn.close()


def save_patient(name, symptoms, result):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    status = check_emergency(symptoms)
    spec = symptom_to_specialization(symptoms)

    c.execute("""
    SELECT username
    FROM doctor_extra
    WHERE LOWER(specialization)=LOWER(?)
    AND LOWER(COALESCE(availability, 'Available')) != 'busy'
    """, (spec,))

    doc = c.fetchone()

    if doc:
        assigned_doctor = doc[0]
        status = "ASSIGNED"
    else:
        assigned_doctor = "Emergency Duty Doctor"

    c.execute("SELECT * FROM patients WHERE name=?", (name,))
    existing = c.fetchone()

    if existing:
        c.execute("""
        UPDATE patients
        SET symptoms=?, result=?, date=?, time=?, status=?, assigned_doctor=?
        WHERE name=?
        """, (
            symptoms, result, date, time, status,
            assigned_doctor, name
        ))

    else:
        c.execute("""
        INSERT INTO patients
        (name, symptoms, result, date, time, status, assigned_doctor)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, symptoms, result, date, time,
            status, assigned_doctor
        ))

    c.execute("""
    INSERT INTO history
    (name, symptoms, result, date, time)
    VALUES (?, ?, ?, ?, ?)
    """, (name, symptoms, result, date, time))

    conn.commit()
    conn.close()


def add_note(pid, note):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    UPDATE patients
    SET note=?
    WHERE id=?
    """, (note, pid))

    conn.commit()
    conn.close()


def get_active_patients():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, name, symptoms, status
    FROM patients
    WHERE status IN ('EMERGENCY','HIGH')
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def update_patient_status(pid, status):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    UPDATE patients
    SET status=?
    WHERE id=?
    """, (status, pid))

    conn.commit()
    conn.close()


def get_all_patients():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, name, symptoms, status, date, time
    FROM patients
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def get_patients():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT
        id,
        name,
        symptoms,
        result,
        date,
        time,
        status,
        assigned_doctor,
        hospital
    FROM patients
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def get_assigned_patients(doctor):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, name, symptoms, result, date, time, status, assigned_doctor, hospital
    FROM patients
    WHERE assigned_doctor=?
    ORDER BY id DESC
    """, (doctor,))

    data = c.fetchall()
    conn.close()
    return data


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

    active = c.fetchone()

    if active:
        conn.close()
        return

    c.execute("""
    INSERT INTO cases
    (doctor, message, status)
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

    final = []

    for d in data:
        if str(d[3]).upper() != "DONE":
            final.append({
                "id": d[0],
                "doctor": d[1],
                "message": d[2],
                "status": d[3]
            })

    return final


def update_case(cid, status):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    if str(status).upper() == "DONE":
        c.execute("""
        SELECT doctor, message
        FROM cases
        WHERE id=?
        """, (cid,))

        row = c.fetchone()

        if row:
            doctor, message = row
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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


def get_completed_cases(doctor):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, doctor, message, completed_time
    FROM completed_cases
    WHERE doctor=?
    ORDER BY id DESC
    """, (doctor,))

    data = c.fetchall()
    conn.close()
    return data


def get_history(name):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    if name == "all":
        c.execute("""
        SELECT name, symptoms, result, date, time
        FROM history
        ORDER BY id DESC
        """)
    else:
        c.execute("""
        SELECT name, symptoms, result, date, time
        FROM history
        WHERE name=?
        ORDER BY id DESC
        """, (name,))

    data = c.fetchall()
    conn.close()
    return data


def get_patient_full_history(name):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT symptoms, result, date, time
    FROM history
    WHERE name=?
    ORDER BY id DESC
    """, (name,))

    data = c.fetchall()
    conn.close()
    return data


def send_message(sender, receiver, message):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
    INSERT INTO messages
    (sender, receiver, message, time)
    VALUES (?, ?, ?, ?)
    """, (sender, receiver, message, now))

    conn.commit()
    conn.close()


def get_messages(user):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, sender, receiver, message, time
    FROM messages
    WHERE sender=? OR receiver=?
    ORDER BY id DESC
    """, (user, user))

    data = c.fetchall()
    conn.close()
    return data


def get_patient_users():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, username, password, role, name, age, phone, blood_group
    FROM users
    WHERE role='patient'
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def get_doctor_users():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, username, password, role, name, age, phone, blood_group
    FROM users
    WHERE role='doctor'
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def get_staff_users():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, username, password, role, name, age, phone, blood_group
    FROM users
    WHERE role='staff'
    ORDER BY id DESC
    """)

    data = c.fetchall()
    conn.close()
    return data


def get_patient_user():
    return get_patient_users()


def get_doctor_user():
    return get_doctor_users()


def get_staff_user():
    return get_staff_users()


def init_hospital_beds():
    import os
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS hospital_beds (
        hospital_name TEXT UNIQUE,
        total_beds INTEGER,
        available_beds INTEGER,
        total_icu INTEGER,
        available_icu INTEGER,
        emergency_support TEXT
    )
    """)
    
    c.execute("SELECT COUNT(*) FROM hospital_beds")
    count = c.fetchone()[0]
    if count == 0:
        try:
            import pandas as pd
            import random
            csv_path = "hospitals.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, on_bad_lines="skip")
                for _, row in df.iterrows():
                    name = str(row.get("name", "")).strip()
                    if not name:
                        continue
                    spec = str(row.get("specialization", "")).lower()
                    emergency_support = "Yes" if ("emergency" in spec or "cardio" in spec or "neuro" in spec) else "No"
                    rating = float(row.get("rating", 4.0)) if not pd.isna(row.get("rating")) else 4.0
                    total = int(rating * 20)
                    total = max(total, 10)
                    avail = random.randint(2, int(total * 0.6))
                    total_icu = int(rating * 4)
                    total_icu = max(total_icu, 2)
                    avail_icu = random.randint(0, int(total_icu * 0.5))
                    c.execute("""
                    INSERT OR IGNORE INTO hospital_beds 
                    (hospital_name, total_beds, available_beds, total_icu, available_icu, emergency_support)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, total, avail, total_icu, avail_icu, emergency_support))
        except Exception as e:
            print("Error initializing hospital_beds from CSV:", e)
            
    conn.commit()
    conn.close()


def init_appointments():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        doctor_name TEXT,
        hospital_name TEXT,
        appointment_date TEXT,
        appointment_time TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()


def init_medication_reminders():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS medication_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        medicine_name TEXT,
        dosage TEXT,
        frequency TEXT,
        duration TEXT,
        start_date TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()


def init_notifications_table():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT,
        type TEXT,
        message TEXT,
        status TEXT,
        time TEXT
    )
    """)
    conn.commit()
    conn.close()


def get_hospital_beds(hospital_name):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    SELECT total_beds, available_beds, total_icu, available_icu, emergency_support
    FROM hospital_beds
    WHERE hospital_name=?
    """, (hospital_name,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "total_beds": row[0],
            "available_beds": row[1],
            "total_icu": row[2],
            "available_icu": row[3],
            "emergency_support": row[4]
        }
    return None


def update_hospital_beds(hospital_name, available_beds, available_icu):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    UPDATE hospital_beds
    SET available_beds=?, available_icu=?
    WHERE hospital_name=?
    """, (available_beds, available_icu, hospital_name))
    conn.commit()
    conn.close()


def get_all_hospital_beds():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    SELECT hospital_name, total_beds, available_beds, total_icu, available_icu, emergency_support
    FROM hospital_beds
    """)
    rows = c.fetchall()
    conn.close()
    return [{
        "hospital_name": r[0],
        "total_beds": r[1],
        "available_beds": r[2],
        "total_icu": r[3],
        "available_icu": r[4],
        "emergency_support": r[5]
    } for r in rows]


def add_appointment(patient_name, doctor_name, hospital_name, date, time_slot):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    INSERT INTO appointments (patient_name, doctor_name, hospital_name, appointment_date, appointment_time, status)
    VALUES (?, ?, ?, ?, ?, 'Pending')
    """, (patient_name, doctor_name, hospital_name, date, time_slot))
    conn.commit()
    conn.close()


def get_appointments(user_name, role):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    if role == "patient":
        c.execute("""
        SELECT id, patient_name, doctor_name, hospital_name, appointment_date, appointment_time, status
        FROM appointments
        WHERE patient_name=?
        ORDER BY id DESC
        """, (user_name,))
    elif role == "doctor":
        c.execute("""
        SELECT id, patient_name, doctor_name, hospital_name, appointment_date, appointment_time, status
        FROM appointments
        WHERE doctor_name=?
        ORDER BY id DESC
        """, (user_name,))
    else:  # admin / staff
        c.execute("""
        SELECT id, patient_name, doctor_name, hospital_name, appointment_date, appointment_time, status
        FROM appointments
        ORDER BY id DESC
        """)
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "patient_name": r[1],
        "doctor_name": r[2],
        "hospital_name": r[3],
        "appointment_date": r[4],
        "appointment_time": r[5],
        "status": r[6]
    } for r in rows]


def update_appointment_status(appointment_id, status):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    UPDATE appointments
    SET status=?
    WHERE id=?
    """, (status, appointment_id))
    conn.commit()
    conn.close()


def add_reminder(patient_name, medicine_name, dosage, frequency, duration):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    start_date = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
    INSERT INTO medication_reminders (patient_name, medicine_name, dosage, frequency, duration, start_date, status)
    VALUES (?, ?, ?, ?, ?, ?, 'Active')
    """, (patient_name, medicine_name, dosage, frequency, duration, start_date))
    conn.commit()
    conn.close()


def get_reminders(patient_name):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    SELECT id, medicine_name, dosage, frequency, duration, start_date, status
    FROM medication_reminders
    WHERE patient_name=? AND status='Active'
    ORDER BY id DESC
    """, (patient_name,))
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "medicine_name": r[1],
        "dosage": r[2],
        "frequency": r[3],
        "duration": r[4],
        "start_date": r[5],
        "status": r[6]
    } for r in rows]


def update_reminder_status(reminder_id, status):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    UPDATE medication_reminders
    SET status=?
    WHERE id=?
    """, (status, reminder_id))
    conn.commit()
    conn.close()


def get_patient_risk_score(symptoms, age=30):
    text = str(symptoms).lower().strip()
    score = 0
    weights = {
        "chest pain": 45,
        "heart attack": 50,
        "breathing problem": 40,
        "shortness of breath": 40,
        "cannot breathe": 45,
        "unconscious": 50,
        "stroke": 50,
        "seizure": 40,
        "heavy bleeding": 40,
        "severe bleeding": 40,
        "accident": 45,
        "poison": 45,
        "overdose": 45,
        "electric shock": 50,
        "drowning": 50,
        "snake bite": 45,
        "head injury": 40,
        "spinal injury": 45,
        "burn": 25,
        "dog bite": 20,
        "fracture": 30,
        "high fever": 20,
        "continuous fever": 15,
        "vomiting blood": 45,
        "blood vomiting": 45,
        "severe stomach pain": 25,
        "severe dehydration": 30,
        "allergy severe": 35,
        "asthma attack": 40,
        "heat stroke": 40,
        "hypothermia": 35,
        "fever": 5,
        "vomiting": 5,
        "stomach pain": 10,
        "headache": 5,
        "dizziness": 10
    }
    
    for symptom, weight in weights.items():
        if symptom in text:
            score += weight
            
    if age > 60:
        score += 15
    elif age < 5:
        score += 10
        
    score = min(score, 100)
    return score


def init_shared_history():
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS shared_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_username TEXT,
        hospital_name TEXT,
        doctor_username TEXT,
        shared_data TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()


def share_patient_history(patient_username, hospital_name, doctor_username, shared_data):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
    INSERT INTO shared_history (patient_username, hospital_name, doctor_username, shared_data, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (patient_username, hospital_name, doctor_username, shared_data, now))
    conn.commit()
    conn.close()


def get_shared_history(hospital_name=None, doctor_username=None):
    conn = sqlite3.connect("hospital.db")
    c = conn.cursor()
    if hospital_name and doctor_username:
        c.execute("""
        SELECT id, patient_username, hospital_name, doctor_username, shared_data, timestamp
        FROM shared_history
        WHERE LOWER(hospital_name)=LOWER(?) OR LOWER(doctor_username)=LOWER(?)
        ORDER BY id DESC
        """, (hospital_name, doctor_username))
    elif hospital_name:
        c.execute("""
        SELECT id, patient_username, hospital_name, doctor_username, shared_data, timestamp
        FROM shared_history
        WHERE LOWER(hospital_name)=LOWER(?)
        ORDER BY id DESC
        """, (hospital_name,))
    elif doctor_username:
        c.execute("""
        SELECT id, patient_username, hospital_name, doctor_username, shared_data, timestamp
        FROM shared_history
        WHERE LOWER(doctor_username)=LOWER(?)
        ORDER BY id DESC
        """, (doctor_username,))
    else:
        c.execute("""
        SELECT id, patient_username, hospital_name, doctor_username, shared_data, timestamp
        FROM shared_history
        ORDER BY id DESC
        """)
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "patient_username": r[1],
        "hospital_name": r[2],
        "doctor_username": r[3],
        "shared_data": r[4],
        "timestamp": r[5]
    } for r in rows]


def load_patient_clinical_data(username):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        SELECT age, blood_group, allergies, chronic_diseases, previous_diseases, previous_medications, previous_reports, gender, emergency_contact, patient_id, phone, name
        FROM users WHERE username=?
        """, (username,))
        row = c.fetchone()
        
        c.execute("SELECT symptoms, result FROM history WHERE name=? ORDER BY id DESC LIMIT 3", (username,))
        history_rows = c.fetchall()
        conn.close()
        
        history_summary = ""
        if history_rows:
            history_summary = "; ".join([f"Symptoms: {r[0]}, Diagnosis: {r[1]}" for r in history_rows])
            
        if row:
            return {
                "age": row[0] or 30,
                "blood_group": row[1] or "Not Assigned",
                "allergies": row[2] or "None",
                "chronic_diseases": row[3] or "None",
                "previous_diseases": row[4] or "None",
                "previous_medications": row[5] or "None",
                "previous_reports": row[6] or "None",
                "gender": row[7] or "Unknown",
                "emergency_contact": row[8] or "Not Assigned",
                "patient_id": row[9] or "N/A",
                "phone": row[10] or "N/A",
                "name": row[11] or username,
                "history": history_summary or "None"
            }
    except Exception as e:
        print("Error loading patient clinical data:", e)
    return None


def update_patient_clinical_data(username, allergies, chronic_diseases, previous_diseases, previous_medications, previous_reports, emergency_contact, gender):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        UPDATE users
        SET allergies=?, chronic_diseases=?, previous_diseases=?, previous_medications=?, previous_reports=?, emergency_contact=?, gender=?
        WHERE username=?
        """, (allergies, chronic_diseases, previous_diseases, previous_medications, previous_reports, emergency_contact, gender, username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating patient clinical data:", e)
        return False


def update_doctor_image(username, image_bytes, image_path, updated_at):
    try:
        init_doctor_extra()
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        UPDATE doctor_extra
        SET doctor_profile_image=?, image_path=?, image_updated_at=?
        WHERE username=?
        """, (image_bytes, image_path, updated_at, username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating doctor image:", e)
        return False


def delete_doctor_image(username):
    try:
        init_doctor_extra()
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        UPDATE doctor_extra
        SET doctor_profile_image=NULL, image_path=NULL, image_updated_at=NULL
        WHERE username=?
        """, (username,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error deleting doctor image:", e)
        return False

# ================= NEW HELPERS FOR FORGOT PASSWORD & EMERGENCY LOGIN & LOGS =================

def check_mobile_number(phone):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE phone=?", (phone,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print("Error checking mobile number:", e)
        return None

def reset_user_password(username, new_password):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error resetting password:", e)
        return False

def verify_emergency_patient(patient_id, emergency_phone):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT username, name FROM users WHERE patient_id=? AND emergency_contact=?", (patient_id, emergency_phone))
        row = c.fetchone()
        conn.close()
        return row if row else None
    except Exception as e:
        print("Error verifying emergency patient:", e)
        return None

def log_emergency_access(patient_id, accessed_by, otp_verified="Yes"):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO emergency_access_logs (patient_id, accessed_by, access_time, otp_verified)
        VALUES (?, ?, ?, ?)
        """, (patient_id, accessed_by, now, otp_verified))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error logging emergency access:", e)
        return False

def log_login_event(username, status="Success", ip="127.0.0.1"):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO login_logs (username, login_time, ip_address, status)
        VALUES (?, ?, ?, ?)
        """, (username, now, ip, status))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error logging login event:", e)
        return False


def save_referral_request(patient_name, hospital, symptoms, result, lat, lon, emergency_id, referral_id, assigned_doctor, patient_id, transfer_status='SENT', to_hospital_id=None, from_hospital_id='HOSP_PRASAD', selected_hospital_id=None, selection_timestamp=None):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO hospital_requests 
        (patient_name, hospital, status, symptoms, result, lat, lon, created_at, emergency_id, referral_id, assigned_doctor, ambulance_status, ambulance_vehicle, referral_status, patient_id, last_updated, transfer_status, to_hospital_id, from_hospital_id, selected_hospital_id, selection_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_name, hospital, 'Sent', symptoms, result, lat, lon, now, emergency_id, referral_id, assigned_doctor, 'Requested', 'TBD', 'Sent', patient_id, now, transfer_status, to_hospital_id, from_hospital_id, selected_hospital_id, selection_timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving referral request:", e)
        return False


def get_prasad_referrals():
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM hospital_requests ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Error getting Prasad referrals:", e)
        return []


def get_received_referrals(hospital_name):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM hospital_requests WHERE hospital=? ORDER BY id DESC", (hospital_name,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Error getting received referrals:", e)
        return []


def update_referral_status(request_id, status):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE hospital_requests SET status=?, referral_status=?, last_updated=? WHERE id=?", (status, status, now, request_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating referral status:", e)
        return False


def update_referral_ambulance(request_id, status, vehicle):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE hospital_requests SET ambulance_status=?, ambulance_vehicle=?, last_updated=? WHERE id=?", (status, vehicle, now, request_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating ambulance status:", e)
        return False


def check_doctor_patient_authorization(doctor_username, patient_username):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        
        # 1. Check if currently assigned in hospital_requests
        c.execute("SELECT 1 FROM hospital_requests WHERE assigned_doctor=? AND patient_name=?", (doctor_username, patient_username))
        if c.fetchone():
            conn.close()
            return True
            
        # 2. Check if previously treated in cases table
        c.execute("SELECT 1 FROM cases WHERE doctor=? AND id IN (SELECT id FROM patients WHERE name=?)", (doctor_username, patient_username))
        if c.fetchone():
            conn.close()
            return True
            
        # 3. Check if previously treated in appointments table
        c.execute("SELECT 1 FROM appointments WHERE doctor=? AND patient_name=?", (doctor_username, patient_username))
        if c.fetchone():
            conn.close()
            return True
            
        # 4. Check if previously treated in shared_history table
        c.execute("SELECT 1 FROM shared_history WHERE doctor_username=? AND patient_username=?", (doctor_username, patient_username))
        if c.fetchone():
            conn.close()
            return True
            
        conn.close()
        return False
    except Exception as e:
        print("Error checking doctor authorization:", e)
        return False


def init_new_tables():
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        
        # Emergencies table
        c.execute("""
        CREATE TABLE IF NOT EXISTS emergencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emergency_id TEXT UNIQUE,
            patient_id TEXT,
            patient_name TEXT,
            emergency_type TEXT,
            detection_time TEXT,
            lat REAL,
            lon REAL,
            address TEXT,
            severity TEXT,
            status TEXT,
            ambulance_status TEXT,
            ambulance_vehicle TEXT,
            assigned_doctor TEXT,
            first_aid_provided TEXT,
            created_at TEXT
        )
        """)
        
        # Prescriptions table
        c.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id TEXT UNIQUE,
            consultation_id TEXT,
            patient_id TEXT,
            drug_name TEXT,
            dose TEXT,
            unit TEXT,
            frequency TEXT,
            route TEXT,
            duration TEXT,
            instructions TEXT,
            doctor_id TEXT,
            hospital_id TEXT,
            date_time TEXT,
            status TEXT
        )
        """)
        
        # Consultations table
        c.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consultation_id TEXT UNIQUE,
            patient_id TEXT,
            patient_name TEXT,
            symptoms TEXT,
            observations TEXT,
            diagnosis TEXT,
            treatment_plan TEXT,
            follow_up TEXT,
            doctor_id TEXT,
            hospital_id TEXT,
            created_at TEXT
        )
        """)
        
        # Medical Knowledge Table
        c.execute("""
        CREATE TABLE IF NOT EXISTS medical_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            key_name TEXT,
            value_data TEXT,
            version TEXT,
            last_validated TEXT
        )
        """)
        
        # Symptom submissions table
        c.execute("""
        CREATE TABLE IF NOT EXISTS symptom_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT,
            symptom_input TEXT,
            submission_time TEXT,
            emergency_detection_result TEXT,
            emergency_id TEXT,
            ai_analysis_id TEXT,
            dataset_version TEXT,
            risk_severity_result TEXT,
            first_aid_protocol_id TEXT,
            ambulance_id TEXT,
            referral_id TEXT,
            doctor_id TEXT,
            final_doctor_assessment TEXT,
            final_outcome TEXT
        )
        """)
        
        # Emergency dataset table
        c.execute("""
        CREATE TABLE IF NOT EXISTS emergency_dataset (
            case_id TEXT PRIMARY KEY,
            emergency_category TEXT,
            emergency_condition TEXT,
            symptoms TEXT,
            red_flag_symptoms TEXT,
            severity_level TEXT,
            first_aid_protocol TEXT,
            ambulance_required INTEGER,
            required_specialization TEXT,
            hospital_specialization TEXT,
            emergency_protocol_id TEXT,
            source TEXT,
            dataset_version TEXT,
            last_updated TEXT
        )
        """)
        
        conn.commit()
        conn.close()
        
        seed_medical_knowledge()
        seed_emergency_dataset()
    except Exception as e:
        print("Error initializing new tables:", e)


def seed_medical_knowledge():
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM medical_knowledge")
        if c.fetchone()[0] == 0:
            import json
            now_str = datetime.now().strftime("%Y-%m-%d")
            
            # Protocols
            protocols = [
                ("protocol", "heart_attack", json.dumps({
                    "type": "Cardiac Emergency (Heart Attack)",
                    "severity": "CRITICAL",
                    "immediate_response": "1. Chew and swallow one full aspirin (325mg) if not allergic.\n2. Keep the patient sitting down, calm, and resting.\n3. Loosen any tight clothing.\n4. Administer CPR if patient becomes unresponsive.",
                    "warnings": "Do NOT leave the patient alone. Do NOT let them walk or perform physical activity. Do NOT give them water or food.",
                    "emergency_contact": "Prasad Hospital Cardiac Line: +91-4455-6677",
                    "ambulance_action": "High-priority cardiac ALS ambulance dispatched."
                }), "1.0", now_str),
                ("protocol", "stroke", json.dumps({
                    "type": "Neurological Emergency (Stroke)",
                    "severity": "CRITICAL",
                    "immediate_response": "1. Perform the FAST test (Face drooping, Arm weakness, Speech difficulty, Time to call).\n2. Keep the patient lying on their side with head elevated.\n3. Monitor breathing and airway.",
                    "warnings": "Do NOT give the patient aspirin or ibuprofen (it could worsen hemorrhagic stroke). Do NOT give them food or drink.",
                    "emergency_contact": "Prasad Hospital Stroke Center: +91-4455-6688",
                    "ambulance_action": "Mobile Stroke Unit dispatched with neuro team."
                }), "1.0", now_str),
                ("protocol", "asthma", json.dumps({
                    "type": "Respiratory Emergency (Severe Asthma/COPD)",
                    "severity": "HIGH",
                    "immediate_response": "1. Help the patient sit upright immediately.\n2. Assist them in using their rescue inhaler (Albuterol) - 2 to 6 puffs.\n3. Encourage slow, deep breathing.",
                    "warnings": "Do NOT force the patient to lie down. Do NOT leave them alone.",
                    "emergency_contact": "Prasad Hospital Pulmonary Line: +91-4455-6699",
                    "ambulance_action": "Respiratory emergency vehicle dispatched."
                }), "1.0", now_str)
            ]
            
            c.executemany("""
            INSERT INTO medical_knowledge (category, key_name, value_data, version, last_validated)
            VALUES (?, ?, ?, ?, ?)
            """, protocols)
            conn.commit()
        conn.close()
    except Exception as e:
        print("Error seeding medical knowledge:", e)


def save_emergency(emergency_id, patient_id, patient_name, emergency_type, lat, lon, address, severity, status, assigned_doctor, first_aid=""):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute("SELECT 1 FROM emergencies WHERE emergency_id=?", (emergency_id,))
        if c.fetchone():
            c.execute("""
            UPDATE emergencies 
            SET status=?, lat=?, lon=?, address=?, assigned_doctor=?, first_aid_provided=?, detection_time=?
            WHERE emergency_id=?
            """, (status, lat, lon, address, assigned_doctor, first_aid, now, emergency_id))
        else:
            c.execute("""
            INSERT INTO emergencies 
            (emergency_id, patient_id, patient_name, emergency_type, detection_time, lat, lon, address, severity, status, ambulance_status, ambulance_vehicle, assigned_doctor, first_aid_provided, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (emergency_id, patient_id, patient_name, emergency_type, now, lat, lon, address, severity, status, 'Requested', 'TBD', assigned_doctor, first_aid, now))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving emergency:", e)
        return False


def get_emergencies(patient_id=None):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        if patient_id:
            c.execute("SELECT * FROM emergencies WHERE patient_id=? ORDER BY id DESC", (patient_id,))
        else:
            c.execute("SELECT * FROM emergencies ORDER BY id DESC")
        rows = c.fetchall()
        keys = ["id", "emergency_id", "patient_id", "patient_name", "emergency_type", "detection_time", "lat", "lon", "address", "severity", "status", "ambulance_status", "ambulance_vehicle", "assigned_doctor", "first_aid_provided", "created_at"]
        results = []
        for r in rows:
            results.append(dict(zip(keys, r)))
        conn.close()
        return results
    except Exception as e:
        print("Error getting emergencies:", e)
        return []


def update_emergency_status(emergency_id, status):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("UPDATE emergencies SET status=? WHERE emergency_id=?", (status, emergency_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating emergency status:", e)
        return False


def update_emergency_ambulance_status(emergency_id, amb_status, vehicle):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("UPDATE emergencies SET ambulance_status=?, ambulance_vehicle=? WHERE emergency_id=?", (amb_status, vehicle, emergency_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating emergency ambulance:", e)
        return False


def save_consultation(consultation_id, patient_id, patient_name, symptoms, observations, diagnosis, treatment_plan, follow_up, doctor_id, hospital_id):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO consultations (consultation_id, patient_id, patient_name, symptoms, observations, diagnosis, treatment_plan, follow_up, doctor_id, hospital_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (consultation_id, patient_id, patient_name, symptoms, observations, diagnosis, treatment_plan, follow_up, doctor_id, hospital_id, now))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving consultation:", e)
        return False


def save_prescription(prescription_id, consultation_id, patient_id, drug_name, dose, unit, frequency, route, duration, instructions, doctor_id, hospital_id):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO prescriptions (prescription_id, consultation_id, patient_id, drug_name, dose, unit, frequency, route, duration, instructions, doctor_id, hospital_id, date_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prescription_id, consultation_id, patient_id, drug_name, dose, unit, frequency, route, duration, instructions, doctor_id, hospital_id, now, 'Confirmed'))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving prescription:", e)
        return False


def get_consultations(patient_id):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM consultations WHERE patient_id=? ORDER BY id DESC", (patient_id,))
        rows = c.fetchall()
        keys = ["id", "consultation_id", "patient_id", "patient_name", "symptoms", "observations", "diagnosis", "treatment_plan", "follow_up", "doctor_id", "hospital_id", "created_at"]
        results = [dict(zip(keys, r)) for r in rows]
        conn.close()
        return results
    except Exception as e:
        print("Error getting consultations:", e)
        return []


def get_prescriptions(patient_id):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM prescriptions WHERE patient_id=? ORDER BY id DESC", (patient_id,))
        rows = c.fetchall()
        keys = ["id", "prescription_id", "consultation_id", "patient_id", "drug_name", "dose", "unit", "frequency", "route", "duration", "instructions", "doctor_id", "hospital_id", "date_time", "status"]
        results = [dict(zip(keys, r)) for r in rows]
        conn.close()
        return results
    except Exception as e:
        print("Error getting prescriptions:", e)
        return []


def get_medical_knowledge(category, key_name):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT value_data FROM medical_knowledge WHERE category=? AND key_name=?", (category, key_name))
        row = c.fetchone()
        conn.close()
        if row:
            import json
            return json.loads(row[0])
        return None
    except Exception as e:
        print("Error getting medical knowledge:", e)
        return None


def save_symptom_submission(patient_id, symptoms, emerg_result, em_id, ai_id, dataset_ver, risk, protocol_id, amb_id, ref_id, doc_id):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO symptom_submissions 
        (patient_id, symptom_input, submission_time, emergency_detection_result, emergency_id, ai_analysis_id, dataset_version, risk_severity_result, first_aid_protocol_id, ambulance_id, referral_id, doctor_id, final_doctor_assessment, final_outcome)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, symptoms, now, emerg_result, em_id, ai_id, dataset_ver, risk, protocol_id, amb_id, ref_id, doc_id, 'Pending Doctor Review', 'Active'))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving symptom submission:", e)
        return False


def seed_emergency_dataset():
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM emergency_dataset")
        if c.fetchone()[0] == 0:
            import json
            now_str = datetime.now().strftime("%Y-%m-%d")
            
            cases = [
                (
                    "CASE-001",
                    "Toxicology (Bite)",
                    "Snake Bite",
                    "snake bite, bite, fang marks, swelling, pain",
                    "difficulty breathing, paralysis, bleeding, vision changes",
                    "HIGH",
                    json.dumps({
                        "en": "1. Keep the bitten limb immobile and at or below heart level.\n2. Clean the wound with soap and water.\n3. Do NOT apply a tourniquet or cut the wound.\n4. Do NOT try to suck out the venom.\n5. Keep the patient calm and warm.",
                        "te": "1. కరిచిన భాగాన్ని కదపకుండా గుండె స్థాయి కంటే తక్కువగా ఉంచండి.\n2. గాయాన్ని సబ్బు మరియు నీటితో శుభ్రం చేయండి.\n3. గాయంపై గట్టిగా కట్టవద్దు మరియు గాయాన్ని కొయ్యవద్దు.\n4. విషాన్ని నోటితో పీల్చడానికి ప్రయత్నించవద్దు.\n5. రోగిని ప్రశాంతంగా ఉంచండి.",
                        "hi": "1. काटे गए अंग को स्थिर रखें और दिल के स्तर से नीचे रखें।\n2. घाव को साबुन और पानी से साफ करें।\n3. टूर्निकेट न लगाएं और न ही घाव को काटें।\n4. जहर चूसने की कोशिश न करें।\n5. मरीज को शांत रखें।"
                    }),
                    1,
                    "Toxicology / Emergency Medicine",
                    "General Hospital / Poison Control",
                    "protocol_snake_bite",
                    "World Health Organization (WHO) Guidelines",
                    "v1.0-Validated",
                    now_str
                ),
                (
                    "CASE-002",
                    "Trauma (Bleeding)",
                    "Severe Bleeding",
                    "severe bleeding, bleeding, hemorrhage, cut, wound, accident",
                    "uncontrolled blood loss, dizziness, pale skin, confusion",
                    "HIGH",
                    json.dumps({
                        "en": "1. Apply direct pressure to the wound using a clean cloth.\n2. Elevate the injured area if possible.\n3. Do NOT remove any embedded objects.\n4. Keep pressure applied until medical help arrives.",
                        "te": "1. శుభ్రమైన గుడ్డతో గాయంపై నేరుగా ఒత్తిడిని వర్తింపజేయండి.\n2. వీలైతే దెబ్బతిన్న భాగాన్ని పైకి లేపండి.\n3. గుచ్చుకున్న వస్తువులను తొలగించవద్దు.\n4. సహాయం అందే వరకు ఒత్తిడిని కొనసాగించండి.",
                        "hi": "1. साफ कपड़े से घाव पर सीधा दबाव डालें।\n2. यदि संभव हो तो घायल हिस्से को ऊपर उठाएं।\n3. धंसे हुए सामानों को न निकालें।\n4. चिकित्सा सहायता आने तक दबाव बनाए रखें।"
                    }),
                    1,
                    "Trauma Surgery / Emergency Medicine",
                    "Trauma Care / Emergency Care",
                    "protocol_severe_bleeding",
                    "American Red Cross First Aid",
                    "v1.0-Validated",
                    now_str
                ),
                (
                    "CASE-003",
                    "Cardiology (Cardiac)",
                    "Chest Pain / Suspended Cardiac Emergency",
                    "chest pain, chest pressure, heart pain, left arm pain, jaw pain, sweating",
                    "difficulty breathing, cold sweat, radiating pain to arm/jaw",
                    "HIGH",
                    json.dumps({
                        "en": "1. Sit the patient down and keep them calm.\n2. If not allergic, have them chew a 325mg Aspirin tablet.\n3. Loosen tight clothing.\n4. Be prepared to perform CPR if they become unresponsive.",
                        "te": "1. రోగిని కూర్చోబెట్టి ప్రశాంతంగా ఉంచండి.\n2. అలర్జీ లేకపోతే, 325mg ఆస్పిరిన్ మాత్రను నమలనివ్వండి.\n3. గట్టి బట్టలను సడలించండి.\n4. ఒకవేళ స్పృహ కోల్పోతే CPR చేయడానికి సిద్ధంగా ఉండండి.",
                        "hi": "1. मरीज को बैठाएं और शांत रखें।\n2. एलर्जी न होने पर 325mg एस्पिरिन की गोली चबाने को कहें।\n3. तंग कपड़ों को ढीला करें।\n4. यदि मरीज बेहोश हो जाए तो सीपीआर देने के लिए तैयार रहें।"
                    }),
                    1,
                    "Cardiology / Emergency Medicine",
                    "Cardiac Care Center",
                    "protocol_heart_attack",
                    "AHA ACS Guidelines",
                    "v1.0-Validated",
                    now_str
                ),
                (
                    "CASE-004",
                    "Pulmonology (Respiratory)",
                    "Breathing Difficulty",
                    "breathing difficulty, short of breath, asthma, choking, wheezing",
                    "blue lips, unable to speak in full sentences, silent chest",
                    "HIGH",
                    json.dumps({
                        "en": "1. Help the patient sit upright.\n2. Assist them in using their rescue inhaler if they have one.\n3. Keep them calm and away from triggers like dust or smoke.",
                        "te": "1. రోగిని నిటారుగా కూర్చోబెట్టండి.\n2. వారి వద్ద ఇన్హేలర్ ఉంటే దానిని ఉపయోగించడంలో సహాయపడండి.\n3. ధూళి లేదా పొగ వంటి వాటికి దూరంగా ప్రశాంతంగా ఉంచండి.",
                        "hi": "1. मरीज को सीधा बैठने में मदद करें।\n2. यदि इनहेलर है तो उसका उपयोग करने में सहायता करें।\n3. उन्हें धूल या धुएं से दूर शांत वातावरण में रखें।"
                    }),
                    1,
                    "Pulmonology / Emergency Medicine",
                    "Respiratory Care / General Hospital",
                    "protocol_asthma",
                    "GINA Asthma Guidelines",
                    "v1.0-Validated",
                    now_str
                )
            ]
            
            c.executemany("""
            INSERT INTO emergency_dataset 
            (case_id, emergency_category, emergency_condition, symptoms, red_flag_symptoms, severity_level, first_aid_protocol, ambulance_required, required_specialization, hospital_specialization, emergency_protocol_id, source, dataset_version, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cases)
            conn.commit()
        conn.close()
    except Exception as e:
        print("Error seeding emergency dataset:", e)


def search_emergency_dataset(symptoms_text):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM emergency_dataset")
        rows = c.fetchall()
        conn.close()
        
        keys = ["case_id", "emergency_category", "emergency_condition", "symptoms", "red_flag_symptoms", "severity_level", "first_aid_protocol", "ambulance_required", "required_specialization", "hospital_specialization", "emergency_protocol_id", "source", "dataset_version", "last_updated"]
        
        symptoms_text_lower = str(symptoms_text).lower().strip()
        import re
        
        best_case = None
        best_score = -1
        
        for r in rows:
            case_dict = dict(zip(keys, r))
            keywords = [kw.strip().lower() for kw in case_dict["symptoms"].split(",")]
            score = 0
            
            for kw in keywords:
                if kw == symptoms_text_lower:
                    score += 100
                elif kw in symptoms_text_lower:
                    if len(kw.split()) > 1:
                        score += 50
                    else:
                        if re.search(r'\b' + re.escape(kw) + r'\b', symptoms_text_lower):
                            score += 10
                        else:
                            score += 1
            
            if score > best_score and score > 0:
                best_score = score
                best_case = case_dict
                
        return best_case
    except Exception as e:
        print("Error searching emergency dataset:", e)
        return None


def get_hospitals(city, issue, user_lat=None, user_lon=None):
    try:
        from hospitals import get_hospitals as gh
        return gh(city, issue, user_lat, user_lon)
    except Exception as e:
        print("Error in database wrapper get_hospitals:", e)
        import pandas as pd
        return pd.DataFrame()


def get_nearest_hospitals_sorted(user_lat, user_lon, specialization=None, limit=10):
    """
    Query hospitals_directory, compute Haversine distance from user location,
    optionally filter by specialization keyword, return sorted list (nearest first).
    Falls back to hospitals.csv if DB table is empty.
    """
    import math
    import pandas as pd

    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return round(2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

    results = []

    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()

        # Try hospitals_directory table first
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hospitals_directory'")
        has_table = c.fetchone()

        if has_table:
            c.execute("""
                SELECT hospital_name, address, city, district, state, phone,
                       specialization, emergency_available, latitude, longitude,
                       hospital_id, availability_status
                FROM hospitals_directory
            """)
            rows = c.fetchall()
            conn.close()

            for row in rows:
                name, addr, city, district, state, phone, spec, emerg, lat, lon, h_id, avail = row
                try:
                    lat_f = float(lat)
                    lon_f = float(lon)
                except:
                    continue
                dist = _haversine(user_lat, user_lon, lat_f, lon_f)
                spec_str = str(spec).lower()
                spec_match = True
                if specialization:
                    spec_clean = specialization.lower()
                    spec_match = any(kw in spec_str for kw in spec_clean.split())
                results.append({
                    "name": str(name),
                    "address": str(addr),
                    "city": str(city),
                    "district": str(district) if district else "",
                    "state": str(state) if state else "",
                    "phone": str(phone) if phone else "N/A",
                    "specialization": str(spec),
                    "emergency_available": str(emerg) if emerg else "No",
                    "lat": lat_f,
                    "lon": lon_f,
                    "hospital_id": str(h_id) if h_id else "",
                    "distance": dist,
                    "spec_match": spec_match,
                    "availability_status": str(avail) if avail else "Unknown"
                })
        else:
            conn.close()
            raise Exception("hospitals_directory table not found, trying CSV")

    except Exception as e:
        print("get_nearest_hospitals_sorted DB error:", e)
        # Fallback: read hospitals.csv
        try:
            import os
            csv_path = "hospitals.csv"
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, on_bad_lines="skip")
                df.columns = df.columns.str.strip().str.lower()
                for _, row in df.iterrows():
                    try:
                        lat_f = float(row.get("lat", row.get("latitude", 0)))
                        lon_f = float(row.get("lon", row.get("longitude", 0)))
                    except:
                        continue
                    dist = _haversine(user_lat, user_lon, lat_f, lon_f)
                    spec_str = str(row.get("specialization", "")).lower()
                    spec_match = True
                    if specialization:
                        spec_clean = specialization.lower()
                        spec_match = any(kw in spec_str for kw in spec_clean.split())
                    results.append({
                        "name": str(row.get("name", "")),
                        "address": str(row.get("address", "")),
                        "city": str(row.get("city", "")),
                        "district": "",
                        "state": "",
                        "phone": str(row.get("phone", "N/A")),
                        "specialization": str(row.get("specialization", "")),
                        "emergency_available": "Yes" if "emergency" in spec_str else "No",
                        "lat": lat_f,
                        "lon": lon_f,
                        "hospital_id": "",
                        "distance": dist,
                        "spec_match": spec_match,
                        "availability_status": "Unknown"
                    })
        except Exception as csv_err:
            print("CSV fallback error:", csv_err)

    # Fetch bed info and merge
    try:
        conn2 = sqlite3.connect("hospital.db")
        c2 = conn2.cursor()
        c2.execute("SELECT hospital_name, available_beds, available_icu, emergency_support FROM hospital_beds")
        bed_map = {r[0]: {"available_beds": r[1], "available_icu": r[2], "emergency_support": r[3]} for r in c2.fetchall()}
        conn2.close()
        for h in results:
            b = bed_map.get(h["name"], {})
            h["available_beds"] = b.get("available_beds", "?")
            h["available_icu"] = b.get("available_icu", "?")
            h["emergency_support"] = b.get("emergency_support", h.get("emergency_available", "No"))
    except:
        for h in results:
            h["available_beds"] = "?"
            h["available_icu"] = "?"
            h["emergency_support"] = h.get("emergency_available", "No")

    # Sort: spec_match first, then by distance
    results.sort(key=lambda x: (not x["spec_match"], x["distance"]))
    return results[:limit]


def smart_assign_doctor(hospital_name, specialization):
    """
    Find the best available doctor for a given hospital + specialization.
    Returns a dict with username, name, specialization, qualification, experience,
    availability, image_path. Creates a fallback doctor if none found.
    """
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()

        spec_lower = specialization.lower() if specialization else ""
        spec_keywords = [kw.strip() for kw in spec_lower.replace(",", " ").split() if len(kw.strip()) > 3]

        # 1. Exact match: doctor at this hospital with matching specialization
        for kw in spec_keywords:
            c.execute("""
                SELECT u.username, u.name, u.specialization, u.qualification, u.experience, u.availability,
                       de.image_path
                FROM users u
                LEFT JOIN doctor_extra de ON u.username = de.username
                WHERE u.role='doctor'
                  AND (LOWER(u.hospital_id)=LOWER(?) OR LOWER(u.hospital_id) LIKE ?)
                  AND LOWER(COALESCE(u.specialization,'')) LIKE ?
                  AND LOWER(COALESCE(u.availability,'available')) != 'busy'
                ORDER BY u.experience DESC
                LIMIT 1
            """, (hospital_name, f"%{hospital_name.lower()[:10]}%", f"%{kw}%"))
            row = c.fetchone()
            if row:
                conn.close()
                return _doctor_row_to_dict(row)

        # 2. Any available doctor at this hospital
        c.execute("""
            SELECT u.username, u.name, u.specialization, u.qualification, u.experience, u.availability,
                   de.image_path
            FROM users u
            LEFT JOIN doctor_extra de ON u.username = de.username
            WHERE u.role='doctor'
              AND (LOWER(u.hospital_id)=LOWER(?) OR LOWER(u.hospital_id) LIKE ?)
              AND LOWER(COALESCE(u.availability,'available')) != 'busy'
            ORDER BY u.experience DESC
            LIMIT 1
        """, (hospital_name, f"%{hospital_name.lower()[:10]}%"))
        row = c.fetchone()
        if row:
            conn.close()
            return _doctor_row_to_dict(row)

        # 3. Any doctor globally with matching specialization
        for kw in spec_keywords:
            c.execute("""
                SELECT u.username, u.name, u.specialization, u.qualification, u.experience, u.availability,
                       de.image_path
                FROM users u
                LEFT JOIN doctor_extra de ON u.username = de.username
                WHERE u.role='doctor'
                  AND LOWER(COALESCE(u.specialization,'')) LIKE ?
                  AND LOWER(COALESCE(u.availability,'available')) != 'busy'
                ORDER BY u.experience DESC
                LIMIT 1
            """, (f"%{kw}%",))
            row = c.fetchone()
            if row:
                conn.close()
                return _doctor_row_to_dict(row)

        # 4. Create a new doctor for this hospital dynamically
        import random
        doc_names = ["Rao", "Reddy", "Sharma", "Sastry", "Naidu", "Verma", "Patel", "Murthy"]
        doc_name = f"Dr. {random.choice(['A.','B.','K.','M.','P.','S.','V.'])} {random.choice(doc_names)}"
        clean_hosp = "".join([ch for ch in hospital_name if ch.isalnum()]).lower()
        doc_username = f"doc_{clean_hosp[:8]}_{random.randint(100, 999)}"
        c.execute("""
            INSERT INTO users (username, password, role, name, specialization, qualification, experience, availability, hospital_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_username, "password", "doctor", doc_name, specialization or "Emergency Medicine",
              "MD / MBBS", "10 Years", "Available", hospital_name, "Active"))
        conn.commit()
        conn.close()
        return {
            "username": doc_username,
            "name": doc_name,
            "specialization": specialization or "Emergency Medicine",
            "qualification": "MD / MBBS",
            "experience": "10 Years",
            "availability": "Available",
            "image_path": None
        }
    except Exception as e:
        print("smart_assign_doctor error:", e)
        return {
            "username": "random1",
            "name": "Dr. random",
            "specialization": specialization or "General Physician",
            "qualification": "MBBS",
            "experience": "5 Years",
            "availability": "Available",
            "image_path": None
        }


def _doctor_row_to_dict(row):
    return {
        "username": row[0],
        "name": row[1] if row[1] else row[0],
        "specialization": row[2] if row[2] else "General Physician",
        "qualification": row[3] if row[3] else "MBBS",
        "experience": row[4] if row[4] else "N/A",
        "availability": row[5] if row[5] else "Available",
        "image_path": row[6]
    }


def auto_share_patient_history(patient_username, hospital_name, doctor_username):
    """
    Automatically collect the patient's full clinical profile and share it
    with the selected hospital + doctor. Returns True on success.
    """
    import json
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()

        # Profile
        c.execute("""
            SELECT name, age, gender, phone, blood_group, allergies,
                   chronic_diseases, previous_diseases, previous_medications,
                   previous_reports, emergency_contact, patient_id
            FROM users WHERE username=?
        """, (patient_username,))
        p = c.fetchone()

        # History (last 10 consultations)
        c.execute("""
            SELECT symptoms, result, date, time FROM history
            WHERE name=? ORDER BY id DESC LIMIT 10
        """, (patient_username,))
        history_rows = c.fetchall()
        history_list = [{"symptoms": r[0], "result": r[1], "date": r[2], "time": r[3]} for r in history_rows]

        conn.close()

        payload = {
            "patient_username": patient_username,
            "patient_id": p[11] if p else "N/A",
            "name": p[0] if p else patient_username,
            "age": p[1] if p else "N/A",
            "gender": p[2] if p else "N/A",
            "phone": p[3] if p else "N/A",
            "blood_group": p[4] if p else "N/A",
            "allergies": p[5] if p else "None",
            "chronic_diseases": p[6] if p else "None",
            "previous_diseases": p[7] if p else "None",
            "previous_medications": p[8] if p else "None",
            "previous_reports": p[9] if p else "None",
            "emergency_contact": p[10] if p else "N/A",
            "consultation_history": history_list,
            "shared_to_hospital": hospital_name,
            "shared_to_doctor": doctor_username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        share_patient_history(
            patient_username=patient_username,
            hospital_name=hospital_name,
            doctor_username=doctor_username,
            shared_data=json.dumps(payload)
        )
        return True
    except Exception as e:
        print("auto_share_patient_history error:", e)
        return False


def auto_assign_doctor_for_hospital(hospital_name, specialization):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        
        # 1. Search for existing doctor in this hospital with this specialization
        c.execute("""
        SELECT username 
        FROM users 
        WHERE role='doctor' 
          AND LOWER(hospital_id)=LOWER(?) 
          AND LOWER(specialization) LIKE ?
        """, (hospital_name, f"%{specialization.lower()}%"))
        row = c.fetchone()
        
        if row:
            conn.close()
            return row[0]
            
        # 2. If not found, check if there is *any* doctor in this hospital
        c.execute("""
        SELECT username 
        FROM users 
        WHERE role='doctor' 
          AND LOWER(hospital_id)=LOWER(?)
        """, (hospital_name,))
        row = c.fetchone()
        if row:
            conn.close()
            return row[0]
            
        # 3. If no doctor exists for this hospital, register a new doctor dynamically!
        import random
        doc_names = ["Rao", "Reddy", "Sharma", "Sastry", "Naidu", "Verma", "Patel", "Murthy"]
        doc_name = f"Dr. {random.choice(['A.', 'B.', 'K.', 'M.', 'P.', 'S.', 'V.'])} {random.choice(doc_names)}"
        
        clean_hosp = "".join([char for char in hospital_name if char.isalnum()]).lower()
        doc_username = f"doc_{clean_hosp[:8]}_{random.randint(100, 999)}"
        
        c.execute("""
        INSERT INTO users (
            username, password, role, name, specialization, qualification, experience, availability, hospital_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_username, "password", "doctor", doc_name, specialization or "Emergency Medicine", "MD / MBBS", "10 Years", "Available", hospital_name, "Active"
        ))
        conn.commit()
        conn.close()
        return doc_username
    except Exception as e:
        print("Error auto-assigning doctor for hospital:", e)
        return "random1"


def check_medication_safety(patient_id, drug_name):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        
        c.execute("SELECT allergies, chronic_diseases FROM users WHERE patient_id=?", (patient_id,))
        p_row = c.fetchone()
        patient_allergies = p_row[0] if (p_row and p_row[0]) else "None"
        patient_chronic = p_row[1] if (p_row and p_row[1]) else "None"
        
        c.execute("SELECT drug_name FROM prescriptions WHERE patient_id=? AND status='Active'", (patient_id,))
        active_meds = [r[0] for r in c.fetchall()]
        
        allergy_warning = "None"
        interaction_warning = "None"
        contraindication_warning = "None"
        
        if patient_allergies and patient_allergies.lower() != "none":
            c.execute("SELECT allergen, cross_reactive_drugs, safety_warning FROM allergies_safety")
            allergy_rows = c.fetchall()
            for allergen, cross_drugs, warning in allergy_rows:
                if allergen.lower() in patient_allergies.lower():
                    if drug_name.lower() in allergen.lower() or drug_name.lower() in cross_drugs.lower():
                        allergy_warning = f"⚠️ Allergy Warning: Patient is allergic to {allergen}. Cross reactive drugs: {cross_drugs}. Warning: {warning}"
                        break
                        
        for active_drug in active_meds:
            c.execute("""
            SELECT severity, interaction_effect 
            FROM drug_interactions 
            WHERE (LOWER(drug_a)=LOWER(?) AND LOWER(drug_b)=LOWER(?))
               OR (LOWER(drug_a)=LOWER(?) AND LOWER(drug_b)=LOWER(?))
            """, (drug_name, active_drug, active_drug, drug_name))
            int_row = c.fetchone()
            if int_row:
                interaction_warning = f"⚠️ Drug Interaction ({int_row[0]}): Interaction between {drug_name} and current medicine {active_drug}. Effect: {int_row[1]}"
                break
                
        if patient_chronic and patient_chronic.lower() != "none":
            c.execute("""
            SELECT severity_level, contraindication_details, condition 
            FROM contraindications 
            WHERE LOWER(drug_name)=LOWER(?)
            """, (drug_name,))
            contra_rows = c.fetchall()
            for sev, details, cond in contra_rows:
                if cond.lower() in patient_chronic.lower():
                    contraindication_warning = f"⚠️ Contraindication Warning: Contraindicated for patient's chronic condition: {cond}. Details: {details}"
                    break
                        
        conn.close()
        return {
            "allergy_warning": allergy_warning,
            "interaction_warning": interaction_warning,
            "contraindication_warning": contraindication_warning
        }
    except Exception as e:
        print("Error checking medication safety:", e)
        return {
            "allergy_warning": "None",
            "interaction_warning": "None",
            "contraindication_warning": "None"
        }


def get_doctor_details(username):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT name, specialization, hospital_id FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "name": row[0],
                "specialization": row[1],
                "hospital": row[2]
            }
    except Exception as e:
        print("Error getting doctor details:", e)
    return None


def save_medical_report(report_id, referral_id, patient_id, emergency_id, hospital_id, doctor_id, report_file_path, status, report_version=1):
    try:
        from datetime import datetime
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT OR REPLACE INTO medical_reports 
        (report_id, referral_id, patient_id, emergency_id, hospital_id, doctor_id, report_file_path, report_version, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (report_id, referral_id, patient_id, emergency_id, hospital_id, doctor_id, report_file_path, report_version, status, now, now))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving medical report:", e)
        return False


def get_medical_report_by_referral(referral_id):
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("SELECT * FROM medical_reports WHERE referral_id=? ORDER BY report_version DESC LIMIT 1", (referral_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "report_id": row[0],
                "referral_id": row[1],
                "patient_id": row[2],
                "emergency_id": row[3],
                "hospital_id": row[4],
                "doctor_id": row[5],
                "report_file_path": row[6],
                "report_version": row[7],
                "status": row[8],
                "created_at": row[9],
                "updated_at": row[10]
            }
    except Exception as e:
        print("Error retrieving medical report by referral:", e)
    return None


