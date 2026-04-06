import osmnx as ox
import geopandas as gpd
import pandas as pd
from bayesian_risk import compute_risk_score  # assumes this function exists and takes amenity as input

def main():
    place = "Uttarakhand, India"
    print(f"Downloading POIs for: {place}")

    tags = {
        'amenity': [
            'hospital', 'clinic', 'shelter', 'fire_station',
            'police', 'school', 'pharmacy', 'community_centre'
        ]
    }

    pois = ox.features_from_place(place, tags)
    print("POI columns available:", pois.columns.tolist())

    # Extract usable columns
    id_col = 'osm_id' if 'osm_id' in pois.columns else 'osmid' if 'osmid' in pois.columns else None
    if id_col is None:
        pois = pois.reset_index()
        id_col = 'id'  # from the MultiIndex ('element', 'id')

    pois = pois[[id_col, 'amenity', 'geometry']].dropna()

    # Compute risk scores
    pois['risk_score'] = pois['amenity'].apply(compute_risk_score)

    pois.to_csv('data/pois.csv', index=False)
    print("✅ POIs with risk_score saved to data/pois.csv")

if __name__ == "__main__":
    main()
