import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from bpy.props import StringProperty

import os

from ..utils import SBConstants, specials_selection_to_list, get_base_folder_patho
from ..messages import print_message
def auto_set_bake_margin():
    
    context = bpy.context
    
    multiplier = 4
    
    current_width = context.scene.SimpleBake_Props.imgwidth
    margin = (current_width / 1024) * multiplier
    margin = round(margin, 0)
    
    context.scene.render.bake.margin = int(margin)

    return True



class SimpleBake_OT_selectall_pbr(Operator):
    """Select all PBR bake types"""
    bl_idname = "simplebake.selectall_pbr"
    bl_label = "Select All"
    
    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        sbp.selected_col = True
        sbp.selected_metal = True
        sbp.selected_rough = True
        sbp.selected_normal = True
        sbp.selected_trans = True
        sbp.selected_transrough = True
        sbp.selected_emission = True
        sbp.selected_emission_strength = True
        sbp.selected_clearcoat = True
        sbp.selected_clearcoat_rough = True
        sbp.selected_specular = True
        sbp.selected_alpha = True
        sbp.selected_sss = True
        sbp.selected_ssscol = True
        sbp.selected_bump = True
        sbp.selected_displacement = True
        return {'FINISHED'}

class SimpleBake_OT_selectnone_pbr(Operator):
    """Select none PBR bake types"""
    bl_idname = "simplebake.selectnone_pbr"
    bl_label = "Select None"
    
    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        sbp.selected_col = False
        sbp.selected_metal = False
        sbp.selected_rough = False
        sbp.selected_normal = False
        sbp.selected_trans = False
        sbp.selected_transrough = False
        sbp.selected_emission = False
        sbp.selected_emission_strength = False
        sbp.selected_clearcoat = False
        sbp.selected_clearcoat_rough = False
        sbp.selected_specular = False
        sbp.selected_sss = False
        sbp.selected_ssscol = False
        sbp.selected_bump = False
        sbp.selected_displacement = False
        if not (sbp.selected_s2a == True and sbp.s2a_opmode == "decals"):
            sbp.selected_alpha = False
        return {'FINISHED'}

class SimpleBake_OT_increase_texture_res(Operator):
    """Increase texture resolution by 1k"""
    bl_idname = "simplebake.increase_texture_res"
    bl_label = "+1k"


    def execute(self, context):
        
        sbp = context.scene.SimpleBake_Props
        
        x = sbp.imgwidth
        sbp.imgwidth = x + 1024
        y = sbp.imgheight
        sbp.imgheight = y + 1024
            
        while sbp.imgheight % 1024 != 0:
            sbp.imgheight -= 1
        
        while sbp.imgwidth % 1024 != 0:
            sbp.imgwidth -= 1
        
        result = min(sbp.imgwidth, sbp.imgheight)
        sbp.imgwidth = result
        sbp.imgheight = result
        
        auto_set_bake_margin()
        
        return {'FINISHED'} 

class SimpleBake_OT_decrease_texture_res(Operator):
    """Decrease texture resolution by 1k"""
    bl_idname = "simplebake.decrease_texture_res"
    bl_label = "-1k"


    def execute(self, context):
        
        sbp = context.scene.SimpleBake_Props
        
        x = sbp.imgwidth
        sbp.imgwidth = x - 1024
        y = sbp.imgheight
        sbp.imgheight = y - 1024
        
        if sbp.imgheight < 1:
            sbp.imgheight = 1024
        
        if sbp.imgwidth < 1:
            sbp.imgwidth = 1024
        
        while sbp.imgheight % 1024 != 0:
            sbp.imgheight += 1
        
        while sbp.imgwidth % 1024 != 0:
            sbp.imgwidth += 1
        
        result = max(sbp.imgwidth, sbp.imgheight)
        sbp.imgwidth = result
        sbp.imgheight = result
        
        auto_set_bake_margin()
            
        return {'FINISHED'} 
    
class SimpleBake_OT_increase_output_res(Operator):
    """Increase output resolution by 1k"""
    bl_idname = "simplebake.increase_output_res"
    bl_label = "+1k"

    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        
        x = sbp.outputwidth
        sbp.outputwidth = x + 1024
        y = sbp.outputheight
        sbp.outputheight = y + 1024

        while sbp.outputheight % 1024 != 0:
            sbp.outputheight -= 1
        
        while sbp.outputwidth % 1024 != 0:
            sbp.outputwidth -= 1
        
        result = min(sbp.outputwidth, sbp.outputheight)
        sbp.outputwidth = result
        sbp.outputheight = result

        auto_set_bake_margin()
        
        return {'FINISHED'} 

class SimpleBake_OT_decrease_output_res(Operator):
    """Decrease output resolution by 1k"""
    bl_idname = "simplebake.decrease_output_res"
    bl_label = "-1k"

    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        
        x = sbp.outputwidth
        sbp.outputwidth = x - 1024
        y = sbp.outputheight
        sbp.outputheight = y - 1024
        
        if sbp.outputheight < 1:
            sbp.outputheight = 1024
        
        if sbp.outputwidth < 1:
            sbp.outputwidth = 1024
            
            
        while sbp.outputheight % 1024 != 0:
            sbp.outputheight += 1
        
        while sbp.outputwidth % 1024 != 0:
            sbp.outputwidth += 1
        
        result = max(sbp.outputwidth, sbp.outputheight)
        sbp.outputwidth = result
        sbp.outputheight = result
        
        auto_set_bake_margin()
        
        return {'FINISHED'} 
    
class SimpleBake_OT_panel_show_all(Operator):
    """Show all SimpleBake panel items"""
    bl_idname = "simplebake.panel_show_all"
    bl_label = "Show all"


    def execute(self, context):
        
        sbp = context.scene.SimpleBake_Props
        
        sbp.showtips = True
        sbp.presets_show = True
        sbp.bake_objects_show = True
        sbp.pbr_settings_show = True
        sbp.cyclesbake_settings_show = True
        sbp.specials_show = True
        sbp.textures_show = True
        sbp.export_show = True
        sbp.uv_show = True
        sbp.other_show = True
        sbp.channelpacking_show = True
            
        return {'FINISHED'} 
        
class SimpleBake_OT_panel_hide_all(Operator):
    """Hide all SimpleBake panel items"""
    bl_idname = "simplebake.panel_hide_all"
    bl_label = "Hide all"


    def execute(self, context):
        
        sbp = context.scene.SimpleBake_Props
        
        sbp.showtips = False
        sbp.presets_show = False
        sbp.bake_objects_show = False
        sbp.pbr_settings_show = False
        sbp.cyclesbake_settings_show = False
        sbp.specials_show = False
        sbp.textures_show = False
        sbp.export_show = False
        sbp.uv_show = False
        sbp.other_show = False
        sbp.channelpacking_show = False
        
        return {'FINISHED'} 
    
    
class SimpleBake_OT_Import_Special_Mats(Operator):
    """Import the selected specials materials if you want to edit them. Once edited, they will be used for all bakes of that type in this file"""
    bl_idname = "simplebake.import_special_mats"
    bl_label = "Import specials materials"
    
    @classmethod
    def poll(cls,context):

        if context.mode != "OBJECT":
            return False
        
        specials_list = specials_selection_to_list(context)
        specials_list = [i for i in specials_list if i not in [SBConstants.VERTEXCOL, SBConstants.COLOURID]]
        
        if len(specials_list)>0:
            return True
        else:
            return False
    
    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        
        specials = specials_selection_to_list(context)
        
        for special in specials:
            import_mat_name = f"SimpleBake_{special}"
            if import_mat_name not in bpy.data.materials:
                path = os.path.dirname(__file__) + "/../resources/specials.blend/Material/"
                bpy.ops.wm.append(filename=import_mat_name, directory=path)
        
        self.report({"INFO"}, "Materials imported into scene. Create a dummy object and edit them. They will be used for Specials bakes of this type going forwards")
        
        return {'FINISHED'} 

class SimpleBake_OT_Protect_Clear(Operator):
    """If you are online, you likely need to complete the 'I am not a robot' check on the web server. Click here to do that. All will be explained..."""
    bl_idname = "simplebake.protect_clear"
    bl_label = "Launch web browser"
    
    def execute(self, context):
        import webbrowser
        webbrowser.open('http://www.toohey.co.uk/SimpleBake/protect_clear.html', new=2)
        
        return {'FINISHED'} 


class SimpleBake_OT_Export_Path_To_Blend_Location(Operator):
    """Set export path to the location of current blend file"""
    bl_idname = "simplebake.export_path_to_blend_location"
    bl_label = "Set"
 
    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        sbp.export_path = get_base_folder_patho(context).as_posix() + "/SimpleBake_Bakes"
        sbp.export_path = bpy.path.relpath(sbp.export_path)
        return {'FINISHED'}
 
    #def invoke(self, context, event):b
        #context.window_manager.fileselect_add(self)
        #return {'RUNNING_MODAL'}


classes = ([
    SimpleBake_OT_selectall_pbr,
    SimpleBake_OT_selectnone_pbr,
    SimpleBake_OT_increase_texture_res,
    SimpleBake_OT_decrease_texture_res,
    SimpleBake_OT_increase_output_res,
    SimpleBake_OT_decrease_output_res,
    SimpleBake_OT_panel_show_all,
    SimpleBake_OT_panel_hide_all,
    SimpleBake_OT_Import_Special_Mats,
    SimpleBake_OT_Protect_Clear,
    SimpleBake_OT_Export_Path_To_Blend_Location
        ])

def register():
    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
