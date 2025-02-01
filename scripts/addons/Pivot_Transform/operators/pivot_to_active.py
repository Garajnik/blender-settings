import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty




class PIVOT_OT_to_active(Operator):
    bl_idname = "pivot.to_active"
    bl_label = "Align Position"
    bl_description = "Align Location Pivot Of Selected Objects From Active Object"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name='Axis',
        items=[
            ('X', 'X Axis', '', '', 0),
            ('Y', 'Y Axis', '', '', 1),
            ('Z', 'Z Axis', '', '', 2),
            ('ALL', 'All Axis', '', '', 3)],
        default='X',
        )

    #rotation: BoolProperty( name = 'Rotation', default = False )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'


    def execute(self, context):
        activeObj = context.active_object
        activeLoc = activeObj.location

        cursor_pos = context.scene.cursor.location.copy()
        
        selObject = context.selected_objects

        bpy.ops.object.select_all(action='DESELECT')

        for obj in selObject:
            context.scene.cursor.location = obj.location
            obj.select_set(state=True)

            if self.axis == 'X':
                context.scene.cursor.location[0] = activeLoc[0]
            elif self.axis == 'Y':
                context.scene.cursor.location[1] = activeLoc[1]
            elif self.axis == 'Z':
                context.scene.cursor.location[2] = activeLoc[2]
            else:
                context.scene.cursor.location = activeLoc

            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            obj.select_set(state=False)

        for obj in selObject:
            obj.select_set(state=True)
        context.view_layer.objects.active = activeObj

        context.scene.cursor.location = cursor_pos
        return {'FINISHED'} 





classes = [
    PIVOT_OT_to_active,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)