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
# PAGE 2: GPS SAFETY NAVIGATION – SEARCH-ONLY MODE (NO MANUAL COORDINATES)
# =====================================================================
else:
    st.title("GPS-based Women Safety Navigation")
    st.caption("Search your area to check safety and navigate to the nearest safe zone.")

    # -------------------------------
    # SEARCH DROPDOWN FOR LOCATIONS
    # -------------------------------
    st.subheader("Select Your Location (Police Station Area)")
    selected_area = st.selectbox(
        "Choose a location:",
        df["nm_pol"].unique(),
        index=0
    )

    # Auto-fetch coordinates
    user_row = df[df["nm_pol"] == selected_area].iloc[0]
    user_lat = float(user_row["lat"])
    user_lon = float(user_row["long"])

    st.info(f"Selected Area: **{selected_area}**, Coordinates: ({user_lat:.5f}, {user_lon:.5f})")

    st.write("---")

    # ============================
    # SAFETY ANALYSIS BUTTON
    # ============================
    if st.button("Analyse My Location"):
        nearest = find_nearest_location(df, user_lat, user_lon)
        safe = find_nearest_safe_locations(df, user_lat, user_lon, top_n=3)

        # STORE IN SESSION STATE
        st.session_state["analysis_done"] = True
        st.session_state["nearest"] = nearest
        st.session_state["safe"] = safe
        st.session_state["user_lat"] = user_lat
        st.session_state["user_lon"] = user_lon

    # ============================
    # SHOW ANALYSIS RESULTS
    # ============================
    if st.session_state.get("analysis_done", False):

        nearest = st.session_state["nearest"]
        safe = st.session_state["safe"]

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
        st.dataframe(
            safe[["nm_pol", "area", "risk_level", "risk_score", "distance_km"]]
        )

        # Best safe location
        dest = safe.iloc[0]
        dest_lat = float(dest["lat"])
        dest_lon = float(dest["long"])

        st.session_state["dest_lat"] = dest_lat
        st.session_state["dest_lon"] = dest_lon

        st.write("---")
        st.subheader("Generate Safe Route")

        routing_engine = st.radio("Routing Engine", ["OSMnx", "Mapbox"])
        mapbox_token = ""

        if routing_engine == "Mapbox":
            mapbox_token = st.text_input(
                "Mapbox Token", value=os.getenv("MAPBOX_TOKEN", "")
            )

        # ======================================
        # ROUTE GENERATION BUTTON
        # ======================================
        if st.button("Generate Route"):

            user_lat = st.session_state["user_lat"]
            user_lon = st.session_state["user_lon"]
            dest_lat = st.session_state["dest_lat"]
            dest_lon = st.session_state["dest_lon"]

            st.session_state["route_generated"] = False
            route = None

            if routing_engine == "OSMnx":
                try:
                    route = get_route_osmnx(user_lat, user_lon, dest_lat, dest_lon)
                except Exception as e:
                    st.error(f"Routing failed: {e}")

            else:
                route = get_route_mapbox(user_lat, user_lon, dest_lat, dest_lon, mapbox_token)

            if route:
                st.session_state["route_generated"] = True
                st.session_state["route_coords"] = route
            else:
                st.error("Failed to generate route.")

    # ======================================
    # SHOW ROUTE MAP
    # ======================================
    if st.session_state.get("route_generated", False):

        route_coords = st.session_state["route_coords"]

        m = folium.Map(
            location=[st.session_state["user_lat"], st.session_state["user_lon"]],
            zoom_start=14
        )

        # markers
        folium.Marker(
            [st.session_state["user_lat"], st.session_state["user_lon"]],
            tooltip="Your Location",
            icon=folium.Icon(color="blue")
        ).add_to(m)

        folium.Marker(
            [st.session_state["dest_lat"], st.session_state["dest_lon"]],
            tooltip="Safer Area",
            icon=folium.Icon(color="green")
        ).add_to(m)

        folium.PolyLine(route_coords, color="green", weight=5).add_to(m)

        html(m._repr_html_(), height=600)
        st.success("Safe route generated successfully!")
