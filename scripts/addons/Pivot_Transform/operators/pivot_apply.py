import bpy
from bpy.types import Operator, Macro
from ..utils.utils import flip_normals, activate
from mathutils import Euler
from bpy.props import BoolProperty



contextMode = {'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_ARMATURE', 'EDIT_METABALL', 'EDIT_LATTICE', 'POSE', 'SCULPT', 'PAINT_WEIGHT', 'PAINT_VERTEX', 'PAINT_TEXTURE', 'PARTICLE', 'PAINT_GPENCIL', 'EDIT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}
CONTEXT = 'OBJECT'




class PT_OT_check_normals(Operator):
    bl_idname = 'pt.check_normals'
    bl_label = 'Flip Normals'
    bl_description = 'Flip Normals'
    #bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.flip_normals:
            if activate():
                flip_normals(operator=False)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, 'None Selected!')
                return {'CANCELLED'}
        else:
            return {'CANCELLED'}


class PT_OT_mode_get(Operator):
    bl_idname = 'pt.mode_get'
    bl_label = 'Get Context'
    bl_description = 'Check Context'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object

    def execute(self, context):
        global CONTEXT
        CONTEXT = context.object.mode
        return {'FINISHED'}  


class PT_OT_mode_set(Operator):
    bl_idname = 'pt.mode_set'
    bl_label = 'Set Context'
    bl_description = 'Check Context'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object

    def execute(self, context):
        global CONTEXT
        bpy.ops.object.mode_set(mode=CONTEXT, toggle=False)
        return {'FINISHED'}  


class PT_OT_transform_apply(Operator):
    bl_idname = 'pt.transform_apply'
    bl_label = 'Transform Apply'
    bl_description = 'Transform Apply'
    bl_options = {'REGISTER', 'UNDO'}

    location: BoolProperty(default=False)
    rotation: BoolProperty(default=False)
    scale: BoolProperty(default=False)

    @classmethod
    def poll(self, context):
        return context.object

    def execute(self, context):
        bpy.ops.object.transform_apply(location=self.location, rotation=self.rotation, scale=self.scale)
        return {'FINISHED'}  



class APPLY_OT_location(Operator):
    bl_idname = "apply.location"
    bl_label = "Apply Location"
    bl_description = "Apply Location"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        global contextMode
        if context.mode in contextMode:
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
            bpy.ops.object.editmode_toggle()
        else:
            bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        return {'FINISHED'}  



class APPLY_OT_rotation(Operator):
    bl_idname = "apply.rotation"
    bl_label = "Apply Rotation"
    bl_description = "Apply Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        global contextMode
        if context.mode in contextMode:
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
            bpy.ops.object.editmode_toggle()
        else:
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return {'FINISHED'}  
        


class APPLY_OT_scale(Operator):
    bl_idname = "apply.scale"
    bl_label = "Apply Scale"
    bl_description = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        # FLIP NORMALS
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.flip_normals:
            flip_normals(operator=False)

        # APPLY
        global contextMode
        if context.mode in contextMode:
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bpy.ops.object.editmode_toggle()
        else:
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        return {'FINISHED'} 
   


""" class APPLY_OT_rotation_scale(Operator):
    bl_idname = 'apply.rotation_scale'
    bl_label = 'Apply Rotation & Scale'
    bl_description = 'Apply Rotation & Scale'
    bl_options = {'REGISTER', 'UNDO', 'UNDO_GROUPED'}
    bl_undo_group = 'Apply Rotation & Scale'
    @classmethod
    def poll(self, context):
        if context.object.select_get():
            return context.active_object

    def execute(self, context):
        # FLIP NORMALS
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.flip_normals:
            flip_normals(operator=False)

        # APPLY
        global contextMode
        store_context = context.mode
        if store_context in contextMode:
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            bpy.ops.object.editmode_toggle()
        else:
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        
        return {'FINISHED'} """

class APPLY_OT_rotation_scale(Macro):
    bl_idname = 'apply.rotation_scale'
    bl_label = 'Apply Rotation & Scale'
    bl_description = 'Apply Rotation & Scale'
    bl_options = {'UNDO', 'MACRO'}
    
    @classmethod
    def poll(self, context):
        #if context.object.select_get():
        return context.active_object







class APPLY_OT_all(Operator):
    bl_idname = "apply.all"
    bl_label = "Apply All Transformation"
    bl_description = (
                    "Location, Rotation, Scale\n"
                    "And Delta Transformation"
                    )
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context):
        if context.object.select_get():
            return context.active_object != None


    def execute(self, context):
        # FLIP NORMALS
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.flip_normals:
            flip_normals(operator=False)


        # APPLY DELTA
        for obj in context.selected_objects:
            obj.location = obj.location + obj.delta_location
            obj.rotation_euler.x = obj.rotation_euler.x + obj.delta_rotation_euler.x
            obj.rotation_euler.y = obj.rotation_euler.y + obj.delta_rotation_euler.y
            obj.rotation_euler.z = obj.rotation_euler.z + obj.delta_rotation_euler.z
            obj.delta_rotation_euler = Euler()
            obj.delta_location = (0.0, 0.0, 0.0)
         
        
        global contextMode
        if context.mode in contextMode:
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.object.editmode_toggle()
        else:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        return {'FINISHED'} 





# bpy.ops.object.mode_set(mode='EDIT', toggle=False)


classes = [
    PT_OT_check_normals,
    PT_OT_mode_get,
    PT_OT_mode_set,
    PT_OT_transform_apply,

    APPLY_OT_location,
    APPLY_OT_rotation,
    APPLY_OT_scale,
    APPLY_OT_rotation_scale,
    APPLY_OT_all,
    ]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    global storedMode



    # --- Apply Rotation & Scale
    APPLY_OT_rotation_scale.define('PT_OT_mode_get')

    APPLY_OT_rotation_scale.define('PT_OT_check_normals')
    
    op = APPLY_OT_rotation_scale.define('OBJECT_OT_mode_set')
    op.properties.mode = 'OBJECT'
    
    op = APPLY_OT_rotation_scale.define('PT_OT_transform_apply')
    op.properties.location = False
    op.properties.rotation = True
    op.properties.scale = True

    op = APPLY_OT_rotation_scale.define('PT_OT_mode_set')



def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)