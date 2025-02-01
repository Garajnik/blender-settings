import bpy
import math
import random
import time
from mathutils import Vector
from numpy import interp
from .import materials, texture
from .utils import get_object_by_name, calculate_graph_values, create_or_get_collection, create_or_get_texture, rename_obj_and_mesh
from .texture import set_texture_properties


def get_voxel_size(context, addon_name):
    addon_name = __name__.partition('.')[0]
    voxel_size = context.preferences.addons[addon_name].preferences.ocd_voxel_size / 1000
    return voxel_size

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

def update_func(self, context):
    name = context.object.name + "_temp"
    props = context.scene.dmgamnt
    scale_amount = props.scale_amount
    sourceName = bpy.context.object.name
    sourceObj = bpy.data.objects[sourceName]
    sourceX = sourceObj.dimensions.x
    sourceY = sourceObj.dimensions.y
    sourceZ = sourceObj.dimensions.z
    x = props.damage_amount
    sourceDim = [sourceX, sourceY, sourceZ]
    multiplier = max(sourceDim)

    #strength graph sin
    minS = 0.475
    maxS = 1 
    xSq = math.sqrt(x)/4.2
    sin = math.sin(xSq) * math.sin(xSq)
    amnt = sin*100
    StrengthGraph = interp(amnt, [0, 100], [minS, maxS]) * multiplier
    
    #exponential
    minM = 0.25
    maxM = 0.94
    exp1 = (-x+100)/21.8
    exp2 = math.exp(exp1) * -1 + 100
    MidGraph = interp(exp2, [0, 100], [minM, maxM]) 
    
    #smooth graph sin
    minSm = 0.45 
    maxSm = 0.75
    ins2 = xSq * 0.66
    sinus2 = math.sin(ins2) * math.sin(ins2)
    amount2 = sinus2*100
    SmoothGraph = interp(amount2, [0, 100], [minSm, maxSm]) 

    sc = scale_amount
    minSc = 0.01 * multiplier
    maxSc = 0.5 * multiplier
    xSc = (maxSc - minSc) / 100
    
    # Check if the object exists
    obj = bpy.data.objects.get(name)
    if obj:
        # Check if the specific modifiers exist
        displace_mod = obj.modifiers.get("OCD_Displace")
        smooth_mod = obj.modifiers.get("OCD_Smooth")

        if displace_mod:
            displace_mod.mid_level = MidGraph
            displace_mod.strength = StrengthGraph / 10

        if smooth_mod:
            smooth_mod.factor = SmoothGraph

    # Update texture properties if texture exists
    ocd_texture = bpy.data.textures.get("OCD_texture")
    if ocd_texture:
        ocd_texture.noise_scale = xSc * sc + minSc
        ocd_texture.type = props.noise_type
        has_noise_basis = hasattr(ocd_texture, "noise_basis")

        # Assuming texture.set_texture_properties is a function you've defined elsewhere
        texture_properties = {
            'MUSGRAVE': {'contrast': 1, 'intensity': 1, 'use_clamp': True, 'noise_basis': 'VORONOI_CRACKLE'},
            'CLOUDS': {'contrast': 1.5, 'intensity': 1, 'noise_basis': 'VORONOI_CRACKLE'},
            'MARBLE': {'contrast': 1.5, 'intensity': 1.5, 'turbulence': 5, 'noise_basis': 'IMPROVED_PERLIN'},
            'VORONOI': {'contrast': 0.5, 'intensity': 1.4, 'noise_basis': 'VORONOI_CRACKLE'},
            'WOOD': {'contrast': 1.5, 'intensity': 2, 'turbulence': 15, 'noise_basis': 'IMPROVED_PERLIN'},
        }
        texture.set_texture_properties(ocd_texture, texture_properties[props.noise_type])

def create_ocd_empties(target_obj):
    # Create "OCD_Rot" empty object
    ocd_rot = bpy.data.objects.new("OCD_Rot", None)
    #ocd_rot.location = target_obj.location  # Set location to match the target object
    
    # Create "OCD_Loc" empty object with random location
    ocd_loc = bpy.data.objects.new("OCD_Loc", None)
    random_offset = [random.uniform(-100, 100) for _ in range(3)]  # Random offset in each axis
    ocd_loc.location = [target_obj.location[i] + random_offset[i] for i in range(3)]

    # Link both empties to the same collection as the target object
    for collection in bpy.data.collections:
        if target_obj.name in collection.objects:
            if ocd_rot.name not in collection.objects:
                collection.objects.link(ocd_rot)
            if ocd_loc.name not in collection.objects:
                collection.objects.link(ocd_loc)

    # Set up the parent-child relationships
    ocd_loc.parent = ocd_rot
    ocd_rot.parent = target_obj

    # Hide the empties from selection
    ocd_rot.hide_select = True
    ocd_loc.hide_select = True

    return ocd_rot, ocd_loc

def prepare_object_for_damage(context, source_obj, damaged_col, voxel_size, multiplier, smooth_graph, strength_graph, mid_graph):
    source_name = source_obj.name
    source_mesh_name = source_obj.data.name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
    context.object.name = f"{source_name}_dmg"
    '''
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.edges_select_sharp(sharpness=0.436332)
    bpy.ops.mesh.mark_sharp()
    bpy.ops.object.editmode_toggle()
    '''
    damage_name = context.object.name
    damage_obj = bpy.data.objects[damage_name]

    bpy.context.object.name = damage_name
    bpy.data.objects[damage_name].data.name = damage_name
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[source_name].select_set(True)
    context.view_layer.objects.active = source_obj
    bpy.ops.object.delete(use_global=False)

    bpy.data.objects[damage_name].select_set(True)
    context.view_layer.objects.active = damage_obj

    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
    bpy.context.object.name = f"{damage_name}_temp"

    target_name = bpy.context.object.name
    target_obj = bpy.data.objects[target_name]
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    #bpy.ops.mesh.select_all(action='DESELECT')
    #bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.editmode_toggle()
    
    for ob in bpy.context.object.users_collection:
        ob.objects.unlink(target_obj)

    bpy.data.collections[damaged_col].objects.link(target_obj)

    context.view_layer.objects.active = target_obj
    target_obj.modifiers.new("OCD_remesh", type='REMESH')
    target_obj.modifiers["OCD_remesh"].voxel_size = voxel_size * multiplier
    target_obj.modifiers["OCD_remesh"].use_smooth_shade = True
    target_obj.modifiers.new("OCD_Smooth", type='SMOOTH')
    target_obj.modifiers["OCD_Smooth"].factor = smooth_graph
    target_obj.modifiers["OCD_Smooth"].iterations = 30
    target_obj.modifiers.new("OCD_Displace", type='DISPLACE')
       
    target_obj.modifiers["OCD_Displace"].strength = strength_graph / 10
    target_obj.modifiers["OCD_Displace"].mid_level = mid_graph
    
    # Ensure target_obj is not deleted when unused by adding a fake user
    target_obj.data.use_fake_user = True

    return {
        'target_obj': target_obj,
        'target_name': target_name,
        'damage_obj': damage_obj,
        'parameters': {
            'voxel_size': voxel_size,
            'multiplier': multiplier,
            'smooth_graph': smooth_graph,
            'strength_graph': strength_graph,
            'mid_graph': mid_graph,
        },
    }

def damage_on(context, self):
    props = context.scene.dmgamnt
    scale_amount = props.scale_amount
    damage_amount = props.damage_amount

    sourceObj = context.object
    rename_obj_and_mesh(sourceObj)
    
    sourceName = bpy.context.object.name
    sourceObj = get_object_by_name(sourceName)
    x = props.damage_amount

    #sourceObj dimensions
    sourceDim = sourceObj.dimensions
    #sourceObj multiplier
    multiplier = max(sourceDim)
    graph_values = calculate_graph_values(x, scale_amount, multiplier)
    strength_graph = graph_values['strength_graph']
    mid_graph = graph_values['mid_graph']
    smooth_graph = graph_values['smooth_graph']
    xSc = graph_values['xSc']
    minSc = graph_values['minSc']
    
    addon_name = __name__.partition('.')[0]
    voxel_size = context.preferences.addons[addon_name].preferences.ocd_voxel_size / 1000
    damaged_col = "OCD_temp"
    damaged_collection = create_or_get_collection(damaged_col)
    damaged_collection.hide_viewport = True
    damaged_collection.hide_render = True
    
    source_obj = context.object
    results = prepare_object_for_damage(context, source_obj, damaged_col, voxel_size, multiplier, smooth_graph, strength_graph, mid_graph)
    target_obj = results['target_obj']
    target_name = results['target_name']
    damage_obj = results['damage_obj']

    if "OCD_texture" not in bpy.data.textures:
        OCD_texture = create_or_get_texture("OCD_texture", 'MUSGRAVE')
        has_noise_basis = hasattr(OCD_texture, "noise_basis")
        if has_noise_basis:
            OCD_texture.noise_basis = 'VORONOI_CRACKLE'
        OCD_texture.musgrave_type = 'HYBRID_MULTIFRACTAL'
        OCD_texture = texture.set_OCD_texture_properties(OCD_texture, props.noise_type, has_noise_basis)
        OCD_texture.noise_scale = xSc * scale_amount + minSc
    else:
        OCD_texture = bpy.data.textures["OCD_texture"]
        has_noise_basis = hasattr(OCD_texture, "noise_basis")
        OCD_texture = texture.set_OCD_texture_properties(OCD_texture, props.noise_type, has_noise_basis)
        OCD_texture.noise_scale = xSc * scale_amount + minSc
        
    bpy.context.object.modifiers.new("OCD_remesh_02", type='REMESH')
    bpy.context.object.modifiers["OCD_remesh_02"].voxel_size = voxel_size * multiplier
    bpy.context.object.modifiers["OCD_remesh_02"].use_smooth_shade = True
    bpy.context.object.modifiers["OCD_Displace"].texture = bpy.data.textures['OCD_texture']

    ocd_rot, ocd_loc = create_ocd_empties(target_obj)
    target_obj.modifiers["OCD_Displace"].texture_coords = 'OBJECT'
    target_obj.modifiers["OCD_Displace"].texture_coords_object = ocd_loc  
    #bpy.context.object.modifiers["OCD_Displace"].texture_coords = 'GLOBAL'
    
    bpy.context.view_layer.objects.active = damage_obj
    bpy.context.active_object.select_set(state=True)
    
    props2 = bpy.context.object.stored_value
    damaged_col_obj = bpy.data.collections[damaged_col].objects[target_name]
    ocd_tex = bpy.data.textures["OCD_texture"]

    update_props_from_data(props2, damaged_col_obj, ocd_tex)

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
   
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
    bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
    bpy.context.object.modifiers["OCD_Boolean"].object = target_obj
    bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
    bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

    #bpy.context.object.data.use_auto_smooth = True
    #bpy.context.object.data.auto_smooth_angle = 1.0472

    bpy.data.meshes[sourceName].use_fake_user = True
    
    obj = context.active_object
    if len(obj.modifiers) == 0:
        self.report({'WARNING'}, "Not a single modifier to Expand/Collapse")
        return {'CANCELLED'}
    is_close = any(mod.show_expanded for mod in obj.modifiers)
    for mod in obj.modifiers:
        mod.show_expanded = not is_close
    return {'FINISHED'}

def ctrl_damage(context, self):
    props = context.scene.dmgamnt
    x = props.damage_amount
    scale_amount = props.scale_amount
    sc = scale_amount
    sourceName = bpy.context.object.name
    sourceObj = bpy.data.objects[sourceName]
    rename_obj_and_mesh(sourceObj)

    #sourceObj dimensions
    sourceX = sourceObj.dimensions.x
    sourceY = sourceObj.dimensions.y
    sourceZ = sourceObj.dimensions.z

    sourceDim = [sourceX, sourceY, sourceZ]
    #sourceObj multiplier
    multiplier = max(sourceDim)

    graph_values = calculate_graph_values(x, scale_amount, multiplier)
    strength_graph = graph_values['strength_graph']
    mid_graph = graph_values['mid_graph']
    smooth_graph = graph_values['smooth_graph']
    xSc = graph_values['xSc']
    minSc = graph_values['minSc']
    
    addon_name = __name__.partition('.')[0]
    voxel_size = context.preferences.addons[addon_name].preferences.ocd_voxel_size / 1000
    damaged_col = "OCD_temp"
    damaged_collection = create_or_get_collection(damaged_col)
    damaged_collection.hide_viewport = True
    damaged_collection.hide_render = True

    source_obj = context.object
    results = prepare_object_for_damage(context, source_obj, damaged_col, voxel_size, multiplier, smooth_graph, strength_graph, mid_graph)
    target_obj = results['target_obj']
    target_name = results['target_name']
    damage_obj = results['damage_obj']
    if "OCD_texture" not in bpy.data.textures:
        OCD_texture = create_or_get_texture("OCD_texture", 'MUSGRAVE')
        has_noise_basis = hasattr(OCD_texture, "noise_basis")
        if has_noise_basis:
            OCD_texture.noise_basis = 'VORONOI_CRACKLE'
        OCD_texture.musgrave_type = 'HYBRID_MULTIFRACTAL'
        OCD_texture = texture.set_OCD_texture_properties(OCD_texture, props.noise_type, has_noise_basis)
        OCD_texture.noise_scale = xSc * scale_amount + minSc
    else:
        OCD_texture = bpy.data.textures["OCD_texture"]
        has_noise_basis = hasattr(OCD_texture, "noise_basis")
        OCD_texture = texture.set_OCD_texture_properties(OCD_texture, props.noise_type, has_noise_basis)
        OCD_texture.noise_scale = xSc * scale_amount + minSc

    bpy.context.object.modifiers.new("OCD_remesh_02", type='REMESH')
    bpy.context.object.modifiers["OCD_remesh_02"].voxel_size = voxel_size * multiplier
    bpy.context.object.modifiers["OCD_remesh_02"].use_smooth_shade = True
    bpy.context.object.modifiers["OCD_Displace"].texture = bpy.data.textures['OCD_texture']
    bpy.context.object.modifiers["OCD_Displace"].texture_coords = 'GLOBAL'
    bpy.context.view_layer.objects.active = damage_obj
    bpy.context.active_object.select_set(state=True)
    
    props2 = bpy.context.object.stored_value
    damaged_col_obj = bpy.data.collections[damaged_col].objects[target_name]
    ocd_tex = bpy.data.textures["OCD_texture"]

    update_props_from_data(props2, damaged_col_obj, ocd_tex)

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
    bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
    bpy.context.object.modifiers["OCD_Boolean"].object = target_obj
    bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
    bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
    bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

    try:
        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.data.auto_smooth_angle = 1.0472
    except AttributeError:
        pass
    
    obj = context.active_object
    if len(obj.modifiers) == 0:
        self.report({'WARNING'}, "Not a single modifier to Expand/Collapse")
        return {'CANCELLED'}
    is_close = any(mod.show_expanded for mod in obj.modifiers)
    for mod in obj.modifiers:
        mod.show_expanded = not is_close
    
    active_obj = context.view_layer.objects.active
    
    # Get the current addon preferences
    addon_name = __name__.partition('.')[0]
    prefs = context.preferences.addons[addon_name].preferences

    # Check the boolean method preference
    use_exact_boolean = prefs.use_exact_boolean

    # Apply and remove modifiers
    active_obj = bpy.context.active_object
    for mod in active_obj.modifiers:
        if mod.name == "OCD_Boolean":
            # If use_exact_boolean is True, set the solver method to Exact
            if use_exact_boolean:
                mod.solver = 'EXACT'
            else:
                mod.solver = 'FAST'
            bpy.ops.object.modifier_apply(modifier=mod.name)

        if mod.type == "EDGE_SPLIT":
            bpy.ops.object.modifier_remove(modifier=mod.name)

    # Add WEIGHTED_NORMAL modifier
    bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
    bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
    
    #materials
    mat_names = ["OUTSIDE", "INSIDE"]
    materials.assign_materials(__name__.partition('.')[0], mat_names)
    
    damageName = bpy.context.object.name
    sourceName = damageName[:-4]
    
    bpy.data.meshes[sourceName].use_fake_user = True
    
    collection_name = "OCD_temp"
    collection = bpy.data.collections[collection_name]

    meshes = set()
    for obj in [o for o in collection.objects if o.type == 'MESH']:
        meshes.add( obj.data )
        bpy.data.objects.remove( obj )
    for mesh in [m for m in meshes]:
        bpy.data.meshes.remove( mesh )
    
    collection = bpy.data.collections.get(collection_name)
    bpy.data.collections.remove(collection)
    active_obj["OCD_applied"] = True  
    return {'FINISHED'}   
    
def multobj_damage(context):
    active_object = context.view_layer.objects.active

    # Initialize the variables to None
    props2 = None
    ocd_strength = ocd_mid_level = ocd_smooth = ocd_noise_scale = None
    ocd_noise_type = ocd_noise_basis = ocd_contrast = ocd_brightness = None
    ocd_voxel_size = ocd_voxel_size_02 = None

    if "stored_value" in active_object:
        props2 = active_object["stored_value"]
        # Store each property in a variable
        ocd_strength = props2.get('ocd_strength')
        ocd_mid_level = props2.get('ocd_mid_level')
        ocd_smooth = props2.get('ocd_smooth')
        ocd_noise_scale = props2.get('ocd_noise_scale')
        ocd_noise_type = props2.get('ocd_noise_type')
        ocd_noise_basis = props2.get('ocd_noise_basis')
        ocd_contrast = props2.get('ocd_contrast')
        ocd_brightness = props2.get('ocd_brightness')
        ocd_voxel_size = props2.get('ocd_voxel_size')
        ocd_voxel_size_02 = props2.get('ocd_voxel_size_02')
        
    props = context.scene.dmgamnt
    x = props.damage_amount
    scale_amount = props.scale_amount
    sc = scale_amount
    sourceName = bpy.context.object.name
    sourceObj = bpy.data.objects[sourceName]
    sourceX = sourceObj.dimensions.x
    sourceY = sourceObj.dimensions.y
    sourceZ = sourceObj.dimensions.z
    sourceDim = [sourceX, sourceY, sourceZ]

    #sourceObj multiplier
    multiplier = 1 if props2 is not None else max(sourceDim)

    graph_values = calculate_graph_values(x, scale_amount, multiplier)
    xSc = graph_values['xSc']
    minSc = graph_values['minSc']
   
    addon_name = __name__.partition('.')[0]
    voxel_size = ocd_voxel_size if ocd_voxel_size is not None else (context.preferences.addons[addon_name].preferences.ocd_voxel_size / 1000)
    strength_graph = ocd_strength * 10 if ocd_strength is not None else graph_values['strength_graph']
    mid_graph = ocd_mid_level if ocd_mid_level is not None else graph_values['mid_graph']
    smooth_graph = ocd_smooth if ocd_smooth is not None else graph_values['smooth_graph']
    
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            print(f"Object {obj.name} is not a mesh. Skipping...")
            continue
        # Skip if object is tagged as damaged
        if "OCD_applied" in obj:
            print(f"Object {obj.name} is already damaged. Skipping...")
            continue
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        # Select the current object
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
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

        damaged_col = "OCD_temp"
        damaged_collection = create_or_get_collection(damaged_col)
        damaged_collection.hide_viewport = True
        damaged_collection.hide_render = True

        source_obj = context.object
        results = prepare_object_for_damage(context, source_obj, damaged_col, voxel_size, multiplier, smooth_graph, strength_graph, mid_graph)
        target_obj = results['target_obj']
        target_name = results['target_name']
        damage_obj = results['damage_obj']
        
        if "OCD_texture" not in bpy.data.textures:
            OCD_texture = create_or_get_texture("OCD_texture", 'MUSGRAVE')
            has_noise_basis = hasattr(OCD_texture, "noise_basis")
            if has_noise_basis:
                OCD_texture.noise_basis = 'VORONOI_CRACKLE'
            OCD_texture.musgrave_type = 'HYBRID_MULTIFRACTAL'
            OCD_texture = texture.set_OCD_texture_properties(OCD_texture, ocd_noise_type or props.noise_type, has_noise_basis)
            OCD_texture.noise_scale = ocd_noise_scale or (xSc * scale_amount + minSc)
        else:
            OCD_texture = bpy.data.textures["OCD_texture"]
            has_noise_basis = hasattr(OCD_texture, "noise_basis")
            OCD_texture = texture.set_OCD_texture_properties(OCD_texture, ocd_noise_type or props.noise_type, has_noise_basis)
            OCD_texture.noise_scale = ocd_noise_scale or (xSc * scale_amount + minSc)

        bpy.context.object.modifiers.new("OCD_remesh_02", type='REMESH')
        bpy.context.object.modifiers["OCD_remesh_02"].voxel_size = voxel_size * multiplier    
        bpy.context.object.modifiers["OCD_remesh_02"].use_smooth_shade = True
        bpy.context.object.modifiers["OCD_Displace"].texture = bpy.data.textures['OCD_texture']
        bpy.context.object.modifiers["OCD_Displace"].texture_coords = 'GLOBAL'
        bpy.context.view_layer.objects.active = damage_obj
        bpy.context.active_object.select_set(state=True)
        
        props2 = bpy.context.object.stored_value
        props2.ocd_strength = bpy.data.collections[damaged_col].objects[target_name].modifiers["OCD_Displace"].strength
        props2.ocd_mid_level = bpy.data.collections[damaged_col].objects[target_name].modifiers["OCD_Displace"].mid_level
        props2.ocd_smooth = bpy.data.collections[damaged_col].objects[target_name].modifiers["OCD_Smooth"].factor
        props2.ocd_noise_scale = bpy.data.textures["OCD_texture"].noise_scale
        props2.ocd_noise_type = bpy.data.textures["OCD_texture"].type
        if bpy.data.textures["OCD_texture"].type in ["MUSGRAVE", "CLOUDS", "WOOD", "MARBLE"]:
            props2.ocd_noise_basis = bpy.data.textures["OCD_texture"].noise_basis
        else:
            pass
        if bpy.data.textures["OCD_texture"].type not in ["MUSGRAVE", "CLOUDS", "VORONOI"]:
            props2.ocd_turbulence = bpy.data.textures["OCD_texture"].turbulence
        else:
            pass
        props2.ocd_contrast = bpy.data.textures["OCD_texture"].contrast
        props2.ocd_brightness = bpy.data.textures["OCD_texture"].intensity
        props2.ocd_voxel_size = bpy.data.collections[damaged_col].objects[target_name].modifiers["OCD_remesh"].voxel_size
        props2.ocd_voxel_size_02 = bpy.data.collections[damaged_col].objects[target_name].modifiers["OCD_remesh_02"].voxel_size

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()

        bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
        bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["OCD_Boolean"].object = target_obj
        bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
        bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
        bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

        try:
            bpy.context.object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 1.0472
        except AttributeError:
            pass
        
        obj = context.active_object
        if len(obj.modifiers) == 0:
            self.report({'WARNING'}, "Not a single modifier to Expand/Collapse")
            return {'CANCELLED'}
        is_close = any(mod.show_expanded for mod in obj.modifiers)
        for mod in obj.modifiers:
            mod.show_expanded = not is_close
        
        active_obj = context.view_layer.objects.active
        
        # Get the current addon preferences
        addon_name = __name__.partition('.')[0]
        prefs = context.preferences.addons[addon_name].preferences

        # Check the boolean method preference
        use_exact_boolean = prefs.use_exact_boolean

        # Apply and remove modifiers
        active_obj = bpy.context.active_object
        for mod in active_obj.modifiers:
            if mod.name == "OCD_Boolean":
                # If use_exact_boolean is True, set the solver method to Exact
                if use_exact_boolean:
                    mod.solver = 'EXACT'
                else:
                    mod.solver = 'FAST'
                bpy.ops.object.modifier_apply(modifier=mod.name)

            if mod.type == "EDGE_SPLIT":
                bpy.ops.object.modifier_remove(modifier=mod.name)

        # Add WEIGHTED_NORMAL modifier
        bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
        
        #materials
        mat_names = ["OUTSIDE", "INSIDE"]
        materials.assign_materials(__name__.partition('.')[0], mat_names)

        damageName = bpy.context.object.name
        sourceName = damageName[:-4]
        bpy.data.meshes[sourceName].use_fake_user = True
        collection_name = "OCD_temp"
        collection = bpy.data.collections[collection_name]
        meshes = set()

        for obj in [o for o in collection.objects if o.type == 'MESH']:
            meshes.add( obj.data )
            bpy.data.objects.remove( obj )

        for mesh in [m for m in meshes]:
            bpy.data.meshes.remove( mesh )

        collection = bpy.data.collections.get(collection_name)
        bpy.data.collections.remove(collection)
        active_obj["OCD_applied"] = True  
        #redraw the viewport
        bpy.ops.wm.redraw_timer(type='DRAW_SWAP', iterations=1)
        # pause
        time.sleep(0.015)  

def damage_off(context):
    obj = context.active_object
    damageName = obj.name
    sourceName = damageName[:-4]
    obj.name = sourceName
    if sourceName in bpy.data.meshes:
        mesh = bpy.data.meshes[sourceName]
        bpy.data.meshes.remove(mesh)
        bpy.data.objects[sourceName].data.name = sourceName

    # Remove specific modifiers
    mods_to_remove = [mod for mod in obj.modifiers if mod.type in ["EDGE_SPLIT", "BOOLEAN"]]
    for mod in mods_to_remove:
        bpy.ops.object.modifier_remove(modifier=mod.name)

    # Remove objects from OCD_temp collection
    collection_name = "OCD_temp"
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
        meshes = {obj.data for obj in collection.objects if obj.type == 'MESH'}
        for obj in collection.objects:
            bpy.data.objects.remove(obj)
        for mesh in meshes:
            bpy.data.meshes.remove(mesh)
        # Remove "OCD_Rot" and "OCD_Loc" empty objects if they exist
        for empty_name in ["OCD_Rot", "OCD_Loc"]:
            if empty_name in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[empty_name])
        bpy.data.collections.remove(collection)
    return {'FINISHED'}

def simple_apply(context):
    props2 = context.object.stored_value
    damaged_col = "OCD_temp"
    sourceName = context.object.name
    targetName = sourceName + "_temp"

    target_obj = bpy.data.collections[damaged_col].objects.get(targetName)
    ocd_texture = bpy.data.textures.get("OCD_texture")

    if target_obj:
        ocd_displace = target_obj.modifiers.get("OCD_Displace")
        ocd_smooth = target_obj.modifiers.get("OCD_Smooth")
        ocd_remesh = target_obj.modifiers.get("OCD_remesh")
        ocd_remesh_02 = target_obj.modifiers.get("OCD_remesh_02")

        if ocd_displace:
            props2.ocd_strength = ocd_displace.strength
            props2.ocd_mid_level = ocd_displace.mid_level
        if ocd_smooth:
            props2.ocd_smooth = ocd_smooth.factor
            props2.ocd_smooth_iter = ocd_smooth.iterations
        if ocd_remesh:
            props2.ocd_voxel_size = ocd_remesh.voxel_size
        if ocd_remesh_02:
            props2.ocd_voxel_size_02 = ocd_remesh_02.voxel_size

    if ocd_texture:
        props2.ocd_noise_scale = ocd_texture.noise_scale
        props2.ocd_noise_type = ocd_texture.type
        props2.ocd_contrast = ocd_texture.contrast
        props2.ocd_brightness = ocd_texture.intensity

        has_noise_basis = hasattr(ocd_texture, "noise_basis")

        if has_noise_basis:
            props2.ocd_noise_basis = ocd_texture.noise_basis
        if ocd_texture.type not in ["MUSGRAVE", "CLOUDS", "VORONOI"]:
            props2.ocd_turbulence = ocd_texture.turbulence

    active_obj = context.view_layer.objects.active

    ocd_boolean = active_obj.modifiers.get("OCD_Boolean")

    # Get the current addon preferences
    addon_name = __name__.partition('.')[0]
    prefs = context.preferences.addons[addon_name].preferences

    # Check the boolean method preference
    use_exact_boolean = prefs.use_exact_boolean

    if ocd_boolean:
        # If use_exact_boolean is True, set the solver method to Exact
        if use_exact_boolean:
            ocd_boolean.solver = 'EXACT'
        else:
            ocd_boolean.solver = 'FAST'

        bpy.ops.object.modifier_apply(modifier=ocd_boolean.name)

    # Use list comprehension to collect and remove specific modifiers
    mods_to_remove = [mod for mod in active_obj.modifiers if mod.type == "EDGE_SPLIT"]
    for mod in mods_to_remove:
        bpy.ops.object.modifier_remove(modifier=mod.name)

    w_normal = active_obj.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
    w_normal.keep_sharp = True

    #materials
    mat_names = ["OUTSIDE", "INSIDE"]
    materials.assign_materials(__name__.partition('.')[0], mat_names)
    bpy.data.meshes[sourceName].use_fake_user = True

    collection = bpy.data.collections.get(damaged_col)
    if collection:
        # Use set comprehension to collect mesh objects
        meshes = {obj.data for obj in collection.objects if obj.type == 'MESH'}
        # Remove objects and corresponding meshes
        for obj in collection.objects:
            if obj.type == 'MESH':
                bpy.data.objects.remove(obj)
        for mesh in meshes:
            bpy.data.meshes.remove(mesh)
        # Remove "OCD_Rot" and "OCD_Loc" empty objects if they exist
        for empty_name in ["OCD_Rot", "OCD_Loc"]:
            if empty_name in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[empty_name])
        bpy.data.collections.remove(collection)

    active_obj["OCD_applied"] = True
    return {'FINISHED'}

def recall(context, self):
    damageName = bpy.context.object.name
    damageObj = bpy.data.objects[damageName]
    sourceName = damageName[:-4]

    # Create a new mesh with the same data as the source mesh
    sourceMesh = bpy.data.meshes[sourceName]
    mesh = sourceMesh.copy()
    mesh.name = 'donor'

    # Create a new object and link the mesh
    donorObj = bpy.data.objects.new('donor', mesh)
    bpy.context.collection.objects.link(donorObj)

    # Copy location, rotation, and scale from the original object
    donorObj.location = damageObj.location
    donorObj.rotation_euler = damageObj.rotation_euler
    donorObj.scale = damageObj.scale

    # Check if the '.' character exists in sourceName before splitting
    if '.' in sourceName:
        base_name, source_number = sourceName.rsplit('.', 1)
    else:
        base_name = sourceName
        source_number = "000"

    # Find the highest numbered object with the same base name and _dmg suffix
    highest_number = int(source_number)
    for obj in bpy.data.objects:
        if obj.name.startswith(base_name) and obj.name.endswith("_dmg"):
            try:
                number = int(obj.name.split('.')[1])
                highest_number = max(highest_number, number)
            except (ValueError, IndexError):
                pass

    # Find an available object name
    new_name = None
    i = highest_number + 1
    while new_name is None:
        candidate_name = f"{base_name}.{i:03}"
        candidate_name_dmg = f"{candidate_name}_dmg"
        if candidate_name not in bpy.data.objects and candidate_name_dmg not in bpy.data.objects:
            new_name = candidate_name
        i += 1

    # Duplicate the donor object and update its name
    duplicateObj = donorObj.copy()
    duplicateObj.name = new_name
    bpy.context.collection.objects.link(duplicateObj)

    # Update the duplicate object's mesh name
    duplicateObj.data.name = new_name

    # Update the duplicate object's scale
    duplicateObj.scale = damageObj.scale

    # Deselect the original object
    damageObj.select_set(False)

    # Set the new object as selected and active
    duplicateObj.select_set(True)
    context.view_layer.objects.active = duplicateObj

    # Remove the donor object
    bpy.data.objects.remove(donorObj)

    return {'FINISHED'}
    
def ctrl_recall(context, self):
    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        damageName = obj.name
        sourceName = damageName[:-4]

        # Check if the source mesh exists
        source_mesh = bpy.data.meshes.get(sourceName)
        if source_mesh is None:
            self.report({'ERROR'}, "No source mesh found")
            return {'CANCELLED'}

        # Store the original mesh data
        original_mesh_data = obj.data

        # Remap the mesh data to the source mesh
        obj.data = source_mesh

        # Rename the object and its mesh data
        obj.name = sourceName
        obj.data.name = sourceName

        # Remove the "OCD_WNormal" modifier from the object
        for mod in obj.modifiers:
            if mod.name == "OCD_WNormal":
                obj.modifiers.remove(mod)

        # Remove the original mesh data
        bpy.data.meshes.remove(original_mesh_data)
        self.report({'INFO'}, "Original object recalled")
        if "OCD_applied" in obj:
            del obj["OCD_applied"]

        if "stored_value" in bpy.context.object:
            del bpy.context.object["stored_value"]
    return {'FINISHED'}

def OCD_random(context, self, random):
    # List to store names of initially selected objects
    initial_selected_objects = [obj.name for obj in bpy.context.selected_objects]
    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = obj
        props2 = bpy.context.object.stored_value
        voxel_1 = props2.ocd_voxel_size
        voxel_2 = props2.ocd_voxel_size_02
        mid = props2.ocd_mid_level
        strength = props2.ocd_strength
        noiseScale = props2.ocd_noise_scale
        noiseType = props2.ocd_noise_type
        noise_basis = props2.ocd_noise_basis
        ocd_brightness = props2.ocd_brightness
        ocd_contrast = props2.ocd_contrast
        ocd_turbulence = props2.ocd_turbulence
        smooth = props2.ocd_smooth

        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        # Select the current object
        obj.select_set(True)
        damageName = obj.name
        sourceName2 = damageName[:-4]

        # Check if the source mesh exists
        source_mesh = bpy.data.meshes.get(sourceName2)
        if source_mesh is None:
            continue
            #self.report({'ERROR'}, "No source mesh found")
            #return {'CANCELLED'}

        # Store the original mesh data
        original_mesh_data = obj.data

        # Remap the mesh data to the source mesh
        obj.data = source_mesh

        # Rename the object and its mesh data
        obj.name = sourceName2
        obj.data.name = sourceName2

        # Remove the "OCD_WNormal" modifier from the object
        for mod in obj.modifiers:
            if mod.name == "OCD_WNormal":
                obj.modifiers.remove(mod)

        # Remove the original mesh data
        bpy.data.meshes.remove(original_mesh_data)

        sourceName = bpy.context.object.name
        sourceObj = bpy.data.objects[sourceName]
        damaged_col = "OCD_temp"
            
        if damaged_col not in bpy.data.collections:      
            damaged_collection = bpy.context.blend_data.collections.new(name=damaged_col)
            bpy.context.collection.children.link(damaged_collection)
        else:
            damaged_collection = bpy.data.collections[damaged_col]      

        damaged_collection.hide_viewport = True
        damaged_collection.hide_render = True
        
        sourceName = bpy.context.object.name
        sourceMeshName = bpy.data.objects[sourceName].data.name
        bpy.context.object.name = sourceMeshName
        bpy.context.object.name = sourceName
        
        bpy.data.objects[sourceName].data.name = sourceName 
        
        sourceMeshName = bpy.data.objects[sourceName].data.name
        
        bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)
        
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        bpy.context.object.name = sourceName + "_dmg"
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.edges_select_sharp(sharpness=0.436332)
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.editmode_toggle()

        damageName = bpy.context.object.name
        damageObj = bpy.data.objects[damageName]
        
        bpy.context.object.name = damageName
        bpy.data.objects[damageName].data.name = damageName
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[sourceName].select_set(True)
        bpy.context.view_layer.objects.active = sourceObj
        bpy.ops.object.delete(use_global=False)

        bpy.data.objects[damageName].select_set(True)
        bpy.context.view_layer.objects.active = damageObj

        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        bpy.context.object.name = damageName + "_temp"

        targetName = bpy.context.object.name
        targetObj = bpy.data.objects[targetName]
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.object.editmode_toggle()

        for ob in bpy.context.object.users_collection:
            ob.objects.unlink(targetObj)
        
        bpy.data.collections[damaged_col].objects.link(targetObj)

        #place an Empty named OCD_Empty at the random location
        random_location = (random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100))
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=random_location)
        bpy.context.object.name = "OCD_Empty"
        
        bpy.data.objects[targetName].modifiers.new("OCD_remesh", type='REMESH')
        bpy.data.objects[targetName].modifiers["OCD_remesh"].mode = 'VOXEL'
        bpy.data.objects[targetName].modifiers["OCD_remesh"].voxel_size = voxel_1
        bpy.data.objects[targetName].modifiers["OCD_remesh"].use_smooth_shade = True
        
        bpy.data.objects[targetName].modifiers.new("OCD_Smooth", type='SMOOTH')
        bpy.data.objects[targetName].modifiers["OCD_Smooth"].iterations = 30
        bpy.data.objects[targetName].modifiers["OCD_Smooth"].factor = smooth

        if "OCD_texture" not in bpy.data.textures:
            OCD_texture = bpy.data.textures.new("OCD_texture", type=noiseType)
            try:
                OCD_texture.use_clamp = True
            except AttributeError:
                pass  
        else:
            OCD_texture = bpy.data.textures["OCD_texture"]
            try:
                OCD_texture.use_clamp = True
            except AttributeError:
                pass  

        OCD_texture.noise_scale = noiseScale
        OCD_texture.type = noiseType
        
        # Check if the texture supports the 'noise_basis' attribute
        if hasattr(OCD_texture, "noise_basis"):
            try:
                # Attempt to set the 'noise_basis' to 'VORONOI_CRACKLE', or choose a valid value for your texture type
                OCD_texture.noise_basis = 'VORONOI_CRACKLE'  # Make sure 'VORONOI_CRACKLE' is a valid option for 'noise_basis'
            except ValueError:
                # Handle cases where 'VORONOI_CRACKLE' is not a valid value for 'noise_basis'
                print(f"'VORONOI_CRACKLE' is not a valid noise_basis for {OCD_texture.type}.")

        OCD_texture.contrast = ocd_contrast
        OCD_texture.intensity = ocd_brightness

        has_turbulence = hasattr(OCD_texture, "turbulence")
        if has_turbulence:
            OCD_texture.turbulence = ocd_turbulence

        bpy.data.objects[targetName].modifiers.new("OCD_Displace", type='DISPLACE')
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture = bpy.data.textures["OCD_texture"]
        bpy.data.objects[targetName].modifiers["OCD_Displace"].strength = strength
        bpy.data.objects[targetName].modifiers["OCD_Displace"].mid_level = mid

        bpy.data.objects[targetName].modifiers.new("OCD_remesh_02", type='REMESH')
        bpy.data.objects[targetName].modifiers["OCD_remesh_02"].voxel_size = voxel_2
        bpy.data.objects[targetName].modifiers["OCD_remesh_02"].use_smooth_shade = True
        
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture = OCD_texture
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture_coords = 'OBJECT'
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture_coords_object = bpy.data.objects["OCD_Empty"]
        
        bpy.context.view_layer.objects.active = damageObj
        bpy.context.active_object.select_set(state=True)
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()

        bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
        bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["OCD_Boolean"].object = targetObj
        bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
        bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
        bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

        try:
            bpy.context.object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 1.0472
        except AttributeError:
            pass
        
        bpy.data.objects[damageName].modifiers["OCD_Boolean"].solver = 'FAST'

        active_obj = bpy.context.view_layer.objects.active
        
        # Get the current addon preferences
        addon_name = __name__.partition('.')[0]
        prefs = context.preferences.addons[addon_name].preferences

        # Check the boolean method preference
        use_exact_boolean = prefs.use_exact_boolean
        
        # Apply and remove modifiers
        active_obj = bpy.context.active_object
        for mod in active_obj.modifiers:
            if mod.name == "OCD_Boolean":
                # If use_exact_boolean is True, set the solver method to Exact
                if use_exact_boolean:
                    mod.solver = 'EXACT'
                else:
                    mod.solver = 'FAST'
                bpy.ops.object.modifier_apply(modifier=mod.name)

            if mod.type == "EDGE_SPLIT":
                bpy.ops.object.modifier_remove(modifier=mod.name)

        # Add WEIGHTED_NORMAL modifier
        bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
        
        #materials
        mat_names = ["OUTSIDE", "INSIDE"]
        materials.assign_materials(__name__.partition('.')[0], mat_names)
        
        damageName = bpy.context.object.name
        sourceName = damageName[:-4]
        
        bpy.data.meshes[sourceName].use_fake_user = True
        
        collection_name = "OCD_temp"
        collection = bpy.data.collections[collection_name]

        meshes = set()
        for obj in [o for o in collection.objects if o.type == 'MESH']:
            meshes.add( obj.data )
            bpy.data.objects.remove( obj )
        for mesh in [m for m in meshes]:
            bpy.data.meshes.remove( mesh )
        collection = bpy.data.collections.get(collection_name)
        bpy.data.collections.remove(collection)
        #delete OCD_Empty:
        bpy.data.objects.remove(bpy.data.objects["OCD_Empty"])
        active_obj["OCD_applied"] = True
        # pause
        time.sleep(0.015)  
        
    #Select the initially selected objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj_name in initial_selected_objects:
        if obj_name in bpy.data.objects:  # Check if the object still exists
            bpy.data.objects[obj_name].select_set(True)
    return {'FINISHED'}   

def OCD_random_ctrl(context, self, random):
    props2 = bpy.context.object.stored_value
    noiseType = props2.ocd_noise_type
    noise_basis = props2.ocd_noise_basis
    noiseScale = props2.ocd_noise_scale
    ocd_brightness = props2.ocd_brightness
    ocd_contrast = props2.ocd_contrast
    ocd_turbulence = props2.ocd_turbulence
    active_object = bpy.context.view_layer.objects.active
    
    # List to store names of initially selected objects
    initial_selected_objects = [obj.name for obj in bpy.context.selected_objects]

    for obj in bpy.context.selected_objects:
        if obj == active_object:
            continue
        bpy.context.view_layer.objects.active = obj
        props2 = bpy.context.object.stored_value
        voxel_1 = props2.ocd_voxel_size
        voxel_2 = props2.ocd_voxel_size_02
        mid = props2.ocd_mid_level
        smooth = props2.ocd_smooth
        strength = props2.ocd_strength
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        # Select the current object
        obj.select_set(True)
        damageName = obj.name
        sourceName2 = damageName[:-4]
        # Check if the source mesh exists
        source_mesh = bpy.data.meshes.get(sourceName2)
        if source_mesh is None:
            self.report({'ERROR'}, "No source mesh found")
            return {'CANCELLED'}

        # Store the original mesh data
        original_mesh_data = obj.data

        # Remap the mesh data to the source mesh
        obj.data = source_mesh

        # Rename the object and its mesh data
        obj.name = sourceName2
        obj.data.name = sourceName2

        # Remove the "OCD_WNormal" modifier from the object
        for mod in obj.modifiers:
            if mod.name == "OCD_WNormal":
                obj.modifiers.remove(mod)

        # Remove the original mesh data
        bpy.data.meshes.remove(original_mesh_data)

        sourceName = bpy.context.object.name
        sourceObj = bpy.data.objects[sourceName]
        damaged_col = "OCD_temp"
            
        if damaged_col not in bpy.data.collections:      
            damaged_collection = bpy.context.blend_data.collections.new(name=damaged_col)
            bpy.context.collection.children.link(damaged_collection)
        else:
            damaged_collection = bpy.data.collections[damaged_col]      

        damaged_collection.hide_viewport = True
        damaged_collection.hide_render = True
        
        sourceName = bpy.context.object.name
        sourceMeshName = bpy.data.objects[sourceName].data.name
        bpy.context.object.name = sourceMeshName
        bpy.context.object.name = sourceName
        
        bpy.data.objects[sourceName].data.name = sourceName 
        
        sourceMeshName = bpy.data.objects[sourceName].data.name
        
        bpy.ops.object.transform_apply(location = False, rotation = False, scale = True)
        
        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        bpy.context.object.name = sourceName + "_dmg"
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.edges_select_sharp(sharpness=0.436332)
        bpy.ops.mesh.mark_sharp()
        bpy.ops.object.editmode_toggle()

        damageName = bpy.context.object.name
        damageObj = bpy.data.objects[damageName]
        
        bpy.context.object.name = damageName
        bpy.data.objects[damageName].data.name = damageName
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[sourceName].select_set(True)
        bpy.context.view_layer.objects.active = sourceObj
        bpy.ops.object.delete(use_global=False)

        bpy.data.objects[damageName].select_set(True)
        bpy.context.view_layer.objects.active = damageObj

        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'})
        bpy.context.object.name = damageName + "_temp"

        targetName = bpy.context.object.name
        targetObj = bpy.data.objects[targetName]
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.object.editmode_toggle()

        for ob in bpy.context.object.users_collection:
            ob.objects.unlink(targetObj)
        
        bpy.data.collections[damaged_col].objects.link(targetObj)

        #place an Empty named OCD_Empty at the random location
        random_location = (random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100))
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=random_location)
        bpy.context.object.name = "OCD_Empty"
        
        bpy.data.objects[targetName].modifiers.new("OCD_remesh", type='REMESH')
        bpy.data.objects[targetName].modifiers["OCD_remesh"].mode = 'VOXEL'
        bpy.data.objects[targetName].modifiers["OCD_remesh"].voxel_size = voxel_1 
        bpy.data.objects[targetName].modifiers["OCD_remesh"].use_smooth_shade = True
        
        bpy.data.objects[targetName].modifiers.new("OCD_Smooth", type='SMOOTH')
        bpy.data.objects[targetName].modifiers["OCD_Smooth"].iterations = 30
        bpy.data.objects[targetName].modifiers["OCD_Smooth"].factor = smooth

        if "OCD_texture" not in bpy.data.textures:
            OCD_texture = bpy.data.textures.new("OCD_texture", type = noiseType)
            bpy.data.textures["OCD_texture"].noise_basis = 'VORONOI_CRACKLE'
        else:
            OCD_texture = bpy.data.textures["OCD_texture"]
        bpy.data.textures["OCD_texture"].noise_scale = noiseScale
        bpy.data.textures["OCD_texture"].type = noiseType
        has_noise_basis = hasattr(bpy.data.textures["OCD_texture"], "noise_basis")
        if has_noise_basis:
            bpy.data.textures["OCD_texture"].noise_basis = noise_basis
        else:
            pass
        bpy.data.textures["OCD_texture"].contrast = ocd_contrast
        bpy.data.textures["OCD_texture"].intensity = ocd_brightness
        has_turbulence = hasattr(bpy.data.textures["OCD_texture"], "turbulence")
        if has_turbulence:
            bpy.data.textures["OCD_texture"].turbulence = ocd_turbulence
        else:
            pass
        has_noise_basis = hasattr(bpy.data.textures["OCD_texture"], "noise_basis")
        if has_noise_basis:
            bpy.data.textures["OCD_texture"].noise_basis = noise_basis
        else:
            pass
        
        bpy.data.objects[targetName].modifiers.new("OCD_Displace", type='DISPLACE')
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture = bpy.data.textures["OCD_texture"]
        bpy.data.objects[targetName].modifiers["OCD_Displace"].strength = strength
        bpy.data.objects[targetName].modifiers["OCD_Displace"].mid_level = mid

        bpy.data.objects[targetName].modifiers.new("OCD_remesh_02", type='REMESH')
        bpy.data.objects[targetName].modifiers["OCD_remesh_02"].voxel_size = voxel_2 
        bpy.data.objects[targetName].modifiers["OCD_remesh_02"].use_smooth_shade = True
        
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture = OCD_texture
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture_coords = 'OBJECT'
        bpy.data.objects[targetName].modifiers["OCD_Displace"].texture_coords_object = bpy.data.objects["OCD_Empty"]
        
        bpy.context.view_layer.objects.active = damageObj
        bpy.context.active_object.select_set(state=True)
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.editmode_toggle()

        bpy.context.object.modifiers.new("OCD_Boolean", type='BOOLEAN')
        bpy.context.object.modifiers["OCD_Boolean"].solver = 'FAST'
        bpy.context.object.modifiers["OCD_Boolean"].object = targetObj
        bpy.context.object.modifiers["OCD_Boolean"].operation = 'INTERSECT'
        bpy.context.object.modifiers.new("OCD_Preview", type='EDGE_SPLIT')
        bpy.context.object.modifiers["OCD_Preview"].split_angle = 0.261799

        try:
            bpy.context.object.data.use_auto_smooth = True
            bpy.context.object.data.auto_smooth_angle = 1.0472
        except AttributeError:
            pass

        props2 = bpy.context.object.stored_value
        damaged_col = "OCD_temp"
        sourceName = bpy.context.object.name
        targetName = sourceName + "_temp"

        props2.ocd_strength = bpy.data.collections[damaged_col].objects[targetName].modifiers["OCD_Displace"].strength
        props2.ocd_mid_level = bpy.data.collections[damaged_col].objects[targetName].modifiers["OCD_Displace"].mid_level
        props2.ocd_smooth = bpy.data.collections[damaged_col].objects[targetName].modifiers["OCD_Smooth"].factor
        props2.ocd_noise_scale = bpy.data.textures["OCD_texture"].noise_scale
        props2.ocd_noise_type = bpy.data.textures["OCD_texture"].type
        has_noise_basis = hasattr(bpy.data.textures["OCD_texture"], "noise_basis")
        if has_noise_basis:
            props2.ocd_noise_basis = bpy.data.textures["OCD_texture"].noise_basis
        if bpy.data.textures["OCD_texture"].type not in ["MUSGRAVE", "CLOUDS", "VORONOI"]:
            props2.ocd_turbulence = bpy.data.textures["OCD_texture"].turbulence
        props2.ocd_contrast = bpy.data.textures["OCD_texture"].contrast
        props2.ocd_brightness = bpy.data.textures["OCD_texture"].intensity
        props2.ocd_voxel_size = bpy.data.collections[damaged_col].objects[targetName].modifiers["OCD_remesh"].voxel_size
        props2.ocd_voxel_size_02 = bpy.data.collections[damaged_col].objects[targetName].modifiers["OCD_remesh_02"].voxel_size
        
        bpy.data.objects[damageName].modifiers["OCD_Boolean"].solver = 'FAST'
        active_obj = bpy.context.view_layer.objects.active
        
        # Get the current addon preferences
        addon_name = __name__.partition('.')[0]
        prefs = context.preferences.addons[addon_name].preferences

        # Check the boolean method preference
        use_exact_boolean = prefs.use_exact_boolean

        # Apply and remove modifiers
        active_obj = bpy.context.active_object
        for mod in active_obj.modifiers:
            if mod.name == "OCD_Boolean":
                # If use_exact_boolean is True, set the solver method to Exact
                if use_exact_boolean:
                    mod.solver = 'EXACT'
                else:
                    mod.solver = 'FAST'
                bpy.ops.object.modifier_apply(modifier=mod.name)

            if mod.type == "EDGE_SPLIT":
                bpy.ops.object.modifier_remove(modifier=mod.name)

        # Add WEIGHTED_NORMAL modifier
        bpy.context.object.modifiers.new("OCD_WNormal", type='WEIGHTED_NORMAL')
        bpy.context.object.modifiers["OCD_WNormal"].keep_sharp = True
        
        #materials
        mat_names = ["OUTSIDE", "INSIDE"]
        materials.assign_materials(__name__.partition('.')[0], mat_names)
        damageName = bpy.context.object.name
        sourceName = damageName[:-4]
        bpy.data.meshes[sourceName].use_fake_user = True
        collection_name = "OCD_temp"
        collection = bpy.data.collections[collection_name]

        meshes = set()

        for obj in [o for o in collection.objects if o.type == 'MESH']:
            meshes.add( obj.data )
            bpy.data.objects.remove( obj )
        for mesh in [m for m in meshes]:
            bpy.data.meshes.remove( mesh )
        collection = bpy.data.collections.get(collection_name)
        bpy.data.collections.remove(collection)
        #delete OCD_Empty:
        bpy.data.objects.remove(bpy.data.objects["OCD_Empty"])
        active_obj["OCD_applied"] = True
        # pause
        time.sleep(0.015) 

    #Select the initially selected objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj_name in initial_selected_objects:
        if obj_name in bpy.data.objects:  # Check if the object still exists
            bpy.data.objects[obj_name].select_set(True)
    return {'FINISHED'}   