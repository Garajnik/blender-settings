import bpy
from bpy.types import GizmoGroup, Operator
from mathutils import Matrix, Vector, Quaternion
from math import pi, radians, copysign
from mathutils import Vector, Matrix, Quaternion
from bpy.props import EnumProperty, FloatVectorProperty
from bpy_extras.view3d_utils import (
    region_2d_to_vector_3d, 
    location_3d_to_region_2d
)



class PT_GGT_gizmo_cursor(GizmoGroup):
    bl_idname = 'PT_GGT_gizmo_cursor'
    bl_label = 'Gizmo for 3D Cursor'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SHOW_MODAL_ALL'}


    @classmethod
    def poll(cls, context):
        if context.space_data.show_gizmo:
            return context.scene.pivot_set.cursor_gizmo


    @classmethod
    def setup_keymap(cls, keyconfig):
        if not keyconfig.keymaps.find( name='Gizmo PRO Tweak', space_type='VIEW_3D' ):
            km = keyconfig.keymaps.new( name = 'Gizmo PRO Tweak', space_type = 'VIEW_3D' )
            kmi = km.keymap_items.new( 'gizmogroup.gizmo_tweak', type = 'LEFTMOUSE',  value = 'CLICK_DRAG', any = True )
            kmi.alt,  kmi.oskey = False, False

        else:
            km = keyconfig.keymaps.find( name = 'Gizmo PRO Tweak', space_type = 'VIEW_3D' ) #km.restore_to_default()
            if len(km.keymap_items) < 1:
                kmi = km.keymap_items.new( 'gizmogroup.gizmo_tweak', type = 'LEFTMOUSE',  value = 'CLICK_DRAG', any = True )
                kmi.alt,  kmi.oskey = False, False
            
        return km

    def setup(self, context):
        
        color_x = (1.0, 0.13, 0.24)
        color_y = (0.545, 0.8, 0.0)
        color_z = (0.0, 0.4, 1.0)
        color_highlight = (0.0, 0.0, 0.0)
        alpha = 0.5
        alpha_highlight = 0.9
        
        # --- ARROW
        self.arrow_x = self.gizmos.new('GIZMO_GT_arrow_3d')
        self.arrow_x.use_tooltip = False
        self.arrow_x.use_draw_offset_scale = True
        self.arrow_x.use_draw_modal = True
        self.arrow_x.color = color_x
        self.arrow_x.color_highlight = color_highlight
        self.arrow_x.alpha = alpha
        self.arrow_x.alpha_highlight = alpha_highlight
        self.ar_x = self.arrow_x.target_set_operator('transform.translate')
        self.ar_x.constraint_axis = (True, False, False)
        self.ar_x.release_confirm = True
        self.ar_x.cursor_transform = True

        self.arrow_y = self.gizmos.new('GIZMO_GT_arrow_3d')
        self.arrow_y.use_tooltip = False
        self.arrow_y.use_draw_offset_scale = True
        self.arrow_y.use_draw_modal = True
        self.arrow_y.color = color_y
        self.arrow_y.color_highlight = color_highlight
        self.arrow_y.alpha = alpha
        self.arrow_y.alpha_highlight = alpha_highlight
        self.ar_y = self.arrow_y.target_set_operator('transform.translate')
        self.ar_y.constraint_axis = (False, True, False)
        self.ar_y.release_confirm = True
        self.ar_y.cursor_transform = True

        self.arrow_z = self.gizmos.new('GIZMO_GT_arrow_3d')
        self.arrow_z.use_tooltip = False
        self.arrow_z.use_draw_offset_scale = True
        self.arrow_z.use_draw_modal = True
        self.arrow_z.color = color_z
        self.arrow_z.color_highlight = color_highlight
        self.arrow_z.alpha = alpha
        self.arrow_z.alpha_highlight = alpha_highlight
        self.ar_z = self.arrow_z.target_set_operator('transform.translate')
        self.ar_z.constraint_axis = (False, False, True)
        self.ar_z.release_confirm = True
        self.ar_z.cursor_transform = True
        
        # --- DIAL
        self.dial_x = self.gizmos.new('GIZMO_GT_dial_3d')
        self.dial_x.draw_options = {'CLIP'} # 'FILL_SELECT', 'ANGLE_VALUE'
        self.dial_x.color = color_x
        self.dial_x.color_highlight = color_highlight
        self.dial_x.alpha = alpha
        self.dial_x.alpha_highlight = alpha_highlight
        self.dial_x.use_tooltip = False
        self.dial_x.use_draw_value = True
        self.op_dx = self.dial_x.target_set_operator('pt.rotate_cursor')
        self.op_dx.axis = 'X'

        self.dial_y = self.gizmos.new('GIZMO_GT_dial_3d')
        self.dial_y.draw_options = {'CLIP'}
        self.dial_y.color = color_y
        self.dial_y.color_highlight = color_highlight
        self.dial_y.alpha = alpha
        self.dial_y.alpha_highlight = alpha_highlight
        self.dial_y.use_tooltip = False
        self.dial_y.use_draw_value = True
        self.op_dy = self.dial_y.target_set_operator('pt.rotate_cursor')
        self.op_dy.axis = 'Y'

        self.dial_z = self.gizmos.new('GIZMO_GT_dial_3d')
        self.dial_z.draw_options = {'CLIP'}
        self.dial_z.color = color_z
        self.dial_z.color_highlight = color_highlight
        self.dial_z.alpha = alpha
        self.dial_z.alpha_highlight = alpha_highlight
        self.dial_z.use_tooltip = False
        self.dial_z.use_draw_value = True
        self.op_dz = self.dial_z.target_set_operator('pt.rotate_cursor')
        self.op_dz.axis = 'Z'


        # --- DOT
        self.dot = self.gizmos.new('GIZMO_GT_move_3d')
        self.dot.use_tooltip = False
        self.dot.color = (1.0, 0.13, 0.24)
        self.dot.color_highlight = color_highlight
        self.dot.alpha = alpha
        self.dot.alpha_highlight = alpha_highlight
        self.dot.draw_options = {'FILL_SELECT', 'ALIGN_VIEW'}
        self.ar_dot = self.dot.target_set_operator('transform.translate')
        self.ar_dot.release_confirm = True
        self.ar_dot.cursor_transform = True
        


    def invoke_prepare(self, context, gizmo):
        self.op_dx.matrix = gizmo.matrix_basis
        self.op_dy.matrix = gizmo.matrix_basis
        self.op_dz.matrix = gizmo.matrix_basis


    def draw_prepare(self, context):
        #props = context.preferences.addons['GIZMO_PRO'].preferences
        #settings = context.scene.GP_scene_set
        cursor = context.scene.cursor

        orient = 'GLOBAL' if context.window.scene.transform_orientation_slots[0].type == 'GLOBAL' else 'CURSOR'
        self.ar_x.orient_type = orient
        self.ar_x.orient_matrix_type = orient
        self.ar_y.orient_type = orient
        self.ar_y.orient_matrix_type = orient
        self.ar_z.orient_type = orient
        self.ar_z.orient_matrix_type = orient

        sizeGizmo = 1
        sizeCursor = 1
        lwDot = 3

        coef = 0.2 if sizeCursor > 0.6 else 0.5
        # --- DOT
        self.dot.scale_basis = sizeCursor * coef
        self.dot.line_width = sizeGizmo * lwDot
        self.dot.matrix_basis = cursor.matrix.normalized()
      
        l, r, s  = cursor.matrix.decompose()
        orient_slots = context.window.scene.transform_orientation_slots[0].type
        if orient_slots == 'GLOBAL':
            xR = Quaternion( (0.0, 1.0, 0.0), radians(90) )
            yR = Quaternion( (1.0, 0.0, 0.0), radians(-90) )
            zR = Quaternion( (0.0, 0.0, 1.0), radians(0) )
            x_matrix_move = Matrix.LocRotScale(l, xR, s).normalized() 
            y_matrix_move = Matrix.LocRotScale(l, yR, s).normalized() 
            z_matrix_move = Matrix.LocRotScale(l, zR, s).normalized()

        else:
            xR = r @ Quaternion( (0.0, 1.0, 0.0), radians(90) )
            yR = r @ Quaternion( (1.0, 0.0, 0.0), radians(-90) )
            zR = r
            x_matrix_move = Matrix.LocRotScale(l, xR, s).normalized()
            y_matrix_move = Matrix.LocRotScale(l, yR, s).normalized() 
            z_matrix_move = Matrix.LocRotScale(l, zR, s).normalized()
        

        x_matrix_rot = Matrix.LocRotScale(l, (r @ Quaternion( (0.0, 1.0, 0.0), radians(90) )), s).normalized() 
        y_matrix_rot = Matrix.LocRotScale(l, (r @ Quaternion( (1.0, 0.0, 0.0), radians(-90) )), s).normalized() 
        z_matrix_rot = Matrix.LocRotScale(l, r, s).normalized()
        mo_a = Matrix.Translation(Vector( (0.0, 0.0, 0.7)))
            
    




        
        # --- ARROW
        self.arrow_x.length = 0.3
        self.arrow_x.line_width = sizeCursor * 3
        self.arrow_x.scale_basis = sizeCursor
        self.arrow_x.matrix_basis = x_matrix_move
        self.arrow_x.matrix_offset = mo_a

        self.arrow_y.length = 0.3
        self.arrow_y.line_width = sizeCursor * 3
        self.arrow_y.scale_basis = sizeCursor
        self.arrow_y.matrix_basis = y_matrix_move
        self.arrow_y.matrix_offset = mo_a

        self.arrow_z.length = 0.3
        self.arrow_z.line_width = sizeCursor * 3
        self.arrow_z.scale_basis = sizeCursor
        self.arrow_z.matrix_basis = z_matrix_move
        self.arrow_z.matrix_offset = mo_a
        
        # --- DIAL
        self.dial_x.scale_basis = sizeCursor * 0.7
        self.dial_x.line_width = sizeCursor * 3
        self.dial_x.matrix_basis = x_matrix_rot

        self.dial_y.scale_basis = sizeCursor * 0.7
        self.dial_y.line_width = sizeCursor * 3
        self.dial_y.matrix_basis = y_matrix_rot

        self.dial_z.scale_basis = sizeCursor * 0.7
        self.dial_z.line_width = sizeCursor * 3
        self.dial_z.matrix_basis = z_matrix_rot



""" class PT_OT_rotate_cursor(Operator):
    bl_idname = 'pt.rotate_cursor'
    bl_label = 'Rotate 3D Cursor'

    axis: EnumProperty(
        name='Axis',
        items=[
            ('X', 'X', ''),
            ('Y', 'Y', ''),
            ('Z', 'Z', ''),
        ],
    )

    matrix: FloatVectorProperty(
        size = (4, 4),
        subtype = 'MATRIX',
        default = [
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ],
        )


    def __init__(self):
        self.init_matrix = Matrix()
        self.prev_mouse = Vector((0.0, 0.0))
        self.base_axis = []


    def sign(self, context, event):
        region = context.region
        rv3d = context.region_data
        cursor_3d = context.scene.cursor.location

        # Позиция 3D курсора в 2D
        cursor_2d = location_3d_to_region_2d(region, rv3d, cursor_3d)

        # Текущая и предыдущая позиции курсора мыши в 2D
        current_mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        previous_mouse_pos = self.prev_mouse

        # Векторы от 3D курсора до текущего и предыдущего положения мыши
        vector_current = current_mouse_pos - cursor_2d
        vector_previous = previous_mouse_pos - cursor_2d

        # Векторное произведение для определения знака (+1 или -1)
        cross = vector_previous.cross(vector_current)

        return -1 if cross < 0 else 1
    

    def dot(self):
        context = bpy.context
        region_data = context.region_data
        
        l, q, s = self.matrix.decompose()
        if region_data.is_perspective:
            vL = region_data.view_matrix.inverted().translation
            vv = vL - l
        else:
            vv = region_data.view_rotation @ Vector((0, 0, -1))
        norm = q @ Vector((0, 0, 1))
        dot = norm.angle(vv)
        nDeg = pi / 2
        if dot > nDeg:
            dot = -(pi - dot)
        return int(copysign(1, dot)) 


    def rotation(self, event, context):
        cursor = Vector((event.mouse_region_x, event.mouse_region_y))
        if cursor == self.prev_mouse:
            return Matrix()

        region = context.region
        rv3d = context.region_data

        # Новый вектор направления взгляда с позиции курсора
        new_vector = region_2d_to_vector_3d(region, rv3d, cursor).normalized()
        
        print(new_vector)
        # Векторное произведение для определения знака угла
        cross = self.prev_mouse_vector.cross(new_vector)
        
        if self.axis == 'X': axis_vector = Vector((1, 0, 0))
        elif self.axis == 'Y': axis_vector = Vector((0, 1, 0))
        elif self.axis == 'Z': axis_vector = Vector((0, 0, 1))
        else: return Matrix()

        # Скалярное произведение для определения знака угла
        sign = self.sign(context, event) #1.0 if cross.dot(axis_vector) > 0 else -1.0
        
        # Расчет угла между двумя векторами
        angle = (self.prev_mouse_vector.angle(new_vector) * (sign*self.dot())) * 10
        
        self.prev_mouse_vector = new_vector
        self.prev_mouse = cursor

        if event.shift:
            angle *= 0.1
        return Matrix.Rotation(angle, 4, axis_vector)


    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            rot_mat = self.rotation(event, context)
            cursor = context.scene.cursor
            cursor.matrix = cursor.matrix @ rot_mat
        elif event.type == 'LEFTMOUSE':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.scene.cursor.matrix = self.init_matrix
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        self.init_matrix = context.scene.cursor.matrix.copy()
        self.prev_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        region = context.region
        rv3d = context.region_data
        self.prev_mouse_vector = region_2d_to_vector_3d(region, rv3d, self.prev_mouse)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
 """


class PT_OT_rotate_cursor(Operator):
    bl_idname = 'pt.rotate_cursor'
    bl_label = 'Rotate 3D Cursor'

    axis: EnumProperty(
        name='Axis',
        items=[
            ('X', 'X', ''),
            ('Y', 'Y', ''),
            ('Z', 'Z', ''),
        ],
    )

    matrix: FloatVectorProperty(
        size=(4, 4),
        subtype='MATRIX',
        default=[
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ],
    )

    def __init__(self):
        self.init_matrix = Matrix()
        self.prev_mouse = Vector((0.0, 0.0))
        self.prev_mouse_vector = Vector((0.0, 0.0))

    def sign(self, context, event):
        region = context.region
        rv3d = context.region_data
        cursor_3d = context.scene.cursor.location

        # Позиция 3D курсора в 2D
        cursor_2d = location_3d_to_region_2d(region, rv3d, cursor_3d)

        # Текущая и предыдущая позиции курсора мыши в 2D
        current_mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        previous_mouse_pos = self.prev_mouse

        # Векторы от 3D курсора до текущего и предыдущего положения мыши
        vector_current = current_mouse_pos - cursor_2d
        vector_previous = previous_mouse_pos - cursor_2d

        # Векторное произведение для определения знака (+1 или -1)
        cross = vector_previous.cross(vector_current)

        return -1 if cross < 0 else 1
    
    def dot(self):
        context = bpy.context
        region_data = context.region_data
        
        l, q, s = self.matrix.decompose()
        if region_data.is_perspective:
            vL = region_data.view_matrix.inverted().translation
            vv = vL - l
        else:
            vv = region_data.view_rotation @ Vector((0, 0, -1))
        norm = q @ Vector((0, 0, 1))
        dot = norm.angle(vv)
        nDeg = pi / 2
        if dot > nDeg:
            dot = -(pi - dot)
        return int(copysign(1, dot)) 

    def calc_mouse_vector(self, context, event):
        region = context.region
        rv3d = context.region_data

        if rv3d.is_perspective:
            return region_2d_to_vector_3d(region, rv3d, Vector((event.mouse_region_x, event.mouse_region_y))).normalized()
        else:
            # Рассчитываем направление от центра до курсора в ортографической проекции
            mid_x, mid_y = region.width / 2, region.height / 2
            direction = Vector((event.mouse_region_x - mid_x, event.mouse_region_y - mid_y, 0))
            return direction.normalized()

    def rotation(self, event, context):
        cursor = Vector((event.mouse_region_x, event.mouse_region_y))
        if cursor == self.prev_mouse:
            return Matrix()

        new_vector = self.calc_mouse_vector(context, event)
        
        if self.prev_mouse_vector.length == 0:
            self.prev_mouse_vector = new_vector
            return Matrix()

        cross = self.prev_mouse_vector.cross(new_vector)
        
        if self.axis == 'X': axis_vector = Vector((1, 0, 0))
        elif self.axis == 'Y': axis_vector = Vector((0, 1, 0))
        elif self.axis == 'Z': axis_vector = Vector((0, 0, 1))
        else: return Matrix()

        sign = self.sign(context, event)

        angle = (self.prev_mouse_vector.angle(new_vector) * (sign * self.dot())) * 10
        
        self.prev_mouse_vector = new_vector
        self.prev_mouse = cursor

        if event.shift:
            angle *= 0.1
        return Matrix.Rotation(angle, 4, axis_vector)

    def invoke(self, context, event):
        self.init_matrix = context.scene.cursor.matrix.copy()
        self.prev_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        self.prev_mouse_vector = self.calc_mouse_vector(context, event)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            rot_mat = self.rotation(event, context)
            cursor = context.scene.cursor
            cursor.matrix = cursor.matrix @ rot_mat
        elif event.type == 'LEFTMOUSE':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            context.scene.cursor.matrix = self.init_matrix
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

classes = [
    PT_GGT_gizmo_cursor,
    PT_OT_rotate_cursor,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)   
    

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)