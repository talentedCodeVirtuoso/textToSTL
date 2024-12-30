import bpy
import math
import sys
import locale

def create_cube(name, location, scale, dimensions):
    # Add a cube
    bpy.ops.mesh.primitive_cube_add(location=location)
    cube = bpy.context.object
    cube.name = name

    # Apply scale
    cube.scale = scale

    # Set dimensions (override scale as needed)
    cube.dimensions = dimensions

    return cube

def convert_to_mesh():
    # Get the object
    print("Entering convert to mesh...")
    # Ensure we are in Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Select all objects and convert them to a mesh
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.convert(target='MESH')
    
    # Enter Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Reveal any hidden geometry (just in case)
    bpy.ops.mesh.reveal()
    
    # Deselect all geometry
    bpy.ops.mesh.select_all(action='DESELECT')

    # bpy.ops.mesh.select_face_by_sides(number=4, type='EQUAL', extend=False)  # Select quads (likely top/bottom faces)
    bpy.ops.mesh.hide(unselected=True)  # Hide top and bottom faces to prevent deletion
    
    # Select non-manifold geometry (inner faces and edges)
    bpy.ops.mesh.select_non_manifold()

    # Delete only non-manifold faces
    bpy.ops.mesh.delete(type='ONLY_FACE')
    
    bpy.ops.mesh.reveal()

    # Return to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')


    print(f"Object converted to mesh all...")

def combine_all_objects(new_object_name="CombinedObject"):
    # Select all objects in the scene
    bpy.ops.object.select_all(action='SELECT')
    
    # Set the first object as active
    active_obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = active_obj
    
    # Join all selected objects into one
    bpy.ops.object.join()

    # Rename the combined object
    combined_obj = bpy.context.object
    combined_obj.name = new_object_name
    print(f"Combined all objects into '{new_object_name}'.")
    return combined_obj

def subdivide_combined_object(obj, number_of_cuts):
    # Ensure the object is selected and active
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Switch to Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Select all faces and apply subdivision
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=number_of_cuts)
    
    # Return to Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Subdivided '{obj.name}' with {number_of_cuts} cuts.")

def apply_square_function(obj, scale_factor=1.0):
    # Ensure we are in Object Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the mesh data
    mesh = obj.data
    prev_z = 0.0
    # Iterate over each vertex
    for vertex in mesh.vertices:
        # Access the x and z coordinates
        z = vertex.co.z
        if z != prev_z:
            prev_z = z
        vertex.co.x += scale_factor * ((z * 20 + 0.035 * 20) ** 2)  # Apply the square function
    
    print(f"Applied square function (z = {scale_factor} * x^2) to '{obj.name}'.")

def get_min_z_value(obj):
    # Ensure we're in Object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Access the object's mesh data
    mesh = obj.data
    
    # Get the Z-coordinate of all vertices
    z_values = [vertex.co.z for vertex in mesh.vertices]
    
    # Find and return the minimum Z value
    return min(z_values)

def apply_linear_subtraction_x_to_z(obj, scale_factor=1.0):
    # Ensure we are in Object Mode
    if obj and obj.type == 'MESH':
        min_z = get_min_z_value(obj)
        print(f"The minimum Z-axis value is: {min_z}")
    else:
        print("Please select a mesh object.")

    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Get the mesh data
    mesh = obj.data
    
    # Calculate the mean of the x and z values
    mean_z = sum([vertex.co.z for vertex in mesh.vertices]) / len(mesh.vertices)
    
    # Mark vertices to be removed and adjust z-values for others
    vertices_to_remove = []

    # Iterate over each vertex
    for i, vertex in enumerate(mesh.vertices):
        x = vertex.co.x
        z = vertex.co.z
        
        # If z is greater than the mean z-value, subtract from z based on x
        if z > mean_z:
            vertex.co.z = z - scale_factor * x
            if vertex.co.z < mean_z and mean_z -vertex.co.z > scale_factor * x:
                vertices_to_remove.append(i)
            if vertex.co.z < min_z:
                vertex.co.z = min_z
    
    # Remove marked vertices
    bpy.ops.object.mode_set(mode='EDIT')  # Enter Edit Mode
    bpy.ops.mesh.select_all(action='DESELECT')  # Deselect all vertices
    bpy.ops.object.mode_set(mode='OBJECT')  # Return to Object Mode
    
    # Select vertices to remove
    for v_idx in vertices_to_remove:
        mesh.vertices[v_idx].select = True
    
    # Return to Edit Mode to delete selected vertices
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')  # Back to Object Mode

    print(f"Applied linear subtraction (z = original_z - {scale_factor} * (x - mean_x)) to '{obj.name}'.")

def enable_stl_export_addon():
    # Enable the STL export add-on
    if not bpy.context.preferences.addons.get("io_mesh_stl"):
        bpy.ops.preferences.addon_enable(module="io_mesh_stl")

def export_to_stl(output_path):
    # Ensure the STL export add-on is enabled
    enable_stl_export_addon()

    # Ensure the correct context
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects

    obj = bpy.context.view_layer.objects.active

    if not obj:
        print("No active object found for exporting.")
        return
    
    # Ensure the object is selected
    obj.select_set(True)

    # Export to STL
    bpy.ops.export_mesh.stl(filepath=output_path)
    print(f"STL exported to {output_path}")

def create_text_stl(text, font_path=None, output_path="output.stl"):
    # Clear the current scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Reverse the text to fit the right-to-left reading direction
    hebrew_text = text[::-1]  # Reverse the string for right-to-left order

    text_len = float(count_text)

    # Add a text object
    bpy.ops.object.text_add(location=(0, 0, 0))
    text_obj = bpy.context.object
    text_obj.data.body = hebrew_text

    # Update dimensions to get the current size
    bpy.context.view_layer.update()
    current_width = text_obj.dimensions.x
    current_height = text_obj.dimensions.y
    print("current_width:", current_width)
    print("current_height:", current_height)
    # Desired dimensions in millimeters (converted to Blender units, assuming 1 unit = 1 meter)
    desired_width = 0.15  # 150 mm
    desired_height = 0.075  # 75 mm

    # Calculate scaling factors
    scale_x = desired_width / current_width
    scale_y = desired_height / current_height

    # Apply scale to the text object
    text_obj.scale = (scale_x, scale_y, 1.0)

    # Update dimensions after scaling
    bpy.context.view_layer.update()
    updated_width = text_obj.dimensions.x
    updated_height = text_obj.dimensions.y

    print("Updated width:", updated_width)
    print("Updated height:", updated_height)

    # Load a custom font if provided
    if font_path:
        font = bpy.data.fonts.load(font_path)
        text_obj.data.font = font

    # Set extrusion for 3D depth
    text_obj.data.extrude = 0.05

    # Bevel (Round) settings
    text_obj.data.bevel_depth = 0.005  # Bevel depth
    text_obj.data.bevel_resolution = 1 # Adjust bevel smoothness
    # text_obj.data.fill_mode = 'NONE'  # Disable face fill

    # Get the dimensions of the text object
    text_dimensions = text_obj.dimensions

    # Extract width, height, and depth (x, y, z)
    width = text_dimensions.x
    height = text_dimensions.y

    print("text length:", text_len)

    # Create two cubes
    # Cube 1 - located at one corner of the bounding box
    create_cube(
        name="Cube1",
        location=(width / 7 * text_len, height / 8 * 3, 0.0573),  # Adjust based on the text position
        scale=(1, 1, 1),
        dimensions=(0.005, height / 4 * 3, 0.0147)
    )

    # Cube 2 - located at another corner of the bounding box
    create_cube(
        name="Cube2",
        location=(width / 7 * text_len - 0.005 , height / 8 * 3, 0.0573 + 0.009),  # Adjust based on the text position
        scale=(0.075, 0.061, 0.024),
        dimensions=(0.015, height / 4 * 3, 0.00473)
    )
    print("width / 7 * text_len = ", width / 7 * text_len)
    # Cube connector - located at middle of all text
    create_cube(
        name="Connector",
        location=(width / 14 * (text_len + 0.05), height / 2, -0.0256),
        scale=(1, 1, 1),
        dimensions=(width / 7 * text_len - 0.008, 0.0025, 0.0025)
    )

    print("Start converting objects to mesh...")

    # Convert the combined object to mesh
    convert_to_mesh()  # Replace with your object's name

    # Combine all objects into one
    combined_obj = combine_all_objects("CombinedObject")

    # # Subdivide the combined object with 10 cuts
    subdivide_combined_object(combined_obj, 10)

    combined_obj.location = (-0.004, 0.003, 0.073)

    scale = 0.2
    decrease_factor = 0.035 / text_len * 5
    if combined_obj:
        apply_linear_subtraction_x_to_z(combined_obj, scale_factor=decrease_factor)
        apply_square_function(combined_obj, scale_factor=scale)
    else:
        print(f"Object '{combined_obj}' not found.")

    # # Export the text as an STL file
    export_to_stl(output_path)
    print(f"STL file created at {output_path}")


args = sys.argv

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

text_to_convert = args[5]
font_file_path = args[6]
count_text = args[7]
# Customize inputs
# text_to_convert = "PHONE"
output_file_path = f".\\{text_to_convert}.stl"  # Replace with your desired path
# font_file_path = r"D:\WorkSpace\2024_12_15(numpy-stl)\blender\AppleTea-z8R1a.ttf"  # Replace with your font file path if needed

# Run the function
create_text_stl(text_to_convert, font_path=font_file_path, output_path=output_file_path)