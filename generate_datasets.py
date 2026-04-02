import osmnx as ox
import geopandas as gpd

def main():
    place = "Uttarakhand, India"
    print(f"Downloading road network for: {place}")

    # Get the driving network graph
    G = ox.graph_from_place(place, network_type='drive')

    # Convert graph to GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)

    # edges index is a MultiIndex: (u, v, key)
    # Let's extract 'u' and 'v' from the index
    edges = edges.reset_index()  # will create columns 'u', 'v', 'key'

    # Prepare roads.csv with needed columns
    roads_df = edges[['u', 'v', 'length', 'geometry']].copy()

    # Save roads.csv and nodes.csv
    roads_df.to_csv("roads.csv", index=False)
    nodes.to_csv("locations.csv", index=True)  # nodes have 'osmid' as index

    print("✅ Datasets saved: locations.csv and roads.csv")

if __name__ == "__main__":
    main()
