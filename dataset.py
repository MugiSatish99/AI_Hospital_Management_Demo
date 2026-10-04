import pandas as pd
import random
import os

# ================= LOAD DATASET =================

def load_dataset():
    possible_paths = [
        "diseases.csv",
        "data/diseases.csv",
        "dataset.csv"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            return df

    raise FileNotFoundError("diseases.csv file not found")


df = load_dataset()

df["symptoms"] = df["symptoms"].astype(str).str.lower().str.strip()
df["disease"] = df["disease"].astype(str).str.strip()
df["Medicines"] = df["Medicines"].astype(str).str.strip()
df["Advice"] = df["Advice"].astype(str).str.strip()


# ================= FIND DISEASE =================

def find_disease(symptoms):

    symptoms = str(symptoms).lower().strip()

    if not symptoms:
        return {
            "disease": "Unknown Condition",
            "medicine": "Consult Doctor",
            "advice": "Please enter symptoms clearly"
        }

    input_words = set(
        symptoms.replace(",", " ").split()
    )

    best_match = None
    best_score = -1

    for _, row in df.iterrows():

        dataset_symptoms = str(row["symptoms"]).lower().strip()

        dataset_words = set(
            dataset_symptoms.replace(",", " ").split()
        )

        common_words = input_words.intersection(dataset_words)

        score = len(common_words)

        if symptoms == dataset_symptoms:
            score += 100

        elif symptoms in dataset_symptoms:
            score += 50

        elif dataset_symptoms in symptoms:
            score += 30

        if score > best_score:
            best_score = score
            best_match = row

    if best_match is None or best_score <= 0:
        return {
            "disease": "Unknown Condition",
            "medicine": "Consult Doctor",
            "advice": "Symptoms are unclear. Please consult doctor."
        }

    return {
        "disease": best_match["disease"],
        "medicine": best_match["Medicines"],
        "advice": best_match["Advice"]
    }


# ================= RANDOM HOSPITAL =================

def get_random_hospital():

    hospitals = [
        "Apollo Hospital",
        "Care Hospital",
        "Yashoda Hospital",
        "KIMS Hospital",
        "AIG Hospital"
    ]

    return random.choice(hospitals)


# ================= SPECIALIST =================

def get_specialist(disease):

    disease = str(disease).lower()

    mapping = {
        "heart disease": "Cardiologist",
        "hypertension": "Cardiologist",
        "covid-19": "Pulmonologist",
        "asthma": "Pulmonologist",
        "bronchitis": "Pulmonologist",
        "migraine": "Neurologist",
        "diabetes": "Diabetologist",
        "arthritis": "Orthopedic",
        "gastritis": "Gastroenterologist",
        "food poisoning": "Gastroenterologist",
        "viral fever": "General Physician",
        "flu": "ENT Specialist",
        "allergy": "Dermatologist"
    }

    return mapping.get(disease, "General Physician")


# ================= TEST =================

if __name__ == "__main__":

    while True:

        symptoms = input("\nEnter symptoms: ")

        result = find_disease(symptoms)

        print("\n===== RESULT =====")
        print("Disease :", result["disease"])
        print("Medicine:", result["medicine"])
        print("Advice  :", result["advice"])
        print("Doctor  :", get_specialist(result["disease"]))