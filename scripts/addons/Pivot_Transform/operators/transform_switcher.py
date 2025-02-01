import bpy
from bpy.types import Operator


storeGT = False
storeGR = False
storeGS = False
context_mode = 'OBJECT'



class PIVOT_OT_transform_on(Operator):
    bl_idname = "pivot.transform_on"
    bl_label = "Transform"
    bl_description = "Start Pivot Transformation"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0


    def execute(self, context):
        global context_mode

        if context.mode != 'OBJECT': # and context.object.select_get()
            bpy.ops.object.mode_set(mode='OBJECT')
            context_mode = 'EDIT'
        else:
            context_mode = 'OBJECT'


        if context.scene.tool_settings.use_transform_data_origin == False:
            props = context.preferences.addons['Pivot_Transform'].preferences

            global storeGT
            global storeGR
            global storeGS

            storeGT = context.space_data.show_gizmo_object_translate
            storeGR = context.space_data.show_gizmo_object_rotate 
            storeGS = context.space_data.show_gizmo_object_scale 

            if props.gizmo_preselect:
                context.space_data.show_gizmo_object_translate = props.move_giz
                context.space_data.show_gizmo_object_rotate = props.rotate_giz
                context.space_data.show_gizmo_object_scale = props.scale_giz

                
            context.scene.tool_settings.use_transform_data_origin = True
            return{'FINISHED'}
        else:
            return{'CANCELLED'}



class PIVOT_OT_transform_off(Operator):
    bl_idname = "pivot.transform_off"
    bl_label = "Apply"
    bl_description = "Apply Pivot Transformation"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0


    def execute(self, context):
        global context_mode

        if context.mode != 'OBJECT': 
            bpy.ops.object.mode_set(mode='OBJECT')
        """     context_mode = 'EDIT'
        else:
            context_mode = 'OBJECT' """

        if context.scene.tool_settings.use_transform_data_origin:
            # PIVOT FLOW
            settings = context.scene.pivot_set
            if settings.flow:
                settings.flow = False


            global storeGT
            global storeGR
            global storeGS

            context.space_data.show_gizmo_object_translate = storeGT
            context.space_data.show_gizmo_object_rotate = storeGR
            context.space_data.show_gizmo_object_scale = storeGS

            

            context.scene.tool_settings.use_transform_data_origin = False

        
            bpy.ops.object.mode_set(mode=context_mode)
            return{'FINISHED'}
        else:
            return{'CANCELLED'}












classes = [ 
    PIVOT_OT_transform_on,
    PIVOT_OT_transform_off,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


    global storeGT
    global storeGR
    global storeGS


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls) 