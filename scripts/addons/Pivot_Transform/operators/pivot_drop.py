import bpy, blf
from bpy.types import Operator



def draw_text(self, context):
    font_info = {
        'font_id': 0,
        'handler': None,
    }

    # Для смещения тексто во избежание наложения
    settings = context.scene.pivot_set
    if settings.flow:
        height_offset = 250
    else:
        height_offset = 100

    font_id_name = font_info['font_id']
    #header_height = context.area.regions[0].height # 26px
    width = context.area.regions[2].width + 10
    height = height_offset #context.area.height - header_height - height_offset
    name = 'Pivot Drop'
    blf.position(font_id_name, width, height, 0)
    blf.size(font_id_name, 30)
    blf.color(font_id_name, 0.58, 0.72, 0.0, 1.0)
    blf.draw(font_id_name, name)
    #blf.shadow(font_id_name, 6, 0.0, 0.0, 0.0, 1.0)



    font_id_apply = font_info['font_id']
    #header_height = context.area.regions[0].height # 26px
    #width = context.area.regions[2].width + 10
    height = height_offset - 50
    apply_text = "Add Snap Point: 'A'"
    blf.position(font_id_apply, width, height, 0)
    blf.size(font_id_apply, 16)
    blf.color(font_id_apply, 1.0, 1.0, 1.0, 1.0)
    blf.draw(font_id_apply, apply_text)
    
    font_id_apply = font_info['font_id']
    #header_height = context.area.regions[0].height # 26px
    #width = context.area.regions[2].width + 10
    height = height_offset - 70
    apply_text = "Remove Last Snap Point: 'ALT+A'"
    blf.position(font_id_apply, width, height, 0)
    blf.size(font_id_apply, 16)
    blf.color(font_id_apply, 1.0, 1.0, 1.0, 1.0)
    blf.draw(font_id_apply, apply_text)
    



# Оператор для избежания неправильного позиционирования итогового результата
class PIVOT_OT_drop(Operator):
    bl_idname = "pivot.drop"
    bl_label = "Pivot Drop"
    bl_description = "Drop Pivot Point Using Sanpping Options"
    bl_option = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.pivot.mod('INVOKE_DEFAULT')
        bpy.ops.transform.translate('INVOKE_DEFAULT')
        return {'FINISHED'}



# Оператор для отображения текста и выставления настроек
class PIVOT_OT_mod(Operator):
    bl_idname = "pivot.mod"
    bl_label = "Pivot Modal Mod"

    def __init__(self):
        self.store_list = {}
        self.store_snap = False
        self.stor_align_rot = False
        self.edit_mode = False
        self.snap_target = []




    def modal(self, context, event):
        #context.area.tag_redraw()

        if event.type in {'LEFTMOUSE','RET', 'RIGHTMOUSE','ESC'}:
            context.scene.tool_settings.snap_elements = self.store_list
            context.scene.tool_settings.use_snap = self.store_snap
            context.scene.tool_settings.use_snap_align_rotation = self.stor_align_rot
            context.scene.tool_settings.snap_target = self.snap_target


            settings = bpy.context.scene.pivot_set
            if settings.flow == False:
                context.scene.tool_settings.use_transform_data_origin = False

            if self.edit_mode == True:
                bpy.ops.object.mode_set(mode='EDIT')


            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}


        return {'PASS_THROUGH'}


    def invoke(self, context, event):
        props = context.preferences.addons['Pivot_Transform'].preferences
        if context.area.type == 'VIEW_3D':
            if context.mode == 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='OBJECT')
                self.edit_mode = True


            self.store_list = context.scene.tool_settings.snap_elements
            context.scene.tool_settings.snap_elements = props.snap_elements

            self.store_snap = context.scene.tool_settings.use_snap
            context.scene.tool_settings.use_snap = True

            self.stor_align_rot = context.scene.tool_settings.use_snap_align_rotation
            context.scene.tool_settings.use_snap_align_rotation = True

            self.snap_target = context.scene.tool_settings.snap_target
            context.scene.tool_settings.snap_target = 'CLOSEST'
            


            context.scene.tool_settings.use_transform_data_origin = True

       


            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_text, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        else:
            return{'CANCELLED'}


classes = [
    PIVOT_OT_drop,
    PIVOT_OT_mod,
    ]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)