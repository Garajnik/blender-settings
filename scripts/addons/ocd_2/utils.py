import bpy
import math
import bmesh
from mathutils import Vector
from numpy import interp

def get_object_by_name(name):
    return bpy.data.objects[name]

def rename_obj_and_mesh(obj):
    sourceName = obj.name
    meshName = obj.data.name

    if meshName != sourceName:
        if sourceName not in bpy.data.meshes:
            obj.data.name = sourceName
        else:
            if '.' in sourceName:
                base_name, source_number = sourceName.rsplit('.', 1)
                highest_number = int(source_number)
            else:
                base_name = sourceName
                highest_number = 0

            for mesh in bpy.data.meshes:
                if mesh.name.startswith(base_name):
                    try:
                        number = int(mesh.name.split('.')[1])
                        highest_number = max(highest_number, number)
                    except (ValueError, IndexError):
                        pass

            new_name = None
            i = highest_number + 1
            while new_name is None:
                candidate_name = f"{base_name}.{i:03}"
                if candidate_name not in bpy.data.meshes:
                    new_name = candidate_name
                i += 1

            obj.data.name = new_name
            obj.name = new_name

def calculate_graph_values(x, scale_amount, multiplier):
    graph_values = {}
    # strength graph sin
    minS = 0.475
    maxS = 1
    xSq = math.sqrt(x) / 4.2
    sin = math.sin(xSq) * math.sin(xSq)
    amnt = sin * 100
    graph_values['strength_graph'] = interp(amnt, [0, 100], [minS, maxS]) * multiplier

    # exponential
    minM = 0.25
    maxM = 0.94
    exp1 = (-x + 100) / 21.8
    exp2 = math.exp(exp1) * -1 + 100
    graph_values['mid_graph'] = interp(exp2, [0, 100], [minM, maxM])

    # smooth graph sin
    minSm = 0.45
    maxSm = 0.75
    ins2 = xSq * 0.66
    sinus2 = math.sin(ins2) * math.sin(ins2)
    amount2 = sinus2 * 100
    graph_values['smooth_graph'] = interp(amount2, [0, 100], [minSm, maxSm])

    graph_values['minSc'] = 0.01 * multiplier
    maxSc = 0.5 * multiplier
    xSc = (maxSc - graph_values['minSc']) / 100
    graph_values['xSc'] = xSc
    return graph_values

def create_or_get_collection(name):
    if name not in bpy.data.collections:
        collection = bpy.context.blend_data.collections.new(name=name)
        bpy.context.collection.children.link(collection)
    else:
        collection = bpy.data.collections[name]
    return collection

def create_or_get_texture(name, texture_type):
    if name not in bpy.data.textures:
        texture = bpy.data.textures.new(name=name, type=texture_type)
    else:
        texture = bpy.data.textures[name]
    return texture

def update_props_from_data(props, damaged_col_obj, ocd_tex):
    props.ocd_strength = damaged_col_obj.modifiers["OCD_Displace"].strength
    props.ocd_mid_level = damaged_col_obj.modifiers["OCD_Displace"].mid_level
    props.ocd_smooth = damaged_col_obj.modifiers["OCD_Smooth"].factor
    props.ocd_noise_scale = ocd_tex.noise_scale
    props.ocd_noise_type = ocd_tex.type
    if ocd_tex.type in ["MUSGRAVE", "CLOUDS", "WOOD", "MARBLE"]:
        props.ocd_noise_basis = ocd_tex.noise_basis
    if ocd_tex.type not in ["MUSGRAVE", "CLOUDS", "VORONOI"]:
        props.ocd_turbulence = ocd_tex.turbulence
    props.ocd_contrast = ocd_tex.contrast
    props.ocd_brightness = ocd_tex.intensity
    props.ocd_voxel_size = damaged_col_obj.modifiers["OCD_remesh"].voxel_size
    props.ocd_voxel_size_02 = damaged_col_obj.modifiers["OCD_remesh_02"].voxel_size

def find_mesh_errors(context):
    bad_objects = []
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            # Create a BMesh object and get mesh data
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()

            # Check for edges with only one linked face
            for edge in bm.edges:
                if len(edge.link_faces) == 1:
                    bad_objects.append(obj)
                    break
                        
            # Cleanup the BMesh object
            bmesh.update_edit_mesh(obj.data)
            bpy.ops.object.mode_set(mode='OBJECT')

    # Now select all the bad objects 
    for obj in context.selected_objects:
        if obj in bad_objects:
            obj.select_set(True)
        else:
            obj.select_set(False)
    return bad_objects