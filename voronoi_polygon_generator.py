#!/usr/bin/env python3
import sys
import logging
import os
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from fastkml import kml, Placemark
from fastkml.geometry import Geometry
from pygeoif import geometry as pygeoif_geometry
from shapely.geometry import Point
import simplekml

logging.basicConfig(level=logging.WARNING)

def extract_polygons(features):
    for feature in features:
        if isinstance(feature, kml.Placemark):
            geom = feature.geometry
            if isinstance(geom, pygeoif_geometry.Polygon):
                return feature.name, geom
            elif isinstance(geom, Geometry):
                inner_geom = geom.geometry
                if isinstance(inner_geom, pygeoif_geometry.Polygon):
                    return feature.name, inner_geom
        if hasattr(feature, 'features'):
            result = extract_polygons(feature.features())
            if result:
                return result
    return None, None

def compute_centroid(kml_path):
    with open(kml_path, 'rb') as file:
        doc = file.read()

    k = kml.KML()
    k.from_string(doc)

    features = list(k.features())
    name, polygon = extract_polygons(features)
    if not polygon:
        raise ValueError("The KML file does not contain a Polygon.")

    # Convert pygeoif.geometry.Polygon to shapely.geometry.Polygon
    exterior_coords = list(polygon.exterior.coords)
    poly = Polygon(exterior_coords)
    centroid = poly.centroid
    return name, centroid.x, centroid.y, k

def generate_crosshair_icon(icon_path):
    # Generate a crosshair as an icon
    fig, ax = plt.subplots(figsize=(0.5, 0.5), dpi=100)
    ax.plot([0.1, 0.9], [0.5, 0.5], color='yellow', linewidth=2)  # Horizontal line
    ax.plot([0.5, 0.5], [0.1, 0.9], color='yellow', linewidth=2)  # Vertical line
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    plt.savefig(icon_path, transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

def add_placemark_with_icon(kml_path, name, latitude, longitude):
    # Generate the crosshair icon and save to a file
    icon_path = os.path.join(os.path.dirname(kml_path), "centroid_crosshair.png")
    generate_crosshair_icon(icon_path)

    # Create a new KML object to add the placemark with the custom icon
    kml_obj = simplekml.Kml()
    placemark = kml_obj.newpoint(name=" ", coords=[(longitude, latitude)])
    placemark.description = f"{name} centroid"
    placemark.style.iconstyle.icon.href = icon_path
    placemark.style.iconstyle.scale = 1.2  # Adjust the size of the icon

    # Save the placemark KML file separately
    title = os.path.splitext(os.path.basename(kml_path))[0]
    centroid_kml_path = os.path.join(os.path.dirname(kml_path), f"{title}_centroid.kml")
    kml_obj.save(centroid_kml_path)
    print(f"Centroid placemark saved as {centroid_kml_path}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        kml_path = sys.argv[1]
    else:
        kml_path = input("Enter kml location: ")

    try:
        name, centroid_x, centroid_y, k = compute_centroid(kml_path)
        # Print centroid in a Google Earth compatible format with altitude 0
        print(f"{centroid_y},{centroid_x}")
        # Add a Placemark with crosshair icon to a new KML
        add_placemark_with_icon(kml_path, name, centroid_y, centroid_x)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)
