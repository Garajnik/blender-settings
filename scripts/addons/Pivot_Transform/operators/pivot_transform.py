import bpy
from bpy.types import Operator
from mathutils import Euler
from bpy.props import BoolProperty


cursor_pos = (0,0,0)
cursor_rot = Euler()
source = None



#======================================================================== START
class PIVOT_OT_start(Operator):
    bl_idname = "pivot.start"
    bl_label = "Pivot Transform"
    bl_description = "Start Transformation"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.active_object


    def execute(self, context):
        cursor = context.scene.cursor
        
        global cursor_pos
        global cursor_rot
        cursor_pos = cursor.location.copy()
        cursor_rot = cursor.rotation_euler.copy()


        source = context.active_object
      
        cursor.location = source.delta_location + source.location
        mixMatrix = source.delta_rotation_euler.to_matrix() @ source.rotation_euler.to_matrix() 
        cursor.rotation_euler = mixMatrix.to_euler()

        return {'FINISHED'}



#======================================================================== APPLY
class PIVOT_OT_apply(Operator):
    bl_idname = "pivot.apply"
    bl_label = "Apply"
    bl_description = "Apply Transformation"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    cursor_reset: BoolProperty(name="Reset Cursor", default=True)
    rotation: BoolProperty(name="Rotation", default=True)

    @classmethod
    def poll(cls, context):
        return context.active_object
        
    
    def execute(self, context):
        global cursor_pos
        global cursor_rot


        cursor = context.scene.cursor
        source = context.active_object
       


        """ source.location = source.location + source.delta_location
        source.delta_location = (0.0, 0.0, 0.0) """

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            edit = True
        else:
            edit = False


        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')


        if self.rotation:
            rotate_mat = cursor.rotation_euler.to_matrix()
            double_mat = rotate_mat @ rotate_mat
            invert_mat = double_mat.inverted()


            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            source.delta_rotation_euler = cursor.rotation_euler
            source.rotation_euler = invert_mat.to_euler() 
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)


            source.location = source.location + source.delta_location
            source.rotation_euler.x = source.rotation_euler.x + source.delta_rotation_euler.x
            source.rotation_euler.y = source.rotation_euler.y + source.delta_rotation_euler.y
            source.rotation_euler.z = source.rotation_euler.z + source.delta_rotation_euler.z
            source.delta_rotation_euler = (0.0, 0.0, 0.0) 
            source.delta_location = (0.0, 0.0, 0.0) 
 



        # --- исходное позиционирование курсора
        if self.cursor_reset:
            cursor.location = cursor_pos
            cursor.rotation_euler = cursor_rot


        # --- переключение в режим редактирования
        if edit == True:
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}








class PT_OT_set(Operator):
    bl_idname = 'pt.set'
    bl_label = 'Pivot Set'
    bl_description = 'Apply Transformation'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    cursor: BoolProperty( name = '3D Cursor', description = 'Only Affects The 3D Cursor', default = False  )
    rotation: BoolProperty(name="Rotation", default=True)

    @classmethod
    def poll(cls, context):
        return context.active_object
        
    
    def execute(self, context):
        global cursor_pos
        global cursor_rot


        cursor = context.scene.cursor
        source = context.active_object
       


        """ source.location = source.location + source.delta_location
        source.delta_location = (0.0, 0.0, 0.0) """

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            edit = True
        else:
            edit = False


        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')


        if self.rotation:
            rotate_mat = cursor.rotation_euler.to_matrix()
            double_mat = rotate_mat @ rotate_mat
            invert_mat = double_mat.inverted()


            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            source.delta_rotation_euler = cursor.rotation_euler
            source.rotation_euler = invert_mat.to_euler() 
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)


            source.location = source.location + source.delta_location
            source.rotation_euler.x = source.rotation_euler.x + source.delta_rotation_euler.x
            source.rotation_euler.y = source.rotation_euler.y + source.delta_rotation_euler.y
            source.rotation_euler.z = source.rotation_euler.z + source.delta_rotation_euler.z
            source.delta_rotation_euler = (0.0, 0.0, 0.0) 
            source.delta_location = (0.0, 0.0, 0.0) 
 



        # --- исходное позиционирование курсора
        if self.cursor_reset:
            cursor.location = cursor_pos
            cursor.rotation_euler = cursor_rot


        # --- переключение в режим редактирования
        if edit == True:
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}










classes = [
    PIVOT_OT_start,
    PIVOT_OT_apply,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)