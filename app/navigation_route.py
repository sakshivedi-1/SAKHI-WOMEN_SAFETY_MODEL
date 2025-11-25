# navigation_route.py

from typing import List, Tuple, Optional

import requests


def get_route_osmnx(
    user_lat: float,
    user_lon: float,
    dest_lat: float,
    dest_lon: float,
    dist: int = 3000,
    network_type: str = "walk",
) -> List[Tuple[float, float]]:
    """
    Build a walking route between user location and destination using OSMnx/NetworkX.
    Returns a list of (lat, lon) tuples representing the path.
    """
    import osmnx as ox
    import networkx as nx

    # Build graph around user
    G = ox.graph_from_point((user_lat, user_lon), dist=dist, network_type=network_type)

    origin = ox.nearest_nodes(G, user_lon, user_lat)
    dest = ox.nearest_nodes(G, dest_lon, dest_lat)

    route = nx.shortest_path(G, origin, dest, weight="length")

    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]
    return coords


def get_route_mapbox(
    user_lat: float,
    user_lon: float,
    dest_lat: float,
    dest_lon: float,
    access_token: str,
    profile: str = "walking",
) -> Optional[List[Tuple[float, float]]]:
    """
    Build a route using Mapbox Directions API.
    Returns a list of (lat, lon) tuples or None if request fails.
    """
    if not access_token:
        return None

    base_url = "https://api.mapbox.com/directions/v5/mapbox"
    url = (
        f"{base_url}/{profile}/"
        f"{user_lon},{user_lat};{dest_lon},{dest_lat}"
        f"?geometries=geojson&access_token={access_token}"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        coords = data["routes"][0]["geometry"]["coordinates"]
        # Mapbox returns [lon, lat], convert to (lat, lon)
        return [(lat, lon) for lon, lat in coords]
    except Exception as e:
        print("Mapbox routing error:", e)
        return None
