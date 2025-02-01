import bpy
from bpy.types import Operator



class PT_OT_panel_settings(Operator): # --- Open Panel Settings
    bl_idname = 'pt.panel_settings'
    bl_label = 'Pivot Transform Settings'
    bl_description = ''
    bl_options = {'INTERNAL'}

    def execute(self, context):
        bpy.ops.screen.userpref_show()
        context.preferences.active_section = 'ADDONS'
        bpy.data.window_managers["WinMan"].addon_search = 'Pivot Transform'
        return {'FINISHED'}



classes = [
    PT_OT_panel_settings,
    ]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)