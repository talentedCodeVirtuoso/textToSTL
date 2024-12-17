import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon, LinearRing
from skimage import measure


def align_mesh_z(mesh):
    """
    Align the mesh so that its minimum z-coordinate becomes 0.
    """
    vertices = mesh.vertices.copy()
    z_min = np.min(vertices[:, 2])  # Find minimum z-coordinate
    vertices[:, 2] -= z_min         # Shift z values so z_min becomes 0
    mesh.vertices = vertices
    return mesh


def bend_mesh(mesh, curve_strength):
    vertices = mesh.vertices.copy()
    x_min = np.min(vertices[:, 0])
    x_max = np.max(vertices[:, 0])
    x_range = x_max - x_min

    # Adjust x-coordinate based on the z value
    for i, vertex in enumerate(vertices):
        if vertex[2] != 0.0:
            x_normalized = (x_max - vertex[0]) / x_range  # Normalize z [0, 1]
            z_shift = curve_strength * (x_normalized ** 2)  # Quadratic curve
            vertices[i, 2] += z_shift  # Adjust x based on z

    mesh.vertices = vertices
    return mesh


def extract_polygons_with_holes(contours):
    """
    Extract polygons and holes from contours.
    Returns a list of shapely Polygons with holes.
    """
    polygons = []
    used_contours = set()
    
    for i, contour in enumerate(contours):
        outer_ring = LinearRing(contour)
        outer_poly = Polygon(outer_ring)
        if not outer_poly.is_valid:
            continue
        
        holes = []
        for j, hole_contour in enumerate(contours):
            if i != j and j not in used_contours:
                hole_ring = LinearRing(hole_contour)
                if outer_ring.contains(hole_ring):
                    holes.append(hole_ring)
                    used_contours.add(j)

        # Create polygon with holes
        poly_with_holes = Polygon(outer_ring, holes)
        polygons.append(poly_with_holes)
        used_contours.add(i)
    
    return polygons


def text_to_hollow_stl(text, font_path, output_file, font_size, depth, thickness, curve_factor):
    # Render Text to Image
    image_size = (5000, 1000)
    image = Image.new("L", image_size, 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    
    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_size = (bbox[2] - bbox[0], bbox[3] - bbox[1]) 
    text_position = ((image_size[0] - text_size[0]) // 2, (image_size[1] - text_size[1]) // 2)
    draw.text(text_position, text, fill=255, font=font)

    # Rasterize Text Outline into Polygons
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image = image.transpose(Image.TRANSPOSE)
    pixels = np.array(image)

    # Detect contours using skimage
    contours = measure.find_contours(pixels, level=0.5)
    polygons_with_holes = extract_polygons_with_holes(contours)

    # Extrude each Letter into 3D hollow meshes
    meshes = []
    for i, poly in enumerate(polygons_with_holes):
        if not poly.is_empty:
            inner = poly.buffer(-thickness)
            if inner.is_empty:
                continue

            # Extrude polygons to 3D
            outer_3d = trimesh.creation.extrude_polygon(poly, height=depth)
            inner_3d = trimesh.creation.extrude_polygon(inner, height=depth - thickness)

            # Subtract inner from outer to make hollow geometry
            hollow_mesh = outer_3d.difference(inner_3d)

            # Align z-axis to baseline
            hollow_mesh = align_mesh_z(hollow_mesh)

            meshes.append(hollow_mesh)

    # Combine all hollow meshes
    final_mesh = trimesh.util.concatenate(meshes)

    # Apply bending transformation
    final_mesh = bend_mesh(final_mesh, curve_factor)

    # Export to STL
    final_mesh.export(output_file)
    print(f"STL file saved to {output_file}")


if __name__ == "__main__":
    text = "PHONE"
    font_path = "./fonts/arial.ttf"
    output_file = "hollow_text_phone.stl"
    font_size = 300
    depth = 100
    thickness = 2
    curve_factor = 200  # Controls the bending curve steepness

    text_to_hollow_stl(text, font_path, output_file, font_size, depth, thickness, curve_factor)