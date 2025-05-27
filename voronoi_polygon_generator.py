import os
import sys
import numpy as np
from scipy.spatial import Voronoi
import simplekml
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


def add_bounding_circle(points, num_points=100, margin=10):
    # Calculate the centroid of the original points
    centroid = np.mean(points, axis=0)

    # Calculate the maximum distance from the centroid to any point
    max_distance = np.max(np.linalg.norm(points - centroid, axis=1)) + margin

    # Create points around a circle centered at the centroid
    angles = np.linspace(0, 2 * np.pi, num_points)
    circle_points = np.array([
        [centroid[0] + max_distance * np.cos(angle), centroid[1] + max_distance * np.sin(angle)]
        for angle in angles
    ])

    return np.vstack([points, circle_points])


def generate_custom_icon(icon_path):
    # Generate a crosshair as an icon
    fig, ax = plt.subplots(figsize=(0.5, 0.5), dpi=100)
    ax.plot([0.1, 0.9], [0.5, 0.5], color='red', linewidth=2)
    ax.plot([0.5, 0.5], [0.1, 0.9], color='red', linewidth=2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.savefig(icon_path, transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close(fig)


def parse_kml_placemarks(kml_file):
    """
    Parse a KML file and extract placemark point geometries.
    Returns a list of (name, (lat, lon)).
    """
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    tree = ET.parse(kml_file)
    root = tree.getroot()

    coords = []
    names = []

    for pm in root.findall('.//kml:Placemark', ns):
        # Get the name if present
        name_elem = pm.find('kml:name', ns)
        name = name_elem.text if name_elem is not None else 'Unnamed'

        # Only handle Point geometries
        pt = pm.find('.//kml:Point/kml:coordinates', ns)
        if pt is None or not pt.text:
            # Skip non-point geometries
            continue

        # Coordinates are in 'lon,lat[,alt]' format
        parts = pt.text.strip().split(',')
        lon, lat = float(parts[0]), float(parts[1])

        coords.append((lat, lon))
        names.append(name)

    if not coords:
        print("No valid placemark Point geometries found in the KML.")
        sys.exit(1)

    return names, coords


def generate_voronoi(names, coords, output_file):
    points = np.array(coords)
    points_with_circle = add_bounding_circle(points)

    vor = Voronoi(points_with_circle)
    kml = simplekml.Kml()

    # Bounding box limits for clipping
    min_x, min_y = np.min(points_with_circle, axis=0) - 1
    max_x, max_y = np.max(points_with_circle, axis=0) + 1

    for point, name, region_index in zip(points, names, vor.point_region[:len(points)]):
        region = vor.regions[region_index]
        if len(region) > 0 and not -1 in region:
            poly_points = [vor.vertices[i] for i in region]

            # Clip the polygon to the bounding box
            poly_points = np.clip(poly_points, [min_x, min_y], [max_x, max_y])

            # Convert to KML lat/lon order
            polygon_latlon = [(lat, lon) for lon, lat in poly_points]
            pol = kml.newpolygon(name=name, outerboundaryis=polygon_latlon)
            pol.style.polystyle.color = simplekml.Color.changealphaint(0, simplekml.Color.green)
            pol.style.linestyle.width = 2
            pol.style.linestyle.color = 'ff00ff00'

    # Generate and add custom icon
    icon_path = os.path.splitext(output_file)[0] + '_crosshair.png'
    generate_custom_icon(icon_path)

    for lat, lon, name in [(lat, lon, n) for n, (lat, lon) in zip(names, coords)]:
        pm = kml.newpoint(name=name, coords=[(lon, lat)])
        pm.style.iconstyle.icon.href = icon_path
        pm.style.iconstyle.scale = 1.2

    kml.save(output_file)
    print(f"Voronoi KML written to {output_file}")


def main():
    input_path = input("Enter input .kml or .csv file path: ")
    base, ext = os.path.splitext(input_path)
    ext = ext.lower()

    if ext == '.kml':
        names, coords = parse_kml_placemarks(input_path)
        output_file = base + '_voronoi.kml'
        generate_voronoi(names, coords, output_file)

    elif ext == '.csv':
        import csv
        names = []
        coords = []
        with open(input_path, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row['Latitude'])
                    lon = float(row['Longitude'])
                    names.append(row.get('Location', ''))
                    coords.append((lat, lon))
                except Exception as e:
                    print(f"Skipping invalid row {row}: {e}")
        if not coords:
            print("No valid coordinates found in CSV.")
            sys.exit(1)
        output_file = base + '_voronoi.kml'
        generate_voronoi(names, coords, output_file)

    else:
        print("Unsupported file type. Please provide a .kml or .csv file.")
        sys.exit(1)


if __name__ == '__main__':
    main()