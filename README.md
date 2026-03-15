# Philadelphia Property & Rooftop Area Lookup

A comprehensive tool to calculate precise **Lot Areas** and **Building Rooftop Areas** for any Philadelphia property. It uses official city data sources and performs advanced spatial clipping to ensure rooftop readings are limited strictly to the property boundaries (the "Yellow Area").

---

## 🌟 Key Features

- **Rooftop Area (Clipped)**: Calculates the exact area of building footprints *inside* the property lot lines.
- **"Yellow Area" Precision**: Uses spatial intersection (Turf.js) to trim buildings that span across multiple lots, ensuring you only measure what belongs to your parcel.
- **Vertex Breakdown Tables**: Generates detailed, vertex-by-vertex coordinate tables with segment distances in feet—matching the Philadelphia Atlas measurement tool.
- **Official Atlas Styling**: A premium web interface with the official Philadelphia ArcGIS map theme, including house numbers and city-accurate parcel highlights.
- **Hybrid Search**: Locates buildings using OPA numbers (primary) and spatial point-in-polygon lookups (fallback) for 100% coverage.

---

## 📂 Project Structure

| File | Purpose |
|------|---------|
| `index.html` | **Main Web App**: Premium interface with map, breakdown tables, and real-time calculations. |
| `philly_lot_area.py`| **CLI Python Script**: Batch processor for calculating lot and rooftop areas for many addresses at once. |
| `addresses.txt` | Input file for batch processing in the Python script. |
| `requirements.txt` | Python dependencies (`requests`, `shapely`, `pyproj`). |

---

## 🚀 Getting Started

### 1. Web Frontend (Recommended)
Simply open `index.html` in any modern web browser.
- **Search**: Enter any Philadelphia address (e.g., `2140 Princeton Ave`).
- **Results**: See the "Yellow Area" lot boundary, the clipped building footprints, and the individual building coordinate breakdown.
- **Data Source**: Uses live API calls to Philadelphia AIS, PWD Parcels, and L&I Building Footprints.

### 2. Python Script (Batch Lookup)
To process many addresses at once and save to CSV:
1. Install Python from [python.org](https://www.python.org/).
2. Run `pip install -r requirements.txt`.
3. Run:
   ```bash
   python philly_lot_area.py --batch addresses.txt --output results.csv
   ```

---

## 📐 Methodology: The "Yellow Area" Procedure

To ensure the highest accuracy for urban properties (like row houses), the tool follows this technical procedure:

1. **Resolution**: Resolves the address to a unique OPA Number via the **Philadelphia AIS API**.
2. **Parcel Retrieval**: Fetches the parcel polygon from the **PWD Parcels Feature Server**. This polygon defines the "Yellow Area" (Property Boundary).
3. **Building Fetch**: Retrieves building footprints from the **L&I Building Footprints Server** using the OPA number.
4. **Spatial Clipping**: 
   - Uses `turf.buffer(0)` to clean building and lot geometries.
   - Performs a **Spatial Intersection** (Clipping) between the building and the lot.
   - Only the portion of the building *inside* the lot is used for area calculation.
5. **Projection**: All coordinates are projected from WGS84 (GPS) into **EPSG:2272 (PA South State Plane)** using **US Survey Feet** for precise area math via the Shoelace formula.

---

## 📊 Data Sources

- [Philadelphia AIS](https://api.phila.gov/ais/v1/) - Address Verification
- [PWD Parcels](https://opendataphilly.org/) - Property Boundaries
- [L&I Building Footprints](https://opendataphilly.org/dataset/building-footprints) - Rooftop Geometry
- [ArcGIS CityBasemap](https://tiles.arcgis.com/tiles/fLeGjb7u4uXqeF9q/arcgis/rest/services/CityBasemap/MapServer) - Official Map Tiles

---

## 🛠 Tech Stack

- **Frontend**: HTML5, Vanilla CSS3 (Premium Dark/Light UI), JavaScript (ES6+).
- **Mapping**: Leaflet.js (Map engine), Proj4.js (Coordinate projection), Turf.js (Spatial analysis & clipping).
- **Backend API**: Philadelphia OpenData ArcGIS REST Services.
- **Python**: Requests, Shapely (Geometry manipulation), PyProj (Projection).
