import pandas as pd
import os
import sqlite3
import random
from difflib import get_close_matches
from utils import calculate_distance


SPECIALIZATION_MAP = {
    "heart": "cardiology",
    "cardiac": "cardiology",
    "chest pain": "cardiology",

    "brain": "neurology",
    "stroke": "neurology",
    "headache": "neurology",

    "bone": "orthopedic",
    "fracture": "orthopedic",

    "skin": "dermatology",
    "rash": "dermatology",

    "child": "pediatric",
    "baby": "pediatric",

    "pregnancy": "gynecology",
    "women": "gynecology",

    "mental": "psychiatry",
    "depression": "psychiatry",

    "eye": "ophthalmology",

    "kidney": "nephrology",

    "lungs": "respiratory",
    "breathing": "respiratory",

    "accident": "emergency",
    "critical": "emergency",
    "bleeding": "emergency",

    "emergency": "emergency",
    "general": "general"
}


def load_city_alias():
    try:
        file_path = os.path.join(
            os.path.dirname(__file__),
            "city_alias.csv"
        )
        df = pd.read_csv(file_path)
        df.columns = df.columns.astype(str).str.strip().str.lower()
        return df
    except Exception as e:
        print("City Alias Error:", e)
        return pd.DataFrame()


def normalize_city(city):
    city = str(city).lower().strip()
    alias_df = load_city_alias()

    if not alias_df.empty and "alias" in alias_df.columns and "actual_city" in alias_df.columns:
        alias_df["alias"] = (
            alias_df["alias"]
            .astype(str)
            .str.lower()
            .str.strip()
        )
        alias_df["actual_city"] = (
            alias_df["actual_city"]
            .astype(str)
            .str.lower()
            .str.strip()
        )
        match = alias_df[alias_df["alias"] == city]
        if not match.empty:
            return str(match.iloc[0]["actual_city"]).lower().strip()

    return city


def normalize_issue(issue):
    issue = str(issue).lower().strip()
    normalize_map = {
        "heart": "cardiology",
        "cardio": "cardiology",
        "cardiology": "cardiology",
        "brain": "neurology",
        "stroke": "neurology",
        "neuro": "neurology",
        "neurology": "neurology",
        "bone": "orthopedic",
        "fracture": "orthopedic",
        "ortho": "orthopedic",
        "orthopedic": "orthopedic",
        "breath": "respiratory",
        "breathing": "respiratory",
        "respiratory": "respiratory",
        "pulmonology": "respiratory",
        "skin": "dermatology",
        "rash": "dermatology",
        "dermatology": "dermatology",
        "emergency": "emergency",
        "general": "general"
    }

    for key, value in SPECIALIZATION_MAP.items():
        if key in issue:
            return value

    return normalize_map.get(issue, "general")


def fetch_beds_from_db(hospital_name):
    try:
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
    except Exception as e:
        print("Error fetching beds from db:", e)
    
    # Mock fallback
    total = random.choice([30, 50, 100])
    avail = random.randint(1, 15)
    icu = random.choice([5, 10])
    avail_icu = random.randint(0, 4)
    return {
        "total_beds": total,
        "available_beds": avail,
        "total_icu": icu,
        "available_icu": avail_icu,
        "emergency_support": "Yes"
    }


def get_hospitals(city, issue, user_lat=None, user_lon=None):
    try:
        city = normalize_city(city)
        issue = normalize_issue(issue)
        
        conn = sqlite3.connect("hospital.db")
        df = pd.read_sql_query("SELECT * FROM hospitals_directory", conn)
        conn.close()
        
        df.columns = df.columns.astype(str).str.strip().str.lower()
        
        required = [
            "hospital_id", "hospital_name", "hospital_category", "ownership",
            "address", "city", "district", "state", "pincode", "phone",
            "email", "website", "specialization", "emergency_available",
            "ambulance_available", "availability_status", "latitude", "longitude",
            "location_source", "source_id", "last_updated"
        ]
        
        for col in required:
            if col not in df.columns:
                df[col] = ""
                
        df = df[required].copy()
        df = df.rename(columns={"hospital_name": "name", "latitude": "lat", "longitude": "lon"})
        
        df["city"] = df["city"].astype(str).str.lower().str.strip()
        df["specialization"] = df["specialization"].astype(str).str.lower().str.strip()
        
        cities = df["city"].dropna().unique().tolist()
        if city and city not in cities:
            match = get_close_matches(city, cities, n=1, cutoff=0.65)
            if match:
                city = match[0]
                
        ref_lat, ref_lon = None, None
        if user_lat is not None and user_lon is not None:
            ref_lat, ref_lon = float(user_lat), float(user_lon)
        else:
            city_hospitals = df[df["city"] == city]
            if not city_hospitals.empty:
                lats = pd.to_numeric(city_hospitals["lat"], errors="coerce").dropna()
                lons = pd.to_numeric(city_hospitals["lon"], errors="coerce").dropna()
                if not lats.empty and not lons.empty:
                    ref_lat, ref_lon = lats.mean(), lons.mean()
                    
        local_spec_match = df[
            (df["city"] == city) &
            (df["specialization"].astype(str).str.lower().str.contains(issue, na=False, regex=False))
        ]
        
        result_df = pd.DataFrame()
        result_df = pd.concat([result_df, local_spec_match])
        
        if len(result_df) < 5 and ref_lat is not None and ref_lon is not None:
            def calc_dist(row):
                try:
                    return calculate_distance(ref_lat, ref_lon, float(row["lat"]), float(row["lon"]))
                except:
                    return 9999
            df["distance_temp"] = df.apply(calc_dist, axis=1)
            
            nearby_spec_match = df[
                (df["city"] != city) &
                (df["specialization"].astype(str).str.lower().str.contains(issue, na=False, regex=False)) &
                (df["distance_temp"] < 150)
            ].sort_values(by="distance_temp")
            
            result_df = pd.concat([result_df, nearby_spec_match])
            result_df = result_df.drop_duplicates(subset=["name"])
            
        if len(result_df) < 5:
            local_other = df[df["city"] == city]
            result_df = pd.concat([result_df, local_other])
            result_df = result_df.drop_duplicates(subset=["name"])
            
        if result_df.empty:
            result_df = df.copy()
            
        if ref_lat is not None and ref_lon is not None:
            def calc(row):
                try:
                    return calculate_distance(ref_lat, ref_lon, float(row["lat"]), float(row["lon"]))
                except:
                    return 9999
            result_df["distance"] = result_df.apply(calc, axis=1)
        else:
            result_df["distance"] = 9999
            
        result_df["lat"] = pd.to_numeric(result_df["lat"], errors="coerce")
        result_df["lon"] = pd.to_numeric(result_df["lon"], errors="coerce")
        result_df["rating"] = pd.to_numeric(result_df.get("rating", pd.Series([4.0]*len(result_df))), errors="coerce").fillna(4.0)
        result_df = result_df.dropna(subset=["lat", "lon"])
        
        def add_beds_details(row):
            beds_data = fetch_beds_from_db(row["name"])
            return pd.Series([
                beds_data["total_beds"],
                beds_data["available_beds"],
                beds_data["total_icu"],
                beds_data["available_icu"],
                beds_data["emergency_support"]
            ])
            
        result_df[["total_beds", "available_beds", "total_icu", "available_icu", "emergency_support"]] = result_df.apply(add_beds_details, axis=1)
        
        def priority(row):
            spec = str(row["specialization"]).lower()
            city_val = str(row["city"]).lower()
            p = 1
            if issue in spec:
                p += 3
            if city_val == city:
                p += 2
            return p
            
        result_df["priority"] = result_df.apply(priority, axis=1)
        
        def calculate_hospital_score(row):
            priority_val = row["priority"] * 20
            rating_val = row["rating"] * 4
            distance_penalty = row["distance"] * 0.25 if row["distance"] != 9999 else 0
            
            avail_beds = row["available_beds"]
            avail_icu = row["available_icu"]
            emergency_support_bonus = 15 if row["emergency_support"] == "Yes" else 0
            
            bed_score = min(avail_beds * 0.8, 15)
            icu_score = min(avail_icu * 2.5, 20)
            
            return priority_val + rating_val + bed_score + icu_score + emergency_support_bonus - distance_penalty
            
        result_df["score"] = result_df.apply(calculate_hospital_score, axis=1)
        
        result_df = result_df.sort_values(
            by=["priority", "score", "distance"],
            ascending=[False, False, True]
        )
        
        result_df = result_df.drop_duplicates(subset=["name"])
        result_df["distance"] = result_df["distance"].round(2)
        result_df["rating"] = result_df["rating"].round(1)
        
        result_df["latitude"] = result_df["lat"]
        result_df["longitude"] = result_df["lon"]
        
        return result_df[
            [
                "hospital_id",
                "name",
                "address",
                "phone",
                "city",
                "district",
                "state",
                "pincode",
                "specialization",
                "rating",
                "distance",
                "total_beds",
                "available_beds",
                "total_icu",
                "available_icu",
                "emergency_support",
                "lat",
                "lon",
                "latitude",
                "longitude",
                "place_id",
                "location_verified",
                "location_source",
                "last_location_update"
            ]
        ].head(5)
    except Exception as e:
        print("Hospital Error:", e)
        return pd.DataFrame()