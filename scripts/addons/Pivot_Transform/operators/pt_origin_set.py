import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty



def cursor_set(self, context):
    # --- TODO
    # https://github.com/blender/blender/blob/594f47ecd2d5367ca936cf6fc6ec8168c2b360d0/source/blender/editors/object/object_transform.c#L1567
    # object_origin_set_exec 1046
    # blender/source/blender/editors/object/object_transform.c
    pass



class PT_OT_origin_set(Operator):
    bl_idname = 'pt.origin_set'
    bl_label = 'Set Pivot' # /Cursor
    bl_description = '' # (Ctrl+LMB - Set 3D Cursor)
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    type: EnumProperty(
        name = 'Type', 
        items = [
            ('ORIGIN_CENTER_OF_VOLUME', 'Origin to Center of Mass (Volume)', 'Calculate the center of mass from the volume (must be manifold geometry with consistent normals)', '', 0),
            ('ORIGIN_CENTER_OF_MASS', 'Origin to Center of Mass (Surface)', 'Calculate the center of mass from the surface area', '', 1),
            ('ORIGIN_CURSOR', 'Origin to 3D Cursor', 'Move object origin to position of the 3D cursor', '', 2),
            ('ORIGIN_GEOMETRY', 'Origin to Geometry', 'Calculate the center of geometry based on the current pivot point (median, otherwise bounding-box)', '', 3),
            ('GEOMETRY_ORIGIN', 'Geometry to Origin', 'Move object geometry to object origin', '', 4),
            ],
        default = 'ORIGIN_CENTER_OF_MASS',
        )

    center: EnumProperty(
        name = 'Center', 
        items = [
            ('MEDIAN', 'Median Center', '', '', 0),
            ('BOUNDS', 'Bounds Center', '', '', 1),
            ],
        default = 'MEDIAN',
        )


    @classmethod
    def poll(cls, context):
        return context.active_object


    @classmethod
    def description(self, context, properties):
        if properties.type == 'ORIGIN_CENTER_OF_VOLUME':
            return 'Calculate the center of mass from the volume (must be manifold geometry with consistent normals)'
        elif properties.type == 'ORIGIN_CENTER_OF_MASS':
            return 'Calculate the center of mass from the surface area'
        elif properties.type == 'ORIGIN_CURSOR':
            return 'Move object origin to position of the 3D cursor'
        elif properties.type == 'ORIGIN_GEOMETRY':
            return 'Calculate the center of geometry based on the current pivot point (median, otherwise bounding-box)'
        elif properties.type == 'GEOMETRY_ORIGIN':
            return 'Move object geometry to object origin'
        


    def execute(self, context):
        bpy.ops.object.origin_set(type=self.type, center=self.center)
        return {'FINISHED'}




classes = [
    PT_OT_origin_set,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)