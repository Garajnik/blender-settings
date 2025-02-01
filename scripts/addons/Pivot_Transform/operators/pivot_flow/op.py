import bpy, bmesh
from bpy.types import Operator
from bpy.props import FloatVectorProperty, EnumProperty
from mathutils import Matrix, Vector, Quaternion
from . import flow as flow
from math import radians, sqrt
import numpy


RUN = False
MODE_STATE = False
PT_STATE = False
S_WIRE = False
S_WIRE_TRESH = False
S_WIRE_ALPHA = False
STANDARD_GIZMOS = (False, False, False)
GIZMO_PRO = False
S_MATRIX = Matrix()


# --- RESET
class PT_OT_reset_position(Operator):
    bl_idname = 'pt.reset_position'
    bl_label = 'Reset Position'
    bl_description = 'Reset Pivot Position'
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context):
        if context.scene.pivot_set.flow:
            if context.mode == 'OBJECT':
                return context.object and context.area.type == 'VIEW_3D'


    def execute(self, context):
        global S_MATRIX
        cursor_pos = context.scene.cursor.location.copy()
        context.scene.cursor.location = S_MATRIX.translation
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        context.scene.cursor.location = cursor_pos
        return{'FINISHED'}



class PT_OT_reset_rotation(Operator):
    bl_idname = 'pt.reset_rotation'
    bl_label = 'Reset Rotation'
    bl_description = 'Reset Pivot Rotation'
    bl_options = {'REGISTER', 'UNDO'}


    @classmethod
    def poll(self, context):
        if context.scene.pivot_set.flow:
            if context.mode == 'OBJECT':
                return context.object and context.area.type == 'VIEW_3D'


    def execute(self, context):
        global S_MATRIX
        q = S_MATRIX.decompose()[1]


      
        cursor_rot = context.scene.cursor.rotation_euler.copy()


        
        context.scene.cursor.rotation_euler = q.to_euler()

        #bpy.ops.pivot.apply()
        
        bpy.ops.transform.transform(
            mode = 'ALIGN',
            orient_type = 'CURSOR',
            orient_matrix_type = 'CURSOR'
        )

        context.scene.cursor.rotation_euler = cursor_rot
        return{'FINISHED'}



# --- RUN
def start_flow(context):
    global MODE_STATE, PT_STATE, S_WIRE, S_WIRE_TRESH, S_WIRE_ALPHA, RUN, STANDARD_GIZMOS, GIZMO_PRO, S_MATRIX

    MODE_STATE = context.object.mode

    if context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set( mode = 'OBJECT' )
        
    # --- Pivot Transform On
    PT_STATE = context.scene.tool_settings.use_transform_data_origin
    context.scene.tool_settings.use_transform_data_origin = True

    # --- Wireferame
    overlay = context.space_data.overlay
    S_WIRE = overlay.show_wireframes
    overlay.show_wireframes = True

    S_WIRE_TRESH = overlay.wireframe_threshold
    overlay.wireframe_threshold = 1.0

    S_WIRE_ALPHA = overlay.wireframe_opacity
    overlay.wireframe_opacity = 0.6
    
    # --- Gizmos
    gzm = bpy.context.space_data
    STANDARD_GIZMOS = (gzm.show_gizmo_object_translate, gzm.show_gizmo_object_rotate, gzm.show_gizmo_object_scale)
    bpy.context.space_data.show_gizmo_object_translate = False
    bpy.context.space_data.show_gizmo_object_rotate = False
    bpy.context.space_data.show_gizmo_object_scale = False

    if 'GIZMO_PRO' in context.preferences.addons.keys():
        GIZMO_PRO = bpy.context.scene.GP_scene_set.show_gizmo
        bpy.context.scene.GP_scene_set.show_gizmo = False

    S_MATRIX = context.object.matrix_world.copy()

    context.scene.pivot_set.flow = True
    RUN = True

def exit_flow(context):
    global MODE_STATE, PT_STATE, S_WIRE, S_WIRE_TRESH, S_WIRE_ALPHA, RUN, STANDARD_GIZMOS, GIZMO_PRO
    
    # --- Pivot Transform Off
    context.scene.tool_settings.use_transform_data_origin = PT_STATE

    # --- WIREFRAME
    overlay = context.space_data.overlay
    overlay.show_wireframes = S_WIRE
    overlay.wireframe_threshold = S_WIRE_TRESH
    overlay.wireframe_opacity = S_WIRE_ALPHA

    # --- Restore Mode
    bpy.ops.object.mode_set(mode=MODE_STATE)

    # --- Gizmos
    bpy.context.space_data.show_gizmo_object_translate = STANDARD_GIZMOS[0]
    bpy.context.space_data.show_gizmo_object_rotate = STANDARD_GIZMOS[1]
    bpy.context.space_data.show_gizmo_object_scale = STANDARD_GIZMOS[2]
    if 'GIZMO_PRO' in context.preferences.addons.keys():
        bpy.context.scene.GP_scene_set.show_gizmo = GIZMO_PRO

    context.scene.pivot_set.flow = False
    RUN = False

def set_position(location):
    cursor = bpy.context.scene.cursor
    loc_cursor = cursor.location.copy()
    cursor.location = location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    cursor.location = loc_cursor

def set_orientation(self, element, type):
    # Сохраняем имя изначально активного объекта
    initial_active_obj = bpy.context.active_object
    initial_sel_objs = bpy.context.selected_objects
    initial_orient = bpy.context.scene.transform_orientation_slots[0].type

    # Снимаем выделение со всех объектов
    bpy.ops.object.select_all(action='DESELECT')

    


    # Выделяем объект, к которому относится элемент и делаем его активным
    obj = flow.OBJ
    """obj.select_set(True)
    bpy.context.view_layer.objects.active = obj """


    # Выделяем элемент
    index = element[0].index 
    #bm = bmesh.from_edit_mesh(obj.data)

    mesh = bpy.data.meshes.new(name='Pivot Flow Mesh')

    obj.update_from_editmode()
    depgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depgraph)

    bm = bmesh.new()
    bm.from_mesh(obj_eval.to_mesh())
    bm.normal_update()
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    
    flow_object = bpy.data.objects.new(name='Pivot Flow Object', object_data=mesh)
    flow_object.matrix_world = obj.matrix_world
    bpy.context.scene.collection.objects.link(flow_object)
    bpy.context.view_layer.objects.active = flow_object
    flow_object.select_set(True)
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bm = bmesh.from_edit_mesh(flow_object.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    if type == 'VERT':
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bm.verts[index].select_set(True)
    elif type == 'EDGE':
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)
        bm.edges[index].select_set(True)
    elif type == 'FACE':
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bm.faces[index].select_set(True)
        
    # Создаем новую ориентацию
    bpy.ops.transform.create_orientation(name='Pivot Flow', use_view=False, use=True, overwrite=True)

    # Возвращаемся в объектный режим
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.data.objects.remove(flow_object)

    bpy.ops.object.select_all(action='DESELECT')
    # Снимаем выделение с текущего объекта и возвращаемся к изначально активному объекту
    #obj.select_set(False)
    for ob in initial_sel_objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = initial_active_obj

    # Применяем оператор transform с заданными параметрами
    bpy.ops.transform.transform(
        mode='ALIGN',
        orient_type='Pivot Flow',
        orient_matrix_type='Pivot Flow'
    )
        
    # Удаляем ориентацию "Pivot Flow"
    bpy.ops.transform.delete_orientation()
    bpy.context.scene.transform_orientation_slots[0].type = initial_orient

def set_align(origin, location):
    cursor = bpy.context.scene.cursor
    mat_cursor = cursor.matrix
    #q = normal_qat_from_two_point(loc, self.ray.location, var.PCO_NORMAL_STORE, self.ray.normal)
    n = Vector(location) - origin
    q = n.to_track_quat('X', 'Z')
    s = Vector((1, 1, 1))
    mat = Matrix.LocRotScale(origin, q, s)
    cursor.matrix = mat

    bpy.ops.transform.transform(
            mode='ALIGN',
            orient_type='CURSOR',
            orient_matrix_type='CURSOR'
        )
    cursor.matrix = mat_cursor



class PT_OT_set_pivot_flow(Operator):
    bl_idname = 'pt.set_pivot_flow'
    bl_label = 'Pivot Flow'
    bl_description = ' '
    bl_options = {'UNDO'}

    type: EnumProperty(
        name='Type',
        items=[
            ('VERT', 'Vertex', '', '', 0),
            ('EDGE', 'Edge', '', '', 1),
            ('FACE', 'Face', '', '', 2),
            ],
        default='VERT',
        )

    action: EnumProperty(
        name='Action',
        items=[
            ('ALL', 'All Transform', '', '', 0),
            ('POSITION', 'Position', '', '', 1),
            ('ORIENTATION', 'Orientation', '', '', 2),
            ('ALIGN', 'Align', '', '', 3),
            ],
        default='ALL',
        )


    location: FloatVectorProperty()


    @classmethod
    def poll(self, context):
        if context.mode == 'OBJECT':
            return context.object and context.area.type == 'VIEW_3D'


    def execute(self, context):
        if self.action == 'POSITION' or self.action == 'ALL':
            set_position(self.location)

        if self.action == 'ORIENTATION' or self.action == 'ALL':
            set_orientation(self, flow.ELEM, self.type)

        if self.action == 'ALIGN':
            origin = bpy.context.active_object.location
            set_align(origin, self.location)
        #print('type:', self.type, '|', 'type:', self.action)
        return {'FINISHED'}


    def invoke(self, context, event):
        if event.ctrl and event.shift:
            self.action = 'ALIGN'
        elif event.shift:
            self.action = 'POSITION'
        elif event.ctrl:
            self.action = 'ORIENTATION'
        else:
            self.action = 'ALL'
        return self.execute(context)



class PT_OT_flow(Operator):
    bl_idname = 'pt.flow'
    bl_label = 'Pivot Flow'
    bl_description =    ('Pivot Flow\n'
                        '• LMB - Position and Orientation\n'
                        '• LMB+Shift - Position\n'
                        '• LMB+Ctrl - Orientation\n'
                        '• LMB+Shift+Ctrl - Align +X')

    @classmethod
    def poll(self, context):
        return context.object and context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        global RUN

        if RUN:
            exit_flow(context)
        else:
            start_flow(context)

        return {'FINISHED'}



classes = [
    PT_OT_reset_position,
    PT_OT_reset_rotation,
    PT_OT_set_pivot_flow,
    PT_OT_flow,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)