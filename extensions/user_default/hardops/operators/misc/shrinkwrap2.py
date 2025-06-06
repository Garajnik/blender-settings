import bpy
from ... utility import addon
from ...ui_framework.operator_ui import Master

class HOPS_OT_Shrinkwrap(bpy.types.Operator):
    bl_idname = "hops.shrinkwrap2"
    bl_label = "Hops Shrinkwrap2"
    bl_description = "Shrinkwrap selected mesh"
    bl_options = {"REGISTER", "UNDO"}

    called_ui = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        HOPS_OT_Shrinkwrap.called_ui = False

    @classmethod
    def poll(cls, context):
        object = context.active_object
        if object is None: return False
        if object.mode == "OBJECT" and object.type == "MESH":
            return True

    def execute(self, context):
        object = context.active_object
        objects = context.selected_objects

        for obj in objects:
            if obj.name != object.name:

                mod = obj.modifiers.new("Shrinkwrap", "SHRINKWRAP")
                mod.target = object

        # Operator UI
        if not HOPS_OT_Shrinkwrap.called_ui:
            HOPS_OT_Shrinkwrap.called_ui = True

            ui = Master()
            draw_data = [
                ["Shrink To"],
                ["Secondary selection shrinkwrapped to primary"]]
            ui.receive_draw_data(draw_data=draw_data)
            ui.draw(draw_bg=addon.preference().ui.Hops_operator_draw_bg, draw_border=addon.preference().ui.Hops_operator_draw_border)

        return {"FINISHED"}
