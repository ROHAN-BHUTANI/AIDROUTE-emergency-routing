import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

def load_districts():
    # Create 5 dummy districts as squares with names
    districts = [
        {'district_name': 'Dehradun', 'geometry': Polygon([(77.9,30.1),(78.0,30.1),(78.0,30.2),(77.9,30.2)])},
        {'district_name': 'Haridwar', 'geometry': Polygon([(78.0,29.9),(78.1,29.9),(78.1,30.0),(78.0,30.0)])},
        {'district_name': 'Nainital', 'geometry': Polygon([(79.4,29.2),(79.5,29.2),(79.5,29.3),(79.4,29.3)])},
        {'district_name': 'Almora', 'geometry': Polygon([(79.6,29.6),(79.7,29.6),(79.7,29.7),(79.6,29.7)])},
        {'district_name': 'Rishikesh', 'geometry': Polygon([(78.3,30.1),(78.4,30.1),(78.4,30.2),(78.3,30.2)])}
    ]
    gdf = gpd.GeoDataFrame(districts, crs='EPSG:4326')
    return gdf

def load_risk_scores():
    # Dummy risk scores 0-1
    return pd.DataFrame({
        'district_name': ['Dehradun', 'Haridwar', 'Nainital', 'Almora', 'Rishikesh'],
        'risk_score': [0.3, 0.7, 0.6, 0.8, 0.5]
    })

def load_demand():
    # Dummy demand (e.g., affected population)
    return pd.DataFrame({
        'district_name': ['Dehradun', 'Haridwar', 'Nainital', 'Almora', 'Rishikesh'],
        'demand': [1000, 5000, 3000, 2000, 4000]
    })

def load_hazard_info():
    # Dummy hazard info
    return pd.DataFrame({
        'hazard_type': ['Flood', 'Landslide', 'Earthquake'],
        'affected_districts': ['Haridwar,Rishikesh', 'Nainital,Almora', 'Dehradun,Nainital'],
        'description': [
            'Heavy monsoon floods',
            'Frequent landslides in hills',
            'Seismic activity recorded'
        ]
    })

def load_graph_and_nodes():
    import networkx as nx

    G = nx.DiGraph()

    # Dummy nodes with lat/lon stored in attributes for mapping
    nodes = {
        1: {'district': 'Dehradun', 'x': 77.95, 'y': 30.15},
        2: {'district': 'Haridwar', 'x': 78.05, 'y': 29.95},
        3: {'district': 'Nainital', 'x': 79.45, 'y': 29.25},
        4: {'district': 'Almora', 'x': 79.65, 'y': 29.65},
        5: {'district': 'Rishikesh', 'x': 78.35, 'y': 30.15},
    }
    for n, attr in nodes.items():
        G.add_node(n, **attr)

    # Dummy edges with length and risk_score
    edges = [
        (1,5, {'length': 10, 'risk_score': 0.4}),
        (5,2, {'length': 15, 'risk_score': 0.7}),
        (2,3, {'length': 40, 'risk_score': 0.8}),
        (3,4, {'length': 20, 'risk_score': 0.9}),
        (1,3, {'length': 45, 'risk_score': 0.6}),
        (5,4, {'length': 50, 'risk_score': 0.5}),
    ]
    G.add_edges_from(edges)

    node_to_district = {n: attr['district'] for n, attr in nodes.items()}

    return G, node_to_district
