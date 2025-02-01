import bpy
from bpy.types import Operator
from ..utils.utils import activate, set_pivot_location, set_pivot_rotation



class PT_OT_to_select(Operator):
    bl_idname = 'pt.to_select'
    bl_label = 'Pivot To Select'
    bl_description = ("Pivot To Select \n"
                     "And Normal Alignment \n"
                     "(Ctrl+LMB - Set 3D Cursor)"
    )
    bl_options = { 'REGISTER', 'UNDO', 'BLOCKING' }

    cursor = False


    @classmethod
    def poll(self, context):
        return context.active_object
    

    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences

        if self.cursor:
            set_pivot_location( self, context, cursor = True )
        else:
            set_pivot_location( self, context, undoPush = True, message = 'Pivot To Select' )

        if props.align_to:
            if self.cursor:
                set_pivot_rotation( self, context, cursor = True )
            else:
                set_pivot_rotation( self, context, undoPush = True, message = 'Pivot To Select' )
        
        return {'FINISHED'}
    

    def invoke(self, context, event):
        if activate():
            self.cursor = event.ctrl
            return self.execute(context)
        else:
            self.report({'WARNING'}, 'None Selected!')
            return {'CANCELLED'}



classes = [ 
    PT_OT_to_select,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)