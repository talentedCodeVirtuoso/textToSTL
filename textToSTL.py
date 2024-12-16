import numpy as np
import trimesh
import trimesh.transformations as tf
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon
from shapely import affinity
from skimage import measure

def apply_curve_to_mesh(mesh, curve_amplitude, curve_frequency):
    vertices = mesh.vertices.copy()
    for i, v in enumerate(vertices):
        x, y, z = v
        # Apply sinusoidal wave deformation based on z-coordinate
        vertices[i, 0] += curve_amplitude * np.sin(curve_frequency * z)  # Adjust x-coordinate
    mesh.vertices = vertices
    return mesh

def text_to_hollow_stl(text, font_path, output_file, font_size, depth, thickness, curve_amplitude=0, curve_frequency=0):
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

    # Ensure multiple polygons (letters) are processed
    polygons = [Polygon(c) for c in contours]

    # Create Outer and Inner Meshes
    outer_meshes = []
    for poly in polygons:
        # Outer surface
        outer = poly.buffer(0)
        inner = affinity.scale(outer, xfact=0.8, yfact=0.8)

        # Extrude to 3D
        outer_3d = trimesh.creation.extrude_polygon(outer, height=depth)
        inner_3d = trimesh.creation.extrude_polygon(inner, height=depth - thickness)

        # Subtract inner from outer to make hollow abd apply curvature if specified
        hollow_mesh = outer_3d.difference(inner_3d)
        if curve_amplitude > 0 and curve_frequency > 0:
            hollow_mesh = apply_curve_to_mesh(hollow_mesh, curve_amplitude, curve_frequency)

        outer_meshes.append(hollow_mesh)

    # Combine All Letters and Export
    final_mesh = trimesh.util.concatenate(outer_meshes)
    # rotation_matrix = tf.rotation_matrix(np.pi, [0, 0, 1])
    # final_mesh.apply_transform(rotation_matrix)
    final_mesh.faces = final_mesh.faces[:, ::-1]
    final_mesh.vertex_normals = final_mesh.vertex_normals
    trimesh.repair.fix_normals(final_mesh)

    final_mesh.export(output_file)
    print(f"STL file saved to {output_file}")

if __name__ == "__main__":
    text = "PHONE"
    font_path = "./fonts/arial.ttf"
    output_file = "hollow_text_phone.stl"
    font_size = 300
    depth = 500
    thickness = 2
    curve_amplitude = 100
    curve_frequency = 0.5

    text_to_hollow_stl(text, font_path, output_file, font_size, depth, thickness, curve_amplitude, curve_frequency)