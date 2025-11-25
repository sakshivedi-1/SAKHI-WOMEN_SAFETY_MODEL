# gps_utils.py

import math
import pandas as pd
from functools import lru_cache


@lru_cache(maxsize=1)
def load_risk_data(path: str = "../dataset/final_women_safety_data.csv") -> pd.DataFrame:
    """
    Load the final women safety risk data.
    Cached so repeated calls are cheap.
    """
    df = pd.read_csv(path)
    # Basic safety checks
    required_cols = ["nm_pol", "area", "lat", "long", "risk_score", "risk_level"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in risk data: {missing}")
    return df


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine distance between two lat/long points in km.
    """
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_location(df: pd.DataFrame, user_lat: float, user_lon: float) -> pd.Series:
    """
    Find the nearest police-station region to the user's location.
    """
    distances = df.apply(
        lambda row: haversine_km(user_lat, user_lon, row["lat"], row["long"]),
        axis=1
    )
    idx = distances.idxmin()
    nearest = df.loc[idx].copy()
    nearest["distance_km"] = distances[idx]
    return nearest


def find_nearest_safe_locations(
    df: pd.DataFrame,
    user_lat: float,
    user_lon: float,
    safe_levels=("Very Low", "Low"),
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Find the closest 'safe' locations based on risk_level.
    """
    safe_df = df[df["risk_level"].isin(safe_levels)].copy()
    if safe_df.empty:
        return safe_df

    safe_df["distance_km"] = safe_df.apply(
        lambda row: haversine_km(user_lat, user_lon, row["lat"], row["long"]),
        axis=1
    )
    safe_df = safe_df.sort_values("distance_km").head(top_n)
    return safe_df.reset_index(drop=True)
