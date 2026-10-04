import pandas as pd
import random

symptoms = [
    "fever", "cold", "cough", "headache", "nausea",
    "vomiting", "chest pain", "fatigue", "weakness",
    "joint pain", "back pain", "dizziness",
    "shortness of breath", "rash", "itching",
    "stomach pain", "diarrhea", "sore throat",
    "blurred vision", "frequent urination"
]

diseases = [
    "Flu", "Migraine", "Food Poisoning", "Heart Disease",
    "Viral Fever", "Arthritis", "Asthma",
    "Gastritis", "Diabetes", "Allergy",
    "Hypertension", "Bronchitis", "Covid-19"
]

medicines = [
    "Paracetamol", "Ibuprofen", "Aspirin",
    "Metformin", "ORS", "Antibiotics",
    "Antihistamine", "Cough Syrup"
]

advice = [
    "Take rest",
    "Drink more water",
    "Consult doctor",
    "Avoid stress",
    "Maintain diet",
    "Sleep properly",
    "Exercise regularly"
]

data = set()

while len(data) < 5000:
    s = " ".join(random.sample(symptoms, k=random.randint(2,4)))
    d = random.choice(diseases)
    m = random.choice(medicines)
    a = random.choice(advice)

    row = (s, d, m, a)
    data.add(row)

final_data = []
for i, row in enumerate(data, start=1):
    final_data.append({
        "ID": i,
        "symptoms": row[0],
        "Disease": row[1],
        "Medicines": row[2],
        "Advice": row[3]
    })

df = pd.DataFrame(final_data)
df.to_csv("diseases_5000.csv", index=False)

print("✅ 5000 UNIQUE rows created!")