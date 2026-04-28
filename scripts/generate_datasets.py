from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    locations_csv = DATA_DIR / "locations.csv"
    roads_csv = DATA_DIR / "roads.csv"

    locations_csv.write_text(
        """osmid,y,x
1,28.6100,77.2000
2,28.6145,77.2065
3,28.6180,77.2140
4,28.6210,77.2210
5,28.6150,77.2280
6,28.6070,77.2220
7,28.6035,77.2125
8,28.6075,77.2045
""",
        encoding="utf-8",
    )

    roads_csv.write_text(
        """u,v,length
1,2,1.2
2,1,1.2
2,3,1.0
3,2,1.0
3,4,1.1
4,3,1.1
4,5,1.0
5,4,1.0
5,6,1.4
6,5,1.4
6,7,1.0
7,6,1.0
7,8,1.2
8,7,1.2
8,1,1.1
1,8,1.1
2,8,0.9
8,2,0.9
3,5,1.3
5,3,1.3
2,6,1.6
6,2,1.6
1,7,1.5
7,1,1.5
2,4,0.9
4,2,0.9
4,3,0.9
3,4,0.9
""",
        encoding="utf-8",
    )

    print(f"✅ Datasets saved to {DATA_DIR}")

if __name__ == "__main__":
    main()
