import os
import pandas as pd
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit.components.v1 import html

from gps_utils import load_risk_data, find_nearest_location, find_nearest_safe_locations
from navigation_route import get_route_osmnx, get_route_mapbox


# =========================
# Basic Config
# =========================
st.set_page_config(page_title="Sakhi – Women Safety Analytics", layout="wide")


# =========================
# Data Loading
# =========================
@st.cache_data
def load_data():
    df = load_risk_data("../dataset/final_women_safety_data.csv")
    return df

df = load_data()


# =========================
# Sidebar Menu
# =========================
st.sidebar.title("Women Safety Risk Dashboard")

page = st.sidebar.radio(
    "Select Module",
    ["Risk Analytics", "GPS Safety Navigation"],
)


# =====================================================================
# PAGE 1: RISK ANALYTICS DASHBOARD
# =====================================================================
if page == "Risk Analytics":
    risk_levels = ["Very Low", "Low", "Medium", "High"]
    selected_levels = st.sidebar.multiselect(
        "Select Risk Levels",
        risk_levels,
        default=risk_levels,
    )

    top_n = st.sidebar.slider("Top N locations", 5, 30, 10)
    filtered_df = df[df["risk_level"].isin(selected_levels)]

    st.title("Delhi Women Safety Risk Analytics")
    st.caption("Mini project – Location-wise risk based on crimes against women")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Locations", df.shape[0])
    col2.metric("High Risk Areas", (df["risk_level"] == "High").sum())
    col3.metric("Medium Risk Areas", (df["risk_level"] == "Medium").sum())
    col4.metric(
        "Low/Very Low Risk Areas",
        df["risk_level"].isin(["Low", "Very Low"]).sum(),
    )

    st.write("---")

    st.subheader("🔴 Top Unsafe Locations")
    top_unsafe = (
        df.sort_values(by="risk_score", ascending=False)[
            ["nm_pol", "area", "risk_level", "risk_score"]
        ]
        .head(top_n)
        .reset_index(drop=True)
    )
    st.dataframe(top_unsafe)

    st.subheader("🟢 Top Safe Locations")
    top_safe = (
        df.sort_values(by="risk_score", ascending=True)[
            ["nm_pol", "area", "risk_level", "risk_score"]
        ]
        .head(top_n)
        .reset_index(drop=True)
    )
    st.dataframe(top_safe)

    st.write("---")
    st.subheader("Map View")

    def create_marker_map(data):
        m = folium.Map(location=[28.61, 77.23], zoom_start=10, tiles="cartodbpositron")
        color_map = {
            "Very Low": "green",
            "Low": "lightgreen",
            "Medium": "orange",
            "High": "red",
        }
        for _, row in data.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["long"]],
                radius=7,
                popup=(
                    f"<b>{row['nm_pol']}</b><br>"
                    f"Area: {row['area']}<br>"
                    f"Risk: {row['risk_level']}<br>"
                    f"Score: {row['risk_score']:.2f}"
                ),
                color=color_map[row["risk_level"]],
                fill=True,
                fill_color=color_map[row["risk_level"]],
                fill_opacity=0.8,
            ).add_to(m)
        return m

    tab1, tab2 = st.tabs(["Marker Map", "Risk Heatmap"])
    with tab1:
        html(create_marker_map(filtered_df)._repr_html_(), height=600)

    with tab2:
        hm = folium.Map(location=[28.61, 77.23], zoom_start=10)
        heat_data = filtered_df[["lat", "long", "risk_score"]].values.tolist()
        HeatMap(heat_data).add_to(hm)
        html(hm._repr_html_(), height=600)

    st.caption("Built as a Women Safety Risk Analysis Mini Project.")


# =====================================================================
# PAGE 2: GPS SAFETY NAVIGATION (MANUAL ONLY)
# =====================================================================
else:
    st.title("GPS-based Women Safety Navigation")
    st.caption("Enter your location manually to find the nearest safe zone.")

    user_lat = st.number_input("Enter Latitude", value=28.6139, format="%.6f")
    user_lon = st.number_input("Enter Longitude", value=77.2090, format="%.6f")

    st.write("---")

    if st.button("Analyse My Location"):
        nearest = find_nearest_location(df, user_lat, user_lon)

        st.subheader("Current Zone Assessment")
        st.write(
            f"Nearest police station: **{nearest['nm_pol']} - {nearest['area']}** "
            f"({nearest['distance_km']:.2f} km)"
        )
        st.write(f"Risk Level: **{nearest['risk_level']}**")
        st.write(f"Risk Score: **{nearest['risk_score']:.2f}**")

        if nearest["risk_level"] == "High":
            st.error("⚠ You are in or near a HIGH-RISK zone.")
        elif nearest["risk_level"] == "Medium":
            st.warning("⚠ You are in a MEDIUM-RISK zone.")
        else:
            st.success("✔ You are in a safer zone.")

        st.write("---")

        st.subheader("Nearest Safer Locations")
        safe = find_nearest_safe_locations(df, user_lat, user_lon, top_n=3)
        st.dataframe(
            safe[["nm_pol", "area", "risk_level", "risk_score", "distance_km"]]
        )

        dest = safe.iloc[0]
        dest_lat, dest_lon = dest["lat"], dest["long"]

        st.write("---")
        st.subheader("Generate Safe Route")

        routing_engine = st.radio("Routing Engine", ["OSMnx", "Mapbox"])
        mapbox_token = ""
        if routing_engine == "Mapbox":
            mapbox_token = st.text_input(
                "Mapbox Token", value=os.getenv("MAPBOX_TOKEN", "")
            )

        if st.button("Generate Route"):
            route = None

            if routing_engine == "OSMnx":
                try:
                    route = get_route_osmnx(user_lat, user_lon, dest_lat, dest_lon)
                except Exception as e:
                    st.error(f"Routing failed: {e}")

            else:
                route = get_route_mapbox(user_lat, user_lon, dest_lat, dest_lon, mapbox_token)

            if route:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=14)
                folium.Marker([user_lat, user_lon], icon=folium.Icon(color="blue")).add_to(m)
                folium.Marker([dest_lat, dest_lon], icon=folium.Icon(color="green")).add_to(m)
                folium.PolyLine(route, color="green", weight=5).add_to(m)
                html(m._repr_html_(), height=600)
                st.success("Route generated successfully!")
            else:
                st.error("Failed to generate route.")
