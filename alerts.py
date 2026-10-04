# alerts.py

import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st
from twilio.rest import Client

def init_alerts():
    if "alerts" not in st.session_state:
        st.session_state.alerts = []

def send_alert(role, message):
    init_alerts()
    alert = {
        "role": role,
        "message": message,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    st.session_state.alerts.append(alert)
    
    # Save to SQLite notifications table
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        INSERT INTO notifications (recipient, type, message, status, time)
        VALUES (?, 'Alert', ?, 'Logged', ?)
        """, (role, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving notification to DB:", e)

def get_alerts(role=None):
    init_alerts()
    if role:
        return [a for a in st.session_state.alerts if a["role"] == role]
    return st.session_state.alerts

def clear_alerts():
    st.session_state.alerts = []

def show_alerts(role):
    alerts = get_alerts(role)
    st.subheader(f"🔔 {role.capitalize()} Alerts")
    if not alerts:
        st.info("No alerts")
        return
    for a in reversed(alerts):
        st.warning(f"{a['time']} - {a['message']}")

def send_email_alert(recipient_email, subject, message):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    status = "Sent"
    if not smtp_email or not smtp_password:
        print(f"[SMTP Fallback Log] Email to {recipient_email} - Subject: {subject} - Msg: {message}")
        status = "Fallback Logged"
    else:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, recipient_email, msg.as_string())
            server.quit()
        except Exception as e:
            print("SMTP Send Error:", e)
            status = f"Send Failed: {str(e)}"
            
    # Save to notifications table
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        INSERT INTO notifications (recipient, type, message, status, time)
        VALUES (?, 'Email', ?, ?, ?)
        """, (recipient_email, f"Subject: {subject} | Msg: {message}", status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving email notification to DB:", e)
        
    return status

def send_sms_alert(phone_number, message):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    
    status = "Sent"
    if not account_sid or not auth_token or not from_number:
        print(f"[Twilio Fallback Log] SMS to {phone_number} - Msg: {message}")
        status = "Fallback Logged"
    else:
        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_number,
                to=phone_number
            )
        except Exception as e:
            print("Twilio Send Error:", e)
            status = f"Send Failed: {str(e)}"
            
    # Save to notifications table
    try:
        conn = sqlite3.connect("hospital.db")
        c = conn.cursor()
        c.execute("""
        INSERT INTO notifications (recipient, type, message, status, time)
        VALUES (?, 'SMS', ?, ?, ?)
        """, (phone_number, message, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error saving SMS notification to DB:", e)
        
    return status

def send_emergency_broadcast(patient_name, symptoms, severity, risk_score, phone=None, email=None):
    message = f"🚨 EMERGENCY CRITICAL ALERT! Patient: {patient_name}. Severity: {severity}. Risk Score: {risk_score}%. Symptoms: {symptoms}."
    
    # Send Streamlit alerts to roles
    send_alert("doctor", message)
    send_alert("staff", message)
    send_alert("admin", message)
    
    # Send Email and SMS if details are provided
    if phone and phone != "N/A" and phone != "Not Assigned":
        send_sms_alert(phone, f"AI Hospital Alert: {message} First-aid guidelines sent to your portal.")
    
    if email and email != "N/A" and email != "Not Assigned":
        send_email_alert(email, "AI Hospital - EMERGENCY ASSISTANCE ALERT", message)

def assign_doctor(symptoms):
    from utils import map_symptom_to_specialization
    from database import get_doctors_by_specialization, get_users
    spec = map_symptom_to_specialization(symptoms)
    doctors = get_doctors_by_specialization(spec)
    if doctors:
        return doctors[0]
    users = get_users()
    docs = [u[1] for u in users if len(u) > 3 and u[3] == "doctor"]
    return docs[0] if docs else "Emergency Duty Doctor"