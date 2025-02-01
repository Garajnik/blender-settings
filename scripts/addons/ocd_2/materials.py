import bpy

def get_materials_1(self, context):
    items = [(mat.name, mat.name, mat.name) for mat in bpy.data.materials if mat.name != "Dots Stroke"]
    return items

def get_materials_2(self, context):
    items = [(mat.name, mat.name, mat.name) for mat in bpy.data.materials if mat.name != "Dots Stroke"]
    items.append(('NONE', "None", "No material")) # Add None option at the end
    return items


def assign_materials(addon_name, mat_names):
    prefs = bpy.context.preferences.addons[addon_name].preferences
    
    mat_name_1 = prefs.mat_name_1 if prefs.mat_name_1 and prefs.mat_name_1 != 'NONE' else None
    mat_name_2 = prefs.mat_name_2 if prefs.mat_name_2 and prefs.mat_name_2 != 'NONE' else None
    if mat_name_1 is None and mat_name_2 is None:
        return
    
    mat_1 = None
    mat_2 = None

    if mat_name_1 is not None:
        mat_1 = bpy.data.materials.get(mat_name_1) or bpy.data.materials.new(name=mat_name_1)
        mat_1.use_nodes = True
    if mat_name_2 is not None:
        mat_2 = bpy.data.materials.get(mat_name_2) or bpy.data.materials.new(name=mat_name_2)
        mat_2.use_nodes = True
 
    obj = bpy.context.object

    if obj.active_material is None:
        if obj.data.materials:
            # If mat_2 is already in object materials, use that slot
            if mat_2 and mat_name_2 in obj.data.materials:
                obj.active_material_index = obj.data.materials.find(mat_name_2)
            else:
                if mat_1:
                    obj.data.materials[0] = mat_1
                if mat_2:
                    obj.data.materials.append(mat_2)
        else:
            if mat_1:
                obj.data.materials.append(mat_1)
            if mat_2 and mat_name_2 != mat_name_1:  # Prevent duplicating the same material
                obj.data.materials.append(mat_2)

        bpy.ops.object.editmode_toggle()

        if mat_1:
            obj.active_material_index = 0
            bpy.ops.object.material_slot_assign()
        if mat_2:
            bpy.ops.mesh.select_all(action='INVERT')
            obj.active_material_index = 1
            bpy.ops.object.material_slot_assign()
    else:
        # If mat_2 is already in object materials, use that slot
        if mat_2 and mat_name_2 in obj.data.materials:
            obj.active_material_index = obj.data.materials.find(mat_name_2)
        else:
            if mat_2:
                bpy.ops.object.material_slot_add()
                idx = obj.active_material_index
                obj.material_slots[idx].material = mat_2
        bpy.ops.object.editmode_toggle()
        if mat_2:
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.object.material_slot_assign()
            
    bpy.ops.object.editmode_toggle()

