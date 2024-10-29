import os
import numpy as np
from scipy.spatial import Voronoi
import simplekml
import csv

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

def main():
    csv_file_path = input("Enter .csv location: ")
    locations = []
    coords = []

    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                location = row['Location']
                coords.append([lat, lon])
                locations.append(location)
            except ValueError:
                print(f"Invalid coordinate format in row: {row}")
                sys.exit(1)

    points = np.array(coords)
    points_with_circle = add_bounding_circle(points)

    vor = Voronoi(points_with_circle)
    kml = simplekml.Kml()

    print(f"Voronoi points: {points_with_circle}")
    print(f"Voronoi vertices: {vor.vertices}")
    print(f"Voronoi regions: {vor.regions}")

    # Bounding box limits for clipping
    min_x, min_y = np.min(points_with_circle, axis=0) - 1
    max_x, max_y = np.max(points_with_circle, axis=0) + 1

    for point, location, region_index in zip(points, locations, vor.point_region[:len(points)]):
        region = vor.regions[region_index]
        print(f"Region index: {region_index}, Region: {region}")
        if len(region) > 0 and not -1 in region:
            poly_points = [vor.vertices[i] for i in region]

            # Clip the polygon to the bounding box
            poly_points = np.clip(poly_points, [min_x, min_y], [max_x, max_y])

            polygon_latlon = [(lat, lon) for lon, lat in poly_points]  # Convert coordinates for KML
            pol = kml.newpolygon(name=location, outerboundaryis=polygon_latlon)

            # Set polygon style to outlined only with specific color
            pol.style.polystyle.color = simplekml.Color.changealphaint(0, simplekml.Color.green)  # Fully transparent fill
            pol.style.linestyle.width = 2
            pol.style.linestyle.color = 'ff00ff00'  # Electric, fighter-jet-HUD green (aabbggrr)

            print(f"Polygon for point {point} (Location: {location}): {polygon_latlon}")

    # Adding placemarks for each coordinate
    for coord, location in zip(coords, locations):
        lat, lon = coord
        kml.newpoint(name=location, coords=[(lon, lat)])

    # Save KML file to the same directory as the input CSV, with a modified name
    csv_dir = os.path.dirname(csv_file_path)
    csv_name = os.path.splitext(os.path.basename(csv_file_path))[0]
    kml_file_path = os.path.join(csv_dir, f"{csv_name}_voronoi.kml")
    kml.save(kml_file_path)
    print(f"Voronoi diagram and placemarks exported as {kml_file_path}")

if __name__ == "__main__":
    main()
