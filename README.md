# voronoi_polygon_generator

Generates Voronoi polygons from a set of geographic coordinates and exports them in KML format for visualization in applications like Google Earth.

## Features
- Takes a CSV of latitude, longitude, and location names.
- Computes Voronoi polygons with a bounding circle for completeness.
- Outputs results as a KML file, including placemarks for original coordinates.

## Requirements
- Python 3
- Libraries: `numpy`, `scipy`, `simplekml`

Install dependencies with:
```sh
pip install numpy scipy simplekml
```

## Usage
```sh
python voronoi_polygon_generator.py <csv_file_path>
```

- `<csv_file_path>`: Path to a CSV file containing `Latitude`, `Longitude`, and `Location` fields.

## Output
- `voronoi.kml`: KML file containing the generated Voronoi polygons and placemarks.

## Example
CSV format:
```
Latitude,Longitude,Location
34.0522,-118.2437,Los Angeles
40.7128,-74.0060,New York
```

Run the script:
```sh
python voronoi_polygon_generator.py example_coordinates.csv
```

## Notes
- The script adds a bounding circle to ensure the Voronoi diagram covers all input points.
- Polygons are styled with an outlined color and transparent fill for clarity.

