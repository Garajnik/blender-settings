#Copyright (C) 2024 vfxguide
#realvfxguide@gmail.com

#Created by VFXGuide
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "OCD - One Click Damage",
    "author": "VFXGuide",
    "version": (2, 0, 2),
    "blender": (2, 93, 0),
    "location": "View3D -> N-Panel -> OCD2",
    "description": "One Click Damage",
    "doc_url": "https://vfxguide.net/ocd/index.html",
    "category": "Object",
}

import bpy
import os
import bgl
import blf
import random
import webbrowser
from mathutils import Vector
from bpy_extras.view3d_utils import (
    region_2d_to_location_3d, 
    region_2d_to_origin_3d, 
    region_2d_to_vector_3d
)
from bpy.types import Operator, Panel, PropertyGroup, Menu
from bpy.props import (
    IntProperty,
    FloatProperty, 
    PointerProperty, 
    BoolProperty, 
    EnumProperty, 
    StringProperty
)
from bpy.utils import register_class, unregister_class

from .functions import (
    damage_on, 
    ctrl_damage, 
    multobj_damage, 
    damage_off, 
    simple_apply, 
    recall, 
    ctrl_recall, 
    OCD_random, 
    OCD_random_ctrl, 
    update_func
)
from .utils import find_mesh_errors

if bpy.app.version < (2, 93, 0):
    raise Exception("This addon requires Blender 2.93 or later")

class DamageProps(PropertyGroup):
    damage_amount : FloatProperty(
        name = "Amount",
        default = 25,
        min = 0,
        max = 100,
        subtype = "PERCENTAGE",
        update=update_func,
    )
    
    scale_amount : FloatProperty(
        name = "Scale",
        default = 35,
        min = 0,
        soft_max = 100,
        subtype = "PERCENTAGE",
        update=update_func,
    )
    
    noise_type : EnumProperty( 
        name= "Noise Selection", 
        description= "Noise Selection", 
        items= [('CLOUDS', "CLOUDS", ""),
                ('MUSGRAVE', "MUSGRAVE", ""),
                ('MARBLE',"MARBLE",""),
                ('VORONOI', "VORONOI",""),
                ('WOOD', "WOOD","")],
        update=update_func,       
    )

def get_addon_path():
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    return directory

def get_blend_file_path(filename):
    addon_path = get_addon_path()
    blend_filepath = os.path.join(addon_path, filename)
    return blend_filepath

def node_center(context):
    from mathutils import Vector
    loc = Vector((0.0, 0.0))
    node_selected = context.selected_nodes
    if node_selected:
        for node in node_selected:
            loc += node.location
        loc /= len(node_selected)
    return loc

class StoredValueProp(PropertyGroup):
    ocd_strength : FloatProperty(
        name = "Strength",
    )
    ocd_voxel_size : FloatProperty(
        name = "Voxel Size",
    )
    ocd_voxel_size_02 : FloatProperty(
        name = "Voxel Size 02",
    )
    ocd_smooth : FloatProperty(
        name = "Smooth",
    )
    ocd_noise_scale : FloatProperty(
        name = "Noise Scale",
    )
    ocd_mid_level : FloatProperty(
        name = "Mid Level",
    )
    ocd_noise_type : bpy.props.StringProperty(
        name = "Noise Type",
    )
    ocd_noise_basis : bpy.props.StringProperty(
        name = "Noise Basis",
    )
    ocd_turbulence : FloatProperty(
        name = "Noise Turbulence",
    )
    ocd_brightness : FloatProperty(
        name = "Noise Brightness",
    )
    ocd_contrast : FloatProperty(
        name = "Noise Contrast",
    )

class OCD_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    ocd_voxel_size: FloatProperty(
        name="Voxel Size (less is more)",
        default=24,
        min=10,
        soft_max=30,
    )

    mat_name_1: bpy.props.EnumProperty(
        name="Outside Material",
        items=materials.get_materials_1,
    )

    mat_name_2: bpy.props.EnumProperty(
        name="Inside Material",
        items=materials.get_materials_2,
    )

    show_addon_description: bpy.props.BoolProperty(
        name="Show Addon Description",
        description="Show/hide the detailed description about how to use this addon",
        default=False
    )

    use_exact_boolean: bpy.props.BoolProperty(
        name="Use Exact Boolean Solver",
        description="Enables the Exact method: more accurate but slower. If disabled, Fast method is used",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="OCD Resolution:")
        col.prop(self, "ocd_voxel_size")

        col.label(text="OCD Materials:")
        sub_col = col.column()
        sub_col.prop(self, "mat_name_1")
        sub_col.prop(self, "mat_name_2")

        col.separator()
        col.label(text="Boolean Method:")
        col.prop(self, "use_exact_boolean")

        if self.use_exact_boolean:
            col.label(text="Warning: 'Exact' is resource-intensive and much slower!", icon='ERROR')

# Global variable to store removed modifier information
global_removed_modifier_info = {}

class OBJECT_OT_damageON(Operator):
    bl_label = "OCD"
    bl_idname = "object.ocd_on"
    bl_description = "Hold ctrl for instant damage"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select_get() and obj.type == 'MESH' and obj.mode == 'OBJECT'

    def invoke(self, context, event):
        global global_removed_modifier_info
        selected_objects = context.selected_objects

        # Check if the "OCD_temp" collection exists in the Blender file
        if "OCD_temp" in bpy.data.collections:
            ocd_temp_collection = bpy.data.collections["OCD_temp"]

            # Generate a list of base object names (excluding the last 5 characters)
            object_names = [obj.name[:-5] for obj in ocd_temp_collection.objects]

            found_object = None

            # Check for each object by name, but you're only interested in finding one
            for obj_name in object_names:
                obj = context.scene.objects.get(obj_name)
                if obj:
                    found_object = obj
                    break  # Exit the loop after the first match

            if found_object:
                # Deselect all objects first
                bpy.ops.object.select_all(action='DESELECT')
                # Select the found object and set it as the active object
                found_object.select_set(True)
                context.view_layer.objects.active = found_object

                warning_message = "OCD is still active on: " + found_object.name + " - Finish the damage first."
                self.report({'WARNING'}, warning_message)
                return {'CANCELLED'}
            else:
                # No valid object found, remove the "OCD_temp" collection and its contents
                while ocd_temp_collection.objects:
                    bpy.data.objects.remove(ocd_temp_collection.objects[0], do_unlink=True)
                bpy.data.collections.remove(ocd_temp_collection)


        # Clear the global_removed_modifier_info dictionary to store fresh data for this operation
        global_removed_modifier_info.clear()
        
        # Iterate over each selected object to check for Geometry Nodes modifiers
        for obj in selected_objects:
            for modifier in obj.modifiers:
                if modifier.type == 'NODES' and modifier.node_group and modifier.node_group.name.startswith("OCD_Hero"):
                    # Store the modifier's details in the global variable
                    global_removed_modifier_info[obj.name] = {
                        'modifier_name': modifier.name,
                        'node_group_name': modifier.node_group.name
                    }
                    # Remove the Geometry Nodes modifier
                    obj.modifiers.remove(modifier)
                    break  # Assuming one such modifier per object; adjust if necessary

        # Perform damage application based on the user action
        if event.ctrl or event.oskey:
            ctrl_damage(context, self)
            self.restore_modifiers(context)
        elif len(selected_objects) > 1:
            multobj_damage(context)
            # After applying damage, restore modifiers to potentially renamed objects
            self.restore_modifiers(context)
        else:
            damage_on(context, self)

        return {'FINISHED'}

    def restore_modifiers(self, context):
        global global_removed_modifier_info
        # Iterate over the stored information in global_removed_modifier_info to restore modifiers
        for obj_name, mod_info in global_removed_modifier_info.items():
            # Assuming the damaged objects are renamed with "_dmg" suffix
            obj = bpy.data.objects.get(obj_name + "_dmg", None)
            if obj:
                # Restore the modifier if it doesn't already exist on the object
                if not any(mod.name == mod_info['modifier_name'] for mod in obj.modifiers):
                    restored_modifier = obj.modifiers.new(name=mod_info['modifier_name'], type='NODES')
                    restored_modifier.node_group = bpy.data.node_groups.get(mod_info['node_group_name'], None)
                    if not restored_modifier.node_group:
                        self.report({'WARNING'}, f"Node group '{mod_info['node_group_name']}' not found. Modifier restored without node group.")
                else:
                    self.report({'INFO'}, f"Modifier '{mod_info['modifier_name']}' already exists on '{obj_name}', skipping restoration.")
            else:
                self.report({'WARNING'}, f"Object '{obj_name}' not found. Cannot restore modifier.")

        # Clear the global_removed_modifier_info after restoration
        global_removed_modifier_info.clear()



class OBJECT_OT_damageOFF(Operator):
    bl_label = "OCD"
    bl_idname = "object.ocd_off"
    bl_description = "Cancel the damage"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and all(obj.type == 'MESH' and obj.mode == 'OBJECT' for obj in context.selected_objects)
    
    def execute(self, context):
        global global_removed_modifier_info

        # Perform the damage cancellation operation
        damage_off(context)

        # Iterate over the stored information in global_removed_modifier_info to restore modifiers
        for obj_name, mod_info in global_removed_modifier_info.items():
            obj = bpy.data.objects.get(obj_name)
            if obj:
                # Check if the object already has a modifier with the same name to avoid duplicates
                if not any(mod.name == mod_info['modifier_name'] for mod in obj.modifiers):
                    restored_modifier = obj.modifiers.new(name=mod_info['modifier_name'], type='NODES')
                    restored_modifier.node_group = bpy.data.node_groups.get(mod_info['node_group_name'], None)
                    if not restored_modifier.node_group:
                        self.report({'WARNING'}, f"Node group '{mod_info['node_group_name']}' not found. Modifier restored without node group.")
                else:
                    self.report({'INFO'}, f"Modifier '{mod_info['modifier_name']}' already exists on '{obj_name}', skipping restoration.")
            else:
                self.report({'WARNING'}, f"Object '{obj_name}' not found. Cannot restore modifier.")

        # Optionally, clear the global_removed_modifier_info after restoration to clean up
        global_removed_modifier_info.clear()

        self.report({'INFO'}, "Damage cancelled!")
        return {'FINISHED'}

class OBJECT_OT_apply(Operator):
    bl_label = "Apply all"
    bl_idname = "object.apply_all_mods"
    bl_description = "Apply all modifications"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or obj.mode != 'OBJECT':
            return False
        for mod in obj.modifiers:
            if mod.type == "BOOLEAN": 
                return True
        return False
    
    def execute(self, context):
        global global_removed_modifier_info

        # Apply all modifications
        simple_apply(context)

        # Iterate over the stored information in global_removed_modifier_info to restore modifiers
        for obj_name, mod_info in global_removed_modifier_info.items():
            obj = bpy.data.objects.get(obj_name + "_dmg")
            if obj:
                # Check if the object already has a modifier with the same name to avoid duplicates
                if not any(mod.name == mod_info['modifier_name'] for mod in obj.modifiers):
                    restored_modifier = obj.modifiers.new(name=mod_info['modifier_name'], type='NODES')
                    restored_modifier.node_group = bpy.data.node_groups.get(mod_info['node_group_name'], None)
                    if not restored_modifier.node_group:
                        self.report({'WARNING'}, f"Node group '{mod_info['node_group_name']}' not found. Modifier restored without node group.")
                else:
                    self.report({'INFO'}, f"Modifier '{mod_info['modifier_name']}' already exists on '{obj_name}', skipping restoration.")
            else:
                self.report({'WARNING'}, f"Object '{obj_name}' not found. Cannot restore modifier.")

        # Optionally, clear the global_removed_modifier_info after restoration to clean up
        global_removed_modifier_info.clear()
        return {'FINISHED'}

class OBJECT_OT_recall(Operator):
    bl_label = "Recall Original"
    bl_idname = "object.recall_original"
    bl_description = "Hold ctrl to recall the original object as a duplicate"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select_get() and obj.type == 'MESH' and obj.mode == 'OBJECT'

    def invoke(self, context, event):
        if event.ctrl or event.oskey:
            recall(context, self)
            self.report({'INFO'}, "Original object recalled as a duplicate")
        else:
            ctrl_recall(context,self)
        return {'FINISHED'}

class OBJECT_OT_random(Operator):
    bl_label = "Randomize"
    bl_idname = "object.randomize"
    bl_description = "Change the OCD pattern. Size and Resolution will be kept"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}

    ctrl_pressed = False

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select_get() and obj.type == 'MESH' and obj.mode == 'OBJECT'

    def invoke(self, context, event):
        self.ctrl_pressed = event.ctrl

        # Check if the "OCD_temp" collection exists in the Blender file
        if "OCD_temp" in bpy.data.collections:
            # Get the "OCD_temp" collection
            ocd_temp_collection = bpy.data.collections["OCD_temp"]

            # Check if the collection is not empty
            if ocd_temp_collection.objects:
                object_names = [obj.name[:-5] for obj in ocd_temp_collection.objects]
                at_least_one_selected = False

                # Check and select objects in the scene based on names
                for obj_name in object_names:
                    obj = bpy.data.objects.get(obj_name)
                    if obj:
                        if not at_least_one_selected:
                            # Deselect all objects only once before the first selection
                            bpy.ops.object.select_all(action='DESELECT')
                            at_least_one_selected = True

                        obj.select_set(True)
                        context.view_layer.objects.active = obj  # Set the last found object as the active object

                if at_least_one_selected:
                    # Report the warning and return immediately if any object was selected
                    warning_message = "OCD is still active on: " + ", ".join(object_names) + " - Finish the damage first."
                    self.report({'WARNING'}, warning_message)
                    return {'CANCELLED'}

        return self.execute(context)

    def execute(self, context):
        global removed_modifier_info
        selected_objects = context.selected_objects
        obj = context.object
        # Initialize or clear the global dictionary for storing removed modifier info
        removed_modifier_info = {}

        # Iterate over each selected object
        for obj in selected_objects:
            # Ensure we're only working with objects of type 'MESH' and in 'OBJECT' mode, if necessary
            if obj.type == 'MESH' and obj.mode == 'OBJECT':
                # Iterate over each modifier of the current object
                for modifier in obj.modifiers:
                    if modifier.type == 'NODES' and modifier.node_group and modifier.node_group.name.startswith("OCD_Hero"):
                        # Store removed modifier info for each object separately in the global dictionary
                        removed_modifier_info[obj.name] = {
                            'modifier_name': modifier.name,
                            'node_group_name': modifier.node_group.name,
                            'show_viewport': modifier.show_viewport,  
                            'show_render': modifier.show_render  
                        }
                        # Remove the modifier from the current object
                        obj.modifiers.remove(modifier)
                        #break  # Assuming only one such modifier per object; remove this if there could be more

        # Perform OCD_random
        if self.ctrl_pressed:
            OCD_random_ctrl(context, self, random)
        else:
            OCD_random(context, self, random)

        # Restore the removed Geometry Nodes modifier if it was removed
        for obj_name, mod_info in removed_modifier_info.items():
            obj = bpy.data.objects.get(obj_name)  # Use each object's name to fetch the object
            if obj:
                # Check if the object still exists and does not already have a similar modifier
                modifier_exists = any(mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("OCD_Hero") for mod in obj.modifiers)
                if not modifier_exists:
                    # Restore the modifier if a similar one does not exist
                    restored_modifier = obj.modifiers.new(name=mod_info['modifier_name'], type='NODES')
                    restored_modifier.node_group = bpy.data.node_groups.get(mod_info['node_group_name'])
                    # Restore visibility states
                    restored_modifier.show_viewport = mod_info['show_viewport']
                    restored_modifier.show_render = mod_info['show_render']
                else:
                    self.report({'WARNING'}, f"A similar Geometry Nodes modifier already exists for {obj_name}, restoration skipped.")
            else:
                self.report({'WARNING'}, f"Failed to restore modifier for {obj_name}: object no longer exists.")

        # Clear the global info after restoration
        removed_modifier_info.clear()

        return {'FINISHED'}

class OBJECT_OT_find_mesh_errors(bpy.types.Operator):
    bl_idname = "object.find_mesh_errors"
    bl_label = "Find Mesh Errors"
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and obj.select_get() and obj.type == 'MESH' and obj.mode == 'OBJECT'
    
    def execute(self, context):
        bad_objects = find_mesh_errors(context)
        
        if len(bad_objects) == 0:
            self.report({'INFO'}, "No mesh errors found.")
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        # Select bad objects
        for bad_object in bad_objects:
            bad_object.select_set(True)
        if len(bad_objects) > 0:
            OCD_random(context, self, random)
        return {'FINISHED'}

class OBJECT_OT_damage_transform(bpy.types.Operator):
    bl_idname = "object.damage_transform"
    bl_label = "Damage Transform"
    bl_description = "Noise Pattern Shift"
    bl_options = {'UNDO'}

    def calculate_sensitivity_multiplier(self, obj):
        # Calculate the diagonal length of the bounding box
        bb_corners = [Vector(b) for b in obj.bound_box]
        bb_diagonal = (bb_corners[6] - bb_corners[0]).length
        base_multiplier = 2.0  # Sensitivity for a 1 meter object
        return base_multiplier * bb_diagonal

    def modal(self, context, event):
        ocd_loc = bpy.data.objects.get("OCD_Loc")
        if ocd_loc is None:
            self.report({'ERROR'}, "OCD_Loc object not found")
            return {'CANCELLED'}

        if event.type == 'MOUSEMOVE':
            region = context.region
            rv3d = context.region_data
            
            # Calculate view plane normal
            view_normal = rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))

            # Calculate current and initial mouse ray
            current_mouse_ray = region_2d_to_vector_3d(region, rv3d, (event.mouse_region_x, event.mouse_region_y))
            initial_mouse_ray = region_2d_to_vector_3d(region, rv3d, (self.init_mouse_x, self.init_mouse_y))

            # Project the rays onto the view plane
            current_projected = current_mouse_ray - current_mouse_ray.project(view_normal)
            initial_projected = initial_mouse_ray - initial_mouse_ray.project(view_normal)

            # Calculate the translation vector
            translation = (current_projected - initial_projected) * self.sensitivity_multiplier

            
            ocd_loc.location = self.start_loc + translation

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            ocd_loc.location = self.start_loc
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            self.init_mouse_x = event.mouse_region_x
            self.init_mouse_y = event.mouse_region_y

            ocd_loc = bpy.data.objects.get("OCD_Loc")
            if ocd_loc:
                self.start_loc = ocd_loc.location.copy()
                active_obj = context.active_object
                if active_obj:
                    self.sensitivity_multiplier = self.calculate_sensitivity_multiplier(active_obj)
                else:
                    self.sensitivity_multiplier = 5.0  # Default value if no active object
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, "OCD_Loc object not found")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "Active space must be a 3D view")
            return {'CANCELLED'}

class MATERIALS_MT_CustomMenu(bpy.types.Menu):
    bl_label = "Select Material"
    bl_idname = "MATERIALS_MT_CustomMenu"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__.partition('.')[0]].preferences

        col = layout.column(align=True)
        
        row = col.row(align=True)
        row.prop(prefs, "mat_name_1", text="")
        row = col.row(align=True)
        row.prop(prefs, "mat_name_2", text="")

class OBJECT_OT_materials(Operator):
    bl_idname = "object.materials_selection"
    bl_label = "Materials Selection"
    bl_description = "Material Selection"

    def execute(self, context):
        bpy.ops.wm.call_menu(name="MATERIALS_MT_CustomMenu")
        return {'FINISHED'}

class OBJECT_OT_open_docs(Operator):
    bl_idname = "object.open_docs"
    bl_label = "Open Docs"
    bl_description = "Online Manual"

    url: bpy.props.StringProperty(
        name="URL",
        description="URL to open",
        default="https://vfxguide.net/ocd/index.html"
    )

    def execute(self, context):
        webbrowser.open(self.url)
        self.report({'INFO'}, f"Opened URL: {self.url}")
        return {'FINISHED'}

class OBJECT_OT_open_addon_preferences(Operator):
    bl_idname = "object.open_addon_preferences"
    bl_label = "Open Add-on Preferences"
    bl_description = " "

    def execute(self, context):
        # Open the User Preferences window
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')

        # Navigate to the add-ons section
        context.preferences.active_section = 'ADDONS'

        # Set the search field to the name of your add-on
        addon_name = "ocd"  
        bpy.data.window_managers["WinMan"].addon_search = addon_name

        return {'FINISHED'}

class GEONODES_MT_CustomMenu(bpy.types.Menu):
    bl_label = "Select HERO Nodes"
    bl_idname = "GEONODES_MT_CustomMenu"

    def draw(self, context):
        layout = self.layout
        node_trees = [ng for ng in bpy.data.node_groups if ng.name.startswith("OCD_Hero") and ng.name != "OCD_Hero"]

        if not node_trees:
            layout.label(text="No HERO Nodes found.")
            return 

        for nt in node_trees:
            # Add an operator for each node tree, passing the node tree's name as a parameter
            op = layout.operator("object.assign_hero_node_tree", text=nt.name)
            op.node_tree_name = nt.name


class OBJECT_OT_AssignHeroNodeTree(bpy.types.Operator):
    bl_idname = "object.assign_hero_node_tree"
    bl_label = "Assign Hero Node Tree"
    bl_description = "Assign the selected Hero node tree to the active object's OCD_HERO modifier"
    bl_options = {'UNDO'}

    node_tree_name: bpy.props.StringProperty()

    def execute(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if not node_tree:
            self.report({'ERROR'}, f"Node tree '{self.node_tree_name}' not found.")
            return {'CANCELLED'}

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Find an existing OCD_HERO modifier or create a new one
                mod = next((m for m in obj.modifiers if m.type == 'NODES' and m.name == "OCD_HERO"), None)
                if not mod:
                    mod = obj.modifiers.new(name="OCD_HERO", type='NODES')
                mod.node_group = node_tree
        return {'FINISHED'}

class OBJECT_OT_hero(bpy.types.Operator):
    bl_idname = "object.hero"
    bl_label = "OCD Hero"
    bl_description = "Activate HERO Mode"
    bl_options = {'UNDO'}

    def load_node_group(self, blend_file_path):
        """ Load the node group from the specified blend file. """
        with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
            if "OCD_Hero" in data_from.node_groups:
                data_to.node_groups = ["OCD_Hero"]
            else:
                return None
        return bpy.data.node_groups.get("OCD_Hero", None)

    def get_unique_node_group_name(self, base_name):
        """ Generate a unique node group name. """
        counter = 1
        unique_name = base_name
        while bpy.data.node_groups.get(unique_name) is not None:
            unique_name = f"{base_name}.{str(counter).zfill(3)}"
            counter += 1
        return unique_name

    def invoke(self, context, event):
        if event.ctrl:
            bpy.ops.wm.call_menu(name="GEONODES_MT_CustomMenu")
            return {'FINISHED'}
        else:
            addon_path = os.path.dirname(os.path.realpath(__file__))
            blend_file_path = os.path.join(addon_path, 'data.blend')

            # Use the existing node group if it's already in the scene
            node_group = bpy.data.node_groups.get("OCD_Hero", None)

            # If the node group is not found, try loading it from the file
            if not node_group:
                if not os.path.isfile(blend_file_path):
                    self.report({'ERROR'}, "data.blend file not found")
                    return {'CANCELLED'}
                try:
                    node_group = self.load_node_group(blend_file_path)
                    if not node_group:
                        self.report({'ERROR'}, "Node group 'OCD_Hero' not found or failed to load.")
                        return {'CANCELLED'}
                except Exception as e:
                    self.report({'ERROR'}, str(e))
                    return {'CANCELLED'}

            unique_name = self.get_unique_node_group_name("OCD_Hero")

            # Copy the node group with a unique name
            node_group_copy = node_group.copy()
            node_group_copy.name = unique_name

            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    #bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    mod = obj.modifiers.new(name="OCD_HERO", type='NODES')
                    mod.node_group = node_group_copy
            return {'FINISHED'}

is_focus_mode = False
is_local_view = False

class OBJECT_OT_focus(bpy.types.Operator):
    bl_idname = "object.focus"
    bl_label = "HERO Focus"
    bl_description = "Focus on Selected HERO object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        global is_local_view
        # Check if the Ctrl key was pressed during the operator's invocation
        if event.ctrl:
            # Perform focus on selected and toggle local view
            bpy.ops.view3d.localview()
            is_local_view = True
        # Proceed to execute the rest of the operator's logic
        return self.execute(context)

    def execute(self, context):
        global is_focus_mode

        selected_obj = context.active_object

        if not selected_obj:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}

        # Get the node tree of the selected object's Geometry Nodes modifier
        selected_node_tree = next((mod.node_group for mod in selected_obj.modifiers if mod.type == 'NODES' and mod.node_group.name.startswith("OCD_Hero")), None)

        if not selected_node_tree:
            self.report({'WARNING'}, "Selected object does not have a 'OCD_HERO' Geometry Nodes modifier")
            return {'CANCELLED'}

        # Count objects with 'OCD_HERO' GN modifiers sharing the same node tree
        matching_objects = [obj for obj in bpy.data.objects if any(mod for mod in obj.modifiers if mod.type == 'NODES' and mod.node_group == selected_node_tree)]

        # Skip focus mode if there's only one such object
        if len(matching_objects) <= 1:
            return {'FINISHED'}

        # Toggle the focus state
        is_focus_mode = not is_focus_mode

        if is_focus_mode:
            self.apply_focus(context, selected_node_tree)
        else:
            self.clear_focus(context, selected_node_tree)

        return {'FINISHED'}

    def apply_focus(self, context, selected_node_tree):
        selected_objects = context.selected_objects
        if not selected_objects:
            return

        for obj in bpy.data.objects:
            if obj not in selected_objects:
                for mod in obj.modifiers:
                    if mod.type == 'NODES' and mod.node_group == selected_node_tree:
                        mod.show_viewport = False

    def clear_focus(self, context, selected_node_tree):
        global is_local_view
        if is_local_view:
            bpy.ops.view3d.localview()
            is_local_view = False
        for obj in bpy.data.objects:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group == selected_node_tree:
                    mod.show_viewport = True

class OBJECT_OT_selection(bpy.types.Operator):
    bl_idname = "object.selection"
    bl_label = "HERO Select"
    bl_description = "Select similar HERO objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_obj = context.active_object

        if not selected_obj:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}

        # Get the node tree of the Geometry Nodes modifier from the selected object
        selected_node_tree = next((mod.node_group for mod in selected_obj.modifiers if mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("OCD_Hero")), None)

        if not selected_node_tree:
            self.report({'WARNING'}, "Selected object does not have a 'OCD_HERO' Geometry Nodes modifier with a valid node tree")
            return {'CANCELLED'}

        # Also check for objects in the same collections as the selected object
        collections_containing_selected_obj = [coll for coll in bpy.data.collections if selected_obj.name in coll.objects]

        # Iterate through all collections that contain the selected object
        for coll in collections_containing_selected_obj:
            for obj in coll.objects:
                # Check each object's modifiers for a matching node tree
                for mod in obj.modifiers:
                    if mod.type == 'NODES' and mod.node_group == selected_node_tree:
                        obj.select_set(True)
        #active object remains active 
        context.view_layer.objects.active = selected_obj

        return {'FINISHED'}

copied_node_tree_name = ""

class OBJECT_OT_copy(bpy.types.Operator):
    bl_idname = "object.copy"
    bl_label = "HERO Copy"
    bl_description = "Copy HERO Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global copied_node_tree_name
        selected_obj = context.active_object

        if not selected_obj:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}

        # Find the node tree from the selected object's "OCD_HERO" modifier
        node_tree = next((mod.node_group for mod in selected_obj.modifiers if mod.type == 'NODES' and mod.node_group.name.startswith("OCD_Hero")), None)

        if not node_tree:
            self.report({'WARNING'}, "Selected object does not have a suitable 'OCD_HERO' Geometry Nodes modifier")
            return {'CANCELLED'}

        # Copy the node tree name
        copied_node_tree_name = node_tree.name
        self.report({'INFO'}, f"Copied GN tree: {copied_node_tree_name}")

        return {'FINISHED'}

class OBJECT_OT_paste(bpy.types.Operator):
    bl_idname = "object.paste"
    bl_label = "HERO Paste"
    bl_description = "Paste HERO Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global copied_node_tree_name

        if not context.selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        if not copied_node_tree_name:
            self.report({'WARNING'}, "No Geometry Nodes tree copied")
            return {'CANCELLED'}

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            # Find or create the "OCD_HERO" modifier
            ocd_hero_mod = next((mod for mod in obj.modifiers if mod.type == 'NODES' and mod.node_group.name.startswith("OCD_Hero")), None)
            if not ocd_hero_mod:
                ocd_hero_mod = obj.modifiers.new(name="OCD_HERO", type='NODES')

            # Assign the copied node tree
            ocd_hero_mod.node_group = bpy.data.node_groups.get(copied_node_tree_name, None)
            if not ocd_hero_mod.node_group:
                self.report({'WARNING'}, f"Node tree '{copied_node_tree_name}' not found in this file")
                return {'CANCELLED'}
        
        return {'FINISHED'}

class OBJECT_OT_hero_to_mesh(Operator):
    """Convert selected HERO objects to Mesh"""
    bl_idname = "object.hero_to_mesh"
    bl_label = "HERO to Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            # Ensure the object is the active object
            context.view_layer.objects.active = obj
            bpy.ops.object.convert(target='MESH')
        return {'FINISHED'}

class OBJECT_OT_remove_ocd_hero(Operator):
    bl_idname = "object.remove_ocd_hero"
    bl_label = "Remove Modifiers with OCD Hero Node Tree"
    bl_description = "Remove HERO from selected object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        removed_count = 0

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            # Iterate over modifiers and remove those whose node tree name starts with "OCD_Hero"
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("OCD_Hero"):
                    obj.modifiers.remove(mod)
                    removed_count += 1

        if removed_count == 0:
            self.report({'INFO'}, "No modifiers with 'OCD_HERO' node tree found on selected objects")
        else:
            self.report({'INFO'}, f"Removed {removed_count} modifiers with 'OCD_HERO'")

        return {'FINISHED'}

class OBJECT_OT_turn_on_hero(bpy.types.Operator):
    bl_idname = "object.turn_on_hero"
    bl_label = "Turn HERO On"
    bl_description = "Turn On HERO Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("OCD_Hero"):
                    mod.show_viewport = True  # Enable the modifier in the viewport
                    #mod.show_render = True  # Enable the modifier for rendering
        return {'FINISHED'}

class OBJECT_OT_turn_off_hero(bpy.types.Operator):
    bl_idname = "object.turn_off_hero"
    bl_label = "Turn HERO Off"
    bl_description = "Turn Off HERO Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.selected_objects:
            for mod in obj.modifiers:
                if mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("OCD_Hero"):
                    mod.show_viewport = False  # Disable the modifier in the viewport
                    #mod.show_render = False  # Disable the modifier for rendering
        return {'FINISHED'}


def node_hero_add(context, filepath, node_group, ungroup, report, mouse_x, mouse_y):
    space = context.space_data
    node_tree = space.node_tree
    node_active = context.active_node
    node_selected = context.selected_nodes

    if node_tree is None:
        report({'ERROR'}, "No node tree available")
        return

    # Check if the node group is already present in the current file
    existing_node_group = bpy.data.node_groups.get(node_group)
    if existing_node_group:
        node_group = existing_node_group
    else:
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            assert(node_group in data_from.node_groups)
            data_to.node_groups = [node_group]
        node_group = data_to.node_groups[0]

    # add node!
    for node in node_tree.nodes:
        node.select = False

    node_type_string = {
        "GeometryNodeTree": "GeometryNodeGroup",
    }[type(node_tree).__name__]

    node = node_tree.nodes.new(type=node_type_string)
    node.node_tree = node_group
    node.name = node_group.name  # Set the node name to the actual group name
    node.location = Vector((mouse_x, mouse_y))

    is_fail = (node.node_tree is None)
    if is_fail:
        report({'WARNING'}, "Incompatible node type")

    node.select = True
    node_tree.nodes.active = node

    if is_fail:
        node_tree.nodes.remove(node)
    else:
        if ungroup:
            bpy.ops.node.group_ungroup()

class NODE_OT_Hero_add(Operator):
    bl_idname = "node.hero_add"
    bl_label = "Add Hero node group"
    bl_description = "Add Hero node"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(
        subtype='FILE_PATH',
    )
    group_name: StringProperty()
    ungroup: bpy.props.BoolProperty(default=False)

    y: bpy.props.FloatProperty()
    x: bpy.props.FloatProperty()

    def execute(self, context):
        if bpy.app.version < (4, 0, 0):
            self.report({'ERROR'}, "HERO module requires Blender 4.0.0 or higher")
            return {'CANCELLED'}
        else:
            node_hero_add(context, self.filepath, self.group_name, self.ungroup, self.report, self.x, self.y)
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            return {'FINISHED'}

    def invoke(self, context, event):
        region = context.region.view2d
        ui_scale = context.preferences.system.ui_scale
        x, y = region.region_to_view(event.mouse_region_x, event.mouse_region_y)
        self.x, self.y = x / ui_scale, y / ui_scale
        self.ungroup = event.shift
        return self.execute(context) 

class NODE_MT_Hero_main(Menu):
    bl_label = "OCD HERO"

    def draw(self, context):
        layout = self.layout

        mask_node_items = [("data.blend", "HERO - Noise Mask"), ("data.blend", "HERO - Gradient Mask"), ("data.blend", "HERO - Material Mask"), ("data.blend", "HERO - Normal Mask"), ("data.blend", "HERO - Obj Pos Mask")]
        utils_node_items = [("data.blend", "HERO - Texture Transform"), ("data.blend", "HERO - Trimesh"), ("data.blend", "HERO - Blur"), ("data.blend", "HERO - Mask Inverse"), ("data.blend", "HERO - Mask Combine")]
        main_node_items = [("data.blend", "HERO - Start"), ("data.blend", "HERO - End"), ("data.blend", "HERO - Displace"), ("data.blend", "HERO - Scatter"), ("data.blend", "HERO - Image Displace")]
        
        main_menu = layout.menu(NODE_MT_Hero_main_nodes.__name__, text="Mains")
        mask_menu = layout.menu(NODE_MT_Hero_mask.__name__, text="Masks")
        utils_menu = layout.menu(NODE_MT_Hero_utils.__name__, text="Utils")

class NODE_MT_Hero_mask(Menu):
    bl_label = "Masks"
    def draw(self, context):
        layout = self.layout
        mask_node_items = [("data.blend", "HERO - Noise Mask"), ("data.blend", "HERO - Gradient Mask"), ("data.blend", "HERO - Material Mask"), ("data.blend", "HERO - Normal Mask"), ("data.blend", "HERO - Obj Pos Mask")]

        for blend_filename, label in mask_node_items:
            filepath = get_blend_file_path(blend_filename)
            if os.path.isfile(filepath):
                with bpy.data.libraries.load(filepath) as (data_from, data_to):
                    for group_name in data_from.node_groups:
                        if group_name == label:
                            props = layout.operator(
                                NODE_OT_Hero_add.bl_idname,
                                text=label,
                            )
                            props.filepath = filepath
                            props.group_name = group_name
            else:
                layout.label(text=f"{label}: .blend file not found", icon='ERROR')        

class NODE_MT_Hero_utils(Menu):
    bl_label = "Utils"
    def draw(self, context):
        layout = self.layout
        utils_node_items = [("data.blend", "HERO - Texture Transform"), ("data.blend", "HERO - Trimesh"), ("data.blend", "HERO - Blur"), ("data.blend", "HERO - Mask Inverse"), ("data.blend", "HERO - Mask Combine")]

        for blend_filename, label in utils_node_items:
            filepath = get_blend_file_path(blend_filename)
            if os.path.isfile(filepath):
                with bpy.data.libraries.load(filepath) as (data_from, data_to):
                    for group_name in data_from.node_groups:
                        if group_name == label:
                            props = layout.operator(
                                NODE_OT_Hero_add.bl_idname,
                                text=label,
                            )
                            props.filepath = filepath
                            props.group_name = group_name
            else:
                layout.label(text=f"{label}: .blend file not found", icon='ERROR')        

class NODE_MT_Hero_main_nodes(Menu):
    bl_label = "Mains"
    def draw(self, context):
        layout = self.layout
        main_node_items = [("data.blend", "HERO - Start"), ("data.blend", "HERO - End"), ("data.blend", "HERO - Displace"), ("data.blend", "HERO - Scatter"), ("data.blend", "HERO - Image Displace")]

        for blend_filename, label in main_node_items:
            filepath = get_blend_file_path(blend_filename)
            if os.path.isfile(filepath):
                with bpy.data.libraries.load(filepath) as (data_from, data_to):
                    for group_name in data_from.node_groups:
                        if group_name == label:
                            props = layout.operator(
                                NODE_OT_Hero_add.bl_idname,
                                text=label,
                            )
                            props.filepath = filepath
                            props.group_name = group_name
            else:
                layout.label(text=f"{label}: .blend file not found", icon='ERROR')    

def add_hero_node_button(self, context):
    space = context.space_data
    if space.type == 'NODE_EDITOR' and space.tree_type == 'GeometryNodeTree':
        self.layout.menu(
            NODE_MT_Hero_main.__name__,
            text="OCD Hero",
            icon='EVENT_H',
        )

class OBJECT_PT_OCD_panel(Panel):
    bl_label = 'One Click Damage v2.0'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'OCD 2'
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        obj = context.active_object
        props = context.scene.dmgamnt
        damage_amount = props.damage_amount
        scale_amount = props.scale_amount
        dmgamnt = context.scene.dmgamnt
        prefs = context.preferences.addons[__name__.partition('.')[0]].preferences

        targetNameProp = obj.name + '_temp' if obj is not None else ""
        row = layout.row()
        row.scale_y = 2.0

        selected_objects = context.selected_objects
        # Check if any objects are selected
        if not selected_objects:
            row.operator("object.ocd_on", text='Make Damage', depress=True)
            layout.separator()
            hero_box = layout.column()
            hero_row = hero_box.row()
            hero_box.scale_y = 2.0
            hero_row.operator("object.hero", text="GO HERO", depress=True)
            return  # No more processing if no objects are selected

        boolean_mod = next((mod for mod in obj.modifiers if mod.name == 'OCD_Boolean'), None) if obj is not None else None

        # Check if all objects have the 'OCD_applied' property
        all_have_property = all(obj.get("OCD_applied", False) for obj in selected_objects)

        if all_have_property:
            # Create a box for these specific controls
            control_box = layout.box()
            col = control_box.column()

            row = col.row()
            row.scale_y = 2.0
            row.operator("object.recall_original", text="Recall")
            
            # Change Pattern button with increased scale
            row = col.row()
            row.scale_y = 2.0
            row.operator("object.randomize", text="Change Pattern")

            # QuickFix button with increased scale
            row = col.row()
            row.scale_y = 1.5
            row.operator("object.find_mesh_errors", text='QuickFix')

        elif boolean_mod:  
            row.operator("object.ocd_off", text='Cancel', icon = "CANCEL", depress=False)
            col = layout.column()
            col.prop(props, "scale_amount", text='Scale')
            col.prop(props, "damage_amount")
            col.label(text="Noise type:")
            col.prop(dmgamnt, "noise_type", text="")
            row = layout.row()
            row.operator("object.damage_transform", text = "Pos", icon = "ORIENTATION_VIEW")
            
            if prefs.mat_name_2 == 'NONE' or prefs.mat_name_2 == prefs.mat_name_1:
                mat_icon = "ANTIALIASED"  
            else:
                mat_icon = "MATERIAL"

            row.operator("object.materials_selection", text="Mat", icon=mat_icon)
            row.operator("object.open_docs", text = "Help", icon = "HELP")
            row.operator("object.open_addon_preferences", text="", icon = "PREFERENCES")
            row = layout.row()
            row.scale_y = 1.5
            row.operator("object.apply_all_mods", text="Apply", icon = "CHECKMARK", depress=True)
        else:
            row.operator("object.ocd_on", text='Make Damage', depress=True)

        layout.separator()

        boolean_mod = any(mod for mod in obj.modifiers if mod.type == 'BOOLEAN' and mod.name == 'OCD_Boolean') if obj else False
        ocd_hero_mod = any(mod for obj in selected_objects for mod in obj.modifiers if mod.type == 'NODES' and mod.node_group and mod.node_group.name.startswith("OCD_Hero")) 

        # Draw the "GO HERO" button only if neither condition is met
        if not (boolean_mod or ocd_hero_mod):
            hero_box = layout.column()
            hero_row = hero_box.row()
            hero_box.scale_y = 2.0
            hero_row.operator("object.hero", text="GO HERO", depress=True)

        # Draw the HERO Control Panel
        if ocd_hero_mod:
            # Create a box for the HERO Control Panel
            hero_control_panel = layout.box()
            col = hero_control_panel.column()

            col.label(text="HERO Control Panel:", icon='PROPERTIES')

            # Row with Focus and Select All buttons
            row = col.row()
            # Choose the icon based on is_focus_mode state
            focus_icon = 'OUTLINER_OB_LIGHT' if is_focus_mode else 'LIGHT_DATA'
            row.operator("object.focus", text="Focus", icon=focus_icon)
            row.operator("object.selection", text="Select All")

            # Separate line
            col.separator()

            # Copy button
            col.operator("object.copy", text="Copy")
            
            # Paste button
            col.operator("object.paste", text="Paste")

            # Separate line
            col.separator()

            # Row with Focus and Select All buttons
            row = col.row()
            row.operator("object.turn_on_hero", text="On", icon='HIDE_OFF')
            row.operator("object.turn_off_hero", text="Off", icon='HIDE_ON')
            
            # Separate line
            col.separator()
            
            # Remove button with increased scale
            row = col.row()
            row.scale_y = 2.0
            row.operator("object.hero_to_mesh", text="To Mesh", icon='CHECKMARK', depress=True)

            # Remove button with increased scale
            row = col.row()
            row.scale_y = 2.0
            row.operator("object.remove_ocd_hero", text="Remove", icon='CANCEL')
        
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = [
    DamageProps,
    StoredValueProp,
    OCD_Preferences,
    OBJECT_OT_damageON,
    OBJECT_OT_damageOFF,
    OBJECT_OT_apply,
    OBJECT_OT_recall,
    OBJECT_OT_damage_transform,
    MATERIALS_MT_CustomMenu,
    OBJECT_OT_materials,
    OBJECT_OT_open_docs,
    OBJECT_OT_open_addon_preferences,
    GEONODES_MT_CustomMenu,
    OBJECT_OT_AssignHeroNodeTree,
    OBJECT_OT_hero,
    OBJECT_OT_focus,
    OBJECT_OT_selection,
    OBJECT_OT_copy,
    OBJECT_OT_paste,
    OBJECT_OT_hero_to_mesh,
    OBJECT_OT_remove_ocd_hero,
    OBJECT_OT_turn_on_hero,
    OBJECT_OT_turn_off_hero,
    NODE_OT_Hero_add,
    NODE_MT_Hero_main,
    NODE_MT_Hero_mask,
    NODE_MT_Hero_utils,
    NODE_MT_Hero_main_nodes,
    OBJECT_PT_OCD_panel,
    OBJECT_OT_random,
    OBJECT_OT_find_mesh_errors,
    ]

def register():
    for cl in classes:
       register_class(cl)

    bpy.types.NODE_MT_add.append(add_hero_node_button)
    bpy.types.Scene.dmgamnt = PointerProperty(type = DamageProps)
    bpy.types.Object.stored_value = PointerProperty(type = StoredValueProp)
    
       
def unregister():
    for cl in reversed(classes):
        unregister_class(cl)
    
    bpy.types.NODE_MT_add.remove(add_hero_node_button)
    del bpy.types.Scene.dmgamnt
    del bpy.types.Object.stored_value