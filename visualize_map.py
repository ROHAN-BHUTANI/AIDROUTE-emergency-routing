import folium
import pandas as pd
import geopandas as gpd
from shapely import wkt

# Load POIs with geometry and risk
pois = pd.read_csv('pois.csv')
pois['geometry'] = pois['geometry'].apply(wkt.loads)

# Load roads with geometry
roads = gpd.read_file('roads.csv') if False else None  # roads.csv is CSV with WKT geometry? We'll convert.

# Since roads.csv geometry is WKT, convert:
roads = pd.read_csv('roads.csv')
roads['geometry'] = roads['geometry'].apply(wkt.loads)
roads_gdf = gpd.GeoDataFrame(roads, geometry='geometry')

# Initialize map centered around mean of POIs
center = [pois.geometry.y.mean(), pois.geometry.x.mean()]
m = folium.Map(location=center, zoom_start=8)

# Add POIs to map colored by risk
for _, row in pois.iterrows():
    color = 'red' if row['risk_score'] > 0.5 else 'green'
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=5,
        color=color,
        fill=True,
        fill_color=color,
        popup=f"Amenity: {row.get('amenity', 'N/A')}<br>Risk: {row['risk_score']:.2f}"
    ).add_to(m)

# Add roads lines
for _, row in roads_gdf.iterrows():
    folium.GeoJson(row['geometry'], 
                   style_function=lambda x: {'color': 'blue', 'weight': 1}).add_to(m)

# Save to HTML
m.save('map.html')
print("Map saved as map.html")
