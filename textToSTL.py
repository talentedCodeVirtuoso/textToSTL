import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon, LinearRing, MultiPolygon
from skimage import measure

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit
)

class STLTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Text STL Generator")
        self.setGeometry(200, 200, 400, 200)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Input for the name
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter name in Hebrew")
        layout.addWidget(QLabel("Text to convert:"))
        layout.addWidget(self.name_input)

        # Font file selector
        self.font_label = QLabel("No font selected")
        self.font_btn = QPushButton("Select Font")
        self.font_btn.clicked.connect(self.load_font)
        layout.addWidget(self.font_label)
        layout.addWidget(self.font_btn)

        # Generate STL button
        self.generate_btn = QPushButton("Generate STL")
        self.generate_btn.clicked.connect(self.generate_stl)
        layout.addWidget(self.generate_btn)

        self.setLayout(layout)

    def load_font(self):
        font_path, _ = QFileDialog.getOpenFileName(self, "Select Font File", "", "Font Files (*.ttf *.otf)")
        if font_path:
            self.font_label.setText(font_path)
            self.font_path = font_path

    def generate_stl(self):
        text = self.name_input.text()
        font_path = getattr(self, 'font_path', None)
        font_size = 300
        depth = 100
        thickness = 5
        output_file='output_text.stl'
        curve_factor = 200 
        if text and font_path:
            self.text_to_hollow_stl(text, font_path, output_file, font_size, depth, thickness, curve_factor)
        else:
            print("Please enter text and select a font.")

    def align_mesh_z(self, mesh):
        vertices = mesh.vertices.copy()
        z_min = np.min(vertices[:, 2])  # Find minimum z-coordinate
        vertices[:, 2] -= z_min         # Shift z values so z_min becomes 0
        mesh.vertices = vertices
        return mesh

    def extract_polygons_with_holes(self, contours):
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

    def bend_mesh(self, mesh, curve_strength):
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

    def text_to_hollow_stl(self, text, font_path, output_file, font_size, depth, thickness, curve_factor):
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

        # Save or inspect the rendered image
        image.save("debug_text_image.png")
        pixels = np.array(image)
        print(f"Non-zero pixel count: {np.count_nonzero(pixels)}")

        # Detect contours
        contours = measure.find_contours(pixels, level=0.5)
        print(f"Number of contours found: {len(contours)}")

        # Filter out small or invalid contours
        min_contour_length = 10
        contours = [c for c in contours if len(c) >= min_contour_length]
        print(f"Filtered contours count: {len(contours)}")

        # Extract polygons
        polygons_with_holes = self.extract_polygons_with_holes(contours)
        print(f"Number of polygons with holes: {len(polygons_with_holes)}")

        # Filter out invalid or empty polygons
        polygons_with_holes = [poly for poly in polygons_with_holes if poly.is_valid and not poly.is_empty]
        print(f"Valid polygons count: {len(polygons_with_holes)}")

        # Proceed with mesh generation
        meshes = []
        for i, poly in enumerate(polygons_with_holes):
            buffered = poly.buffer(-thickness)
            if isinstance(buffered, Polygon):
                inner = buffered
            elif isinstance(buffered, MultiPolygon):
                inner = max(buffered.geoms, key=lambda p: p.area)  # Choose the largest part
            else:
                continue

            if inner.is_empty:
                continue

            outer_3d = trimesh.creation.extrude_polygon(poly, height=depth)
            inner_3d = trimesh.creation.extrude_polygon(inner, height=depth - thickness)
            hollow_mesh = outer_3d.difference(inner_3d)
            hollow_mesh = self.align_mesh_z(hollow_mesh)
            meshes.append(hollow_mesh)

        if not meshes:
            print("No valid meshes were created. Check your input polygons and parameters.")
            return
        
        # Combine all hollow meshes
        final_mesh = trimesh.util.concatenate(meshes)

        # Apply bending transformation
        final_mesh = self.bend_mesh(final_mesh, curve_factor)

        # Export to STL
        final_mesh.export(output_file)
        print(f"STL file saved to {output_file}")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = STLTool()
    window.show()
    sys.exit(app.exec_())