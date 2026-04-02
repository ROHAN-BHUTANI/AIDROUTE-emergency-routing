import pandas as pd

def load_locations(path="data/locations.csv"):
    df = pd.read_csv(path)
    # Expect columns: id, name, latitude, longitude, type (e.g., 'aid_center', 'affected_area')
    return df

def load_roads(path="data/roads.csv"):
    df = pd.read_csv(path)
    # Expect columns: source_id, target_id, distance_km
    return df
