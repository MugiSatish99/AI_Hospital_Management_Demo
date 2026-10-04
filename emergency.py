import pandas as pd
import os
from difflib import get_close_matches


def load_emergency_dataset():
    try:
        file_path = os.path.join(
            os.path.dirname(__file__),
            "emergency_data.csv"
        )
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print("Emergency CSV Error:", e)
        return None


def normalize_issue(issue):
    issue = str(issue).lower().strip()
    issue_map = {
        "neuro": "neurology",
        "neurology": "neurology",
        "cardio": "cardiology",
        "cardiology": "cardiology",
        "ortho": "orthopedic",
        "orthopedic": "orthopedic",
        "respiratory": "pulmonology",
        "pulmonology": "pulmonology",
        "dermatology": "dermatology",
        "ophthalmology": "ophthalmology",
        "ent": "ent",
        "dental": "dental",
        "emergency": "emergency",
        "general": "general"
    }
    return issue_map.get(issue, issue)


def get_emergency_score(symptoms):
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
    return min(score, 100)


def get_severity_from_score(score):
    if score >= 50:
        return "CRITICAL"
    elif score >= 30:
        return "HIGH"
    elif score >= 15:
        return "MEDIUM"
    return "LOW"


def smart_emergency_rules(symptoms):
    text = str(symptoms).lower().strip()
    score = get_emergency_score(symptoms)
    level = get_severity_from_score(score)
    is_emergency = level in ["HIGH", "CRITICAL"]

    if "chest pain" in text:
        high_signs = [
            "breathing problem",
            "shortness of breath",
            "sweating",
            "dizziness",
            "left arm pain",
            "jaw pain",
            "unconscious",
            "vomiting",
            "low oxygen"
        ]
        for sign in high_signs:
            if sign in text:
                return {
                    "level": "CRITICAL" if score >= 50 else "HIGH",
                    "issue": "cardiology",
                    "emergency": True,
                    "condition": "Possible Cardiac Emergency"
                }

        if "right side" in text:
            return {
                "level": "MEDIUM",
                "issue": "general",
                "emergency": False,
                "condition": "Right Side Chest Pain - Needs Evaluation"
            }

        if "left side" in text:
            return {
                "level": "HIGH",
                "issue": "cardiology",
                "emergency": True,
                "condition": "Left Side Chest Pain - Needs Evaluation"
            }

        return {
            "level": "MEDIUM",
            "issue": "cardiology",
            "emergency": False,
            "condition": "Chest Pain - Needs Further Evaluation"
        }

    if "fever" in text:
        if (
            "unconscious" in text
            or "seizure" in text
            or "breathing problem" in text
            or "stiff neck" in text
            or "confusion" in text
        ):
            return {
                "level": "CRITICAL" if score >= 50 else "HIGH",
                "issue": "emergency",
                "emergency": True,
                "condition": "Fever With Danger Signs"
            }

        if (
            "high fever" in text
            or "continuous fever" in text
            or "fever 3 days" in text
            or "fever for 3 days" in text
        ):
            return {
                "level": "MEDIUM",
                "issue": "general",
                "emergency": False,
                "condition": "High Fever - Needs Medical Evaluation"
            }

        return {
            "level": "LOW",
            "issue": "general",
            "emergency": False,
            "condition": "Fever"
        }

    if "headache" in text or "head pain" in text:
        if (
            "unconscious" in text
            or "seizure" in text
            or "vision loss" in text
            or "weakness one side" in text
            or "stroke" in text
            or "head injury" in text
        ):
            return {
                "level": "CRITICAL" if score >= 50 else "HIGH",
                "issue": "neurology",
                "emergency": True,
                "condition": "Headache With Neurological Danger Signs"
            }

        if (
            "severe headache" in text
            or "dizziness" in text
            or "blurred vision" in text
            or "vomiting" in text
        ):
            return {
                "level": "MEDIUM",
                "issue": "neurology",
                "emergency": False,
                "condition": "Headache - Needs Evaluation"
            }

        return {
            "level": "LOW",
            "issue": "neurology",
            "emergency": False,
            "condition": "Headache"
        }

    # If general score is high/critical, return emergency
    if is_emergency:
        # Determine likely department
        issue = "general"
        if any(w in text for w in ["bone", "fracture", "joint"]):
            issue = "orthopedic"
        elif any(w in text for w in ["stroke", "seizure", "unconscious", "brain"]):
            issue = "neurology"
        elif any(w in text for w in ["chest", "heart", "cardiac"]):
            issue = "cardiology"
        elif any(w in text for w in ["breathing", "oxygen", "lungs", "asthma"]):
            issue = "pulmonology"
        else:
            issue = "emergency"

        return {
            "level": level,
            "issue": issue,
            "emergency": True,
            "condition": "Emergency Condition detected via Scoring"
        }

    return {
        "level": level,
        "issue": "general",
        "emergency": False,
        "condition": "General Condition"
    }


def emergency_dataset_check(symptoms):
    df = load_emergency_dataset()
    text = str(symptoms).lower().strip()

    try:
        rule_result = smart_emergency_rules(text)
        if rule_result and rule_result.get("level") != "LOW":
            return rule_result

        if df is not None:
            df["symptom"] = df["symptom"].astype(str).str.lower().str.strip()
            df["level"] = df["level"].astype(str).str.upper().str.strip()
            df["issue"] = df["issue"].astype(str).str.lower().str.strip()

            for _, row in df.iterrows():
                if row["symptom"] == text:
                    issue = normalize_issue(row["issue"])
                    level = row["level"]
                    if level == "HIGH" and get_emergency_score(text) >= 50:
                        level = "CRITICAL"
                    return {
                        "level": level,
                        "issue": issue,
                        "condition": row["symptom"],
                        "emergency": level in ["HIGH", "CRITICAL"]
                    }

            for _, row in df.iterrows():
                db_symptom = row["symptom"]
                if db_symptom in text:
                    issue = normalize_issue(row["issue"])
                    level = row["level"]
                    if level == "HIGH" and get_emergency_score(text) >= 50:
                        level = "CRITICAL"
                    return {
                        "level": level,
                        "issue": issue,
                        "condition": db_symptom,
                        "emergency": level in ["HIGH", "CRITICAL"]
                    }

            symptom_list = df["symptom"].tolist()
            match = get_close_matches(text, symptom_list, n=1, cutoff=0.82)
            if match:
                row = df[df["symptom"] == match[0]].iloc[0]
                issue = normalize_issue(row["issue"])
                level = row["level"]
                if level == "HIGH" and get_emergency_score(text) >= 50:
                    level = "CRITICAL"
                return {
                    "level": level,
                    "issue": issue,
                    "condition": row["symptom"],
                    "emergency": level in ["HIGH", "CRITICAL"]
                }

    except Exception as e:
        print("Emergency Match Error:", e)

    score = get_emergency_score(text)
    level = get_severity_from_score(score)
    return {
        "level": level,
        "issue": "general",
        "condition": "General Evaluation",
        "emergency": level in ["HIGH", "CRITICAL"]
    }


def check_emergency(symptoms):
    data = emergency_dataset_check(symptoms)
    if data:
        return data.get("emergency", False)
    return False


def get_issue_type(symptoms):
    data = emergency_dataset_check(symptoms)
    if data:
        return normalize_issue(data.get("issue", "general"))
    return "general"


def get_emergency_level(symptoms):
    data = emergency_dataset_check(symptoms)
    if data:
        return data.get("level", "LOW")
    return "LOW"


def get_emergency_condition(symptoms):
    data = emergency_dataset_check(symptoms)
    if data:
        return data.get("condition", "General Condition")
    return "General Condition"