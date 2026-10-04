import pandas as pd
import os
from utils import calculate_distance


def load_ambulances():
    try:
        path = os.path.join(os.path.dirname(__file__), "ambulance.csv")
        return pd.read_csv(path)
    except Exception as e:
        print("Ambulance CSV Error:", e)
        return pd.DataFrame()


def get_available_ambulance(city, user_lat=None, user_lon=None):
    df = load_ambulances()

    if df.empty:
        return None

    df.columns = df.columns.astype(str).str.lower().str.strip()

    for col in ["ambulance_id", "city", "driver_name", "phone", "lat", "lon", "status"]:
        if col not in df.columns:
            df[col] = ""

    city = str(city).lower().strip()

    df["city"] = df["city"].astype(str).str.lower().str.strip()
    df["status"] = df["status"].astype(str).str.lower().str.strip()

    result = df[
        (df["city"] == city) &
        (df["status"] == "available")
    ].copy()

    if result.empty:
        return None

    result["lat"] = pd.to_numeric(result["lat"], errors="coerce")
    result["lon"] = pd.to_numeric(result["lon"], errors="coerce")

    if user_lat is not None and user_lon is not None:
        result["distance"] = result.apply(
            lambda r: calculate_distance(
                float(user_lat),
                float(user_lon),
                float(r["lat"]),
                float(r["lon"])
            ) if pd.notna(r["lat"]) and pd.notna(r["lon"]) else 9999,
            axis=1
        )
        result = result.sort_values("distance")

    return result.iloc[0].to_dict()


def assign_ambulance(city, user_lat=None, user_lon=None):
    ambulance = get_available_ambulance(city, user_lat, user_lon)

    if not ambulance:
        return None

    return {
        "ambulance_id": ambulance.get("ambulance_id"),
        "driver_name": ambulance.get("driver_name"),
        "phone": ambulance.get("phone"),
        "city": ambulance.get("city"),
        "lat": ambulance.get("lat"),
        "lon": ambulance.get("lon")
    }