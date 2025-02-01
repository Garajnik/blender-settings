import bpy, gpu, bmesh
from bpy.types import Gizmo, GizmoGroup
from gpu import state
from mathutils import Matrix, Vector, Quaternion
from gpu import shader as sh
from gpu_extras.batch import batch_for_shader
from gpu.types import GPUShader
from . import op
from bpy_extras import view3d_utils
from mathutils.geometry import intersect_point_line
from math import radians
from mathutils.kdtree import KDTree


# --- Variables
ELEM = None
OBJ = None
DIST = 10
DIST_SQR = DIST**2



# --- Draw Helper
def GPU_SHADER_DIAG_STRIPES_UNIFORM_COLOR():
    vert = '''
        uniform mat4 ModelViewProjectionMatrix;

        #ifdef USE_WORLD_CLIP_PLANES
        uniform mat4 ModelMatrix;
        #endif

        in vec3 pos;

        void main()
        {
          gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);

        #ifdef USE_WORLD_CLIP_PLANES
          world_clip_planes_calc_clip_distance((ModelMatrix * vec4(pos, 1.0)).xyz);
        #endif
        }

    '''

    frag = '''
        #ifndef USE_GPU_SHADER_CREATE_INFO
        uniform vec4 color1;
        uniform vec4 color2;
        uniform int size1;
        uniform int size2;

        out vec4 fragColor;
        #endif

        void main()
        {
          float phase = mod((gl_FragCoord.x + gl_FragCoord.y), (size1 + size2));

          if (phase < size1) {
            fragColor = color1;
          }
          else {
            fragColor = color2;
          }
        }
  
    '''
    #shader.uniform_float("color1", (0.2, 0.2, 0.9, 1.0))
    #shader.uniform_float("color2", (1.0, 0.2, 0.2, 0.5))
    #shader.uniform_int("size1", 10)
    #shader.uniform_int("size2", 10)

    return GPUShader(vert, frag)

def GPU_SHADER_3D_POINT_UNIFORM_SIZE_OUTLINE():
    vert = '''
        
        #ifndef USE_GPU_SHADER_CREATE_INFO
        uniform mat4 ModelViewProjectionMatrix;
        uniform float size;
        uniform float outlineWidth;
        uniform vec4 color;
        in vec3 pos;
        out vec4 radii;
        #endif

        void main()
        {
          gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
          gl_PointSize = size;

          /* calculate concentric radii in pixels */
          float radius = 0.5 * size;

          /* start at the outside and progress toward the center */
          radii[0] = radius;
          radii[1] = radius - 1.0;
          radii[2] = radius - outlineWidth;
          radii[3] = radius - outlineWidth - 1.0;

          /* convert to PointCoord units */
          radii /= size;
          
          
          #ifdef USE_WORLD_CLIP_PLANES
            world_clip_planes_calc_clip_distance((ModelMatrix * vec4(pos, 1.0)).xyz);
        #endif
        }

    '''

    frag = ''' 
        
        #ifndef USE_GPU_SHADER_CREATE_INFO
        uniform vec4 color;
        uniform vec4 outlineColor;

        in vec4 radii;
        out vec4 fragColor;
        #endif

        void main()
        {
          float dist = length(gl_PointCoord - vec2(0.5));

          /* transparent outside of point
           * --- 0 ---
           * smooth transition
           * --- 1 ---
           * pure outline color
           * --- 2 ---
           * smooth transition
           * --- 3 ---
           * pure point color
           * ...
           * dist = 0 at center of point */

          float midStroke = 0.5 * (radii[1] + radii[2]);

          if (dist > midStroke) {
            fragColor.rgb = outlineColor.rgb;
            fragColor.a = mix(outlineColor.a, 0.0, smoothstep(radii[1], radii[0], dist));
          }
          else {
            fragColor = mix(color, outlineColor, smoothstep(radii[3], radii[2], dist));
          }

          if (fragColor.a == 0.0) {
            discard;
          }
        }
  
    '''
    #shader.uniform_float("color", (0.2, 0.2, 0.9, 1.0))
    #shader.uniform_float("outlineColor", (0.0, 0.0, 0.0, 0.5))
    #shader.uniform_float("size", 400.0)
    #shader.uniform_float("outlineWidth", 30.0)

    return GPUShader(vert, frag)

def drawVertex(coords, color, shader_type = 1):
    if shader_type == 1:
        shader = GPU_SHADER_3D_POINT_UNIFORM_SIZE_OUTLINE()
    elif shader_type == 2:
        shader = sh.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {'pos': coords})
    shader.bind()
    shader.uniform_float('color', color)
    if shader_type == 1:
        shader.uniform_float("outlineColor", (0.1, 0.1, 0.1, 1.0))
        shader.uniform_float("size", 20.0)
        shader.uniform_float("outlineWidth", 3.0)
    batch.draw(shader)
 
def drawEdge(coords, color):
    shader = sh.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {'pos': coords})
    shader.bind()
    shader.uniform_float('color', color)
    batch.draw(shader)
 
def drawPoly(coords, color):
    shader = GPU_SHADER_DIAG_STRIPES_UNIFORM_COLOR()
    batch = batch_for_shader(shader, 'TRI_FAN', {'pos': coords})
    shader.bind()
    shader.uniform_float('color1', color)
    shader.uniform_float('color2', (0.0, 0.0, 0.0, 0.6)) # (color[0], color[1], color[2], 0.2)
    shader.uniform_int('size1', 7)
    shader.uniform_int('size2', 10)
    batch.draw(shader)

def oldAxisDraw(context): # --- Draw Old Axis
    pos = Vector() #op.S_LOC # TODO
    rot = Quaternion() #op.S_ROT # TODO
    offset = 0.5

    x_vec =  pos + ( rot.to_matrix().to_4x4() @ Vector((offset, 0.0, 0.0)) )
    x_edges_co = [pos, x_vec]
    
    y_vec = pos + ( rot.to_matrix().to_4x4() @ Vector((0.0, offset, 0.0)) )
    y_edges_co = [pos, y_vec]

    z_vec = pos + ( rot.to_matrix().to_4x4() @ Vector((0.0, 0.0, offset)) )
    z_edges_co = [pos, z_vec]

    return x_edges_co, y_edges_co, z_edges_co


# --- Get Elements
def bmGenerate(self, obj):
    obj.update_from_editmode()
    depgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depgraph)
    bm = bmesh.new()
    bm.from_mesh(obj_eval.to_mesh())
    bm.normal_update()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    self.bm = bm
    self.store_obj = obj_eval.name

def kdtGenerate(self, obj):
    self.kdt = KDTree(len(obj.data.vertices))
    for i, v in enumerate(obj.data.vertices):
        self.kdt.insert(obj.matrix_world @ v.co, i)
    self.kdt.balance()

def kdtFind(self, mouse, kdt):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    #view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse)
    #origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse)
    self.hit = view3d_utils.region_2d_to_location_3d(region, rv3d, mouse, Vector((0,0,1))) 
    return kdt.find(self.hit)

def pointSquareDistance(co1, co2):
    return (Vector(co1) - Vector(co2)).length_squared

def raycast(self, context, mouse):
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    scene_data = context.evaluated_depsgraph_get()
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse) 
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse)

    if context.space_data.local_view:
        for obj in context.selected_objects:
            if obj.data.rna_type.name == 'Mesh':
                mwi = obj.matrix_world.inverted()
                ray_origin_mwi = mwi @ ray_origin
                view_vector_mwi = ((mwi @ view_vector) - mwi.translation).normalized()
                self.result, self.location, normal, index = obj.ray_cast(ray_origin_mwi, view_vector_mwi)
                if self.result:
                    break
            else:
                pass
    else:
        self.result, self.location, normal, index, obj, matrix = scene.ray_cast(scene_data, ray_origin, view_vector)

    if self.result:
        if obj.library:
            self.result = None
            return None, None
    
        if obj.data.rna_type.name == 'Mesh':
            return index, obj
        else:
            self.result = None
            return None, None
    else:
        return None, None

def getElements(self, context, mouse, index, obj):
    """ if self.kdt:
        kd = kdtFind(self, mouse, self.kdt)
        self.location_kd = kd[0]
        #print(kd) """

    if self.result and obj:
        region = context.region
        rv3d = context.region_data

        matrix_world = obj.matrix_world
        if obj.name != self.store_obj:
            bmGenerate(self, obj)
            #kdtGenerate(self, obj)

        if self.pivotMoved:
            bmGenerate(self, obj)
            self.pivotMoved = False
        
        

        poly = self.bm.faces[index]
        verts, edges = poly.verts, poly.edges 
    
        cVert = {}
        for vert in verts:
            if not vert.hide:
                point = matrix_world @ vert.co
                point_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
                if point_2d == None:
                    pass
                else:
                    cVert[vert] = pointSquareDistance(mouse, point_2d)
        
        cEdge = {}
        for edge in edges:
            if not edge.hide:
                points = [matrix_world @ v.co for v in edge.verts]
                points_2d = [view3d_utils.location_3d_to_region_2d(region, rv3d, point) for point in points]
                
                percent = intersect_point_line(self.location, points[0],points[1])[1]
                fakepoint = points[0].lerp(points[1], percent)
                fakepoint_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, fakepoint)

                count = len([p for p in points_2d if p == None])
                if count == 1:
                    for n,p in enumerate(points_2d):
                        if p == None:
                            points_2d[n] = fakepoint_2d
                
                if count == 2:
                    cEdge[edge] = DIST_SQR * 2

                if None not in points_2d:
                    point_2d = intersect_point_line(mouse, points_2d[0], points_2d[1])[0]
                    if point_2d:
                        cEdge[edge] = pointSquareDistance(mouse, point_2d)
                    else:
                        cEdge[edge] = DIST_SQR * 2

        minVert = min(cVert, key=cVert.get)
        minEdge = min(cEdge, key=cEdge.get)

        if cVert.get(minVert) > DIST_SQR and cEdge.get(minEdge) > DIST_SQR:
            element = poly
        else:
            if cVert.get(minVert) < DIST_SQR:
                element = minVert
            else:
                element = minEdge

        return element, obj

def identifyElement(element, obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    if isinstance(element, bmesh.types.BMFace):
        return "FACE", [mw @ vert.co for vert in element.verts]
    elif isinstance(element, bmesh.types.BMEdge):
        return "EDGE", [mw @ vert.co for vert in element.verts]
    elif isinstance(element, bmesh.types.BMVert):
        return "VERT", [mw @ element.co]
    bm.free()

# --- For Matrix
def get_local_orient():
    rot = bpy.context.object.matrix_world.decompose()[1]
    x = rot @ Quaternion( (0.0, 1.0, 0.0), radians(90) )
    y = rot @ Quaternion( (1.0, 0.0, 0.0), radians(-90) )
    z = rot @ Quaternion( (0.0, 0.0, 1.0), radians(-90) )
    return x, y, z

def get_orient_from_type(context):
    l = context.object.matrix_world.translation
    s = Vector((1.0, 1.0, 1.0))
    x, y, z = get_local_orient()
    mX = Matrix.LocRotScale(l, x, s).normalized()
    mY = Matrix.LocRotScale(l, y, s).normalized()
    mZ = Matrix.LocRotScale(l, z, s).normalized()
    return mX, mY, mZ

def get_orient_matrix(matrix, axis):
    mat = matrix.copy().to_3x3()
    if axis == 'X':
        mat = mat @ Quaternion( (0.0, 1.0, 0.0), radians(90) ).to_matrix().to_3x3()
    elif axis == 'Y':
        mat = mat @ Quaternion( (1.0, 0.0, 0.0), radians(90) ).to_matrix().to_3x3()
    return mat


# --- GIZMO
class PIVOT_GT_preselect(Gizmo):
    bl_idname = 'PIVOT_GT_preselect'
    
    __slots__ = (
        'result',
        'elem',
        'elem_type',
        'verts',
        'pivotMoved',
        'location',
        'bm',
        'store_obj',
        'kdt',

        'hit',
        'location_kd',
    )


    def setup(self):
        self.use_tooltip = False
        self.color = (0.0, 1.0, 0.24)
        self.use_select_background = True
        
        self.result = False
        self.elem = None
        self.elem_type = None
        self.verts = []
        self.pivotMoved = False
        self.location = Vector()
        self.store_obj = None
        self.kdt = None

        self.hit = Vector()
        self.location_kd = Vector()

    def test_select(self, context, location):
        idx, obj = raycast(self, context, location)
        self.elem = getElements(self, context, location, idx, obj)
        if self.result:
            global OBJ
            OBJ = obj
            self.elem_type, self.verts = identifyElement(self.elem[0], self.elem[1])
            return 0
        if context.area:
            context.area.tag_redraw()
        return -1

    def draw(self, context):
        state.blend_set('ALPHA')
        state.line_width_set(6.0)
        state.point_size_set(20.0)

        # --- elemets
        if self.result:
            if self.elem_type == 'VERT':
                drawVertex(self.verts, (*self.color, 1.0))
            if self.elem_type == 'EDGE':
                drawEdge(self.verts, (*self.color, 1.0))
            if self.elem_type == 'FACE':
                drawPoly(self.verts, (*self.color, 0.3))

        #drawVertex([self.location_kd, self.hit], (0.0, 0.0, 1.0, 1.0))

        # --- old axis
        #state.line_width_set(2.0)
        """ x_co, y_co, z_co = oldAxisDraw(context)
        drawEdge(x_co, (1.0, 0.1, 0.3, 0.3))
        drawEdge(y_co, (0.1, 1.0, 0.5, 0.3))
        drawEdge(z_co, (0.1, 0.3, 1.0, 0.3)) """

        state.point_size_set(1.0)
        state.line_width_set(1.0)
        state.blend_set('NONE')



class PIVOT_GGT_flow(GizmoGroup):
    bl_idname = 'PIVOT_GGT_flow'
    bl_label = 'Pivot Flow'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'VR_REDRAWS'} # , 'TOOL_INIT', 'SELECT', 'SCALE', 'DEPTH_3D', 'PERSISTENT',


    @classmethod
    def poll(cls, context):
        if context.object and context.mode == 'OBJECT':
            if context.scene.pivot_set.flow:
                return len(context.selected_objects) > 0 and (context.active_object is not None)
    

    @classmethod
    def setup_keymap(cls, keyconfig):
        km = keyconfig.keymaps.new(name='Pivot FLow Click', space_type='VIEW_3D')
        km.keymap_items.new('gizmogroup.gizmo_tweak', type='LEFTMOUSE', value='CLICK')
        km.keymap_items.new('gizmogroup.gizmo_tweak', type='LEFTMOUSE', value='CLICK', ctrl=True)
        km.keymap_items.new('gizmogroup.gizmo_tweak', type='LEFTMOUSE', value='CLICK', shift=True)
        km.keymap_items.new('gizmogroup.gizmo_tweak', type='LEFTMOUSE', value='CLICK', ctrl=True, shift=True)
        return km
    

    def setup(self, context):
        self.preselect = self.gizmos.new('PIVOT_GT_preselect')
        #self.preselect.use_event_handle_all = True
        self.op = self.preselect.target_set_operator('pt.set_pivot_flow')

        
    def invoke_prepare(self, context, gizmo):
        global ELEM
        ELEM = self.preselect.elem

        self.op.type = self.preselect.elem_type

        verts = self.preselect.verts
        mid_position = sum(verts, Vector()) / len(verts)
        self.op.location = mid_position

        self.preselect.pivotMoved = True


    def refresh(self, context):
        if self.preselect.pivotMoved is False:
            self.preselect.pivotMoved = True



class PIVOT_GGT_flow_xform(GizmoGroup):
    bl_idname = 'PIVOT_GGT_flow_xform'
    bl_label = 'Pivot Flow'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'} # , 'TOOL_INIT', 'SELECT', 'SCALE', 'DEPTH_3D', 'PERSISTENT', 
    bl_owner_id = 'PIVOT_GGT_flow'


    @classmethod
    def poll(cls, context):
        if context.object and context.mode == 'OBJECT':
            if context.scene.pivot_set.flow:
                return len(context.selected_objects) > 0 and (context.active_object is not None)
    
    @classmethod
    def setup_keymap(cls, keyconfig):
        km = keyconfig.keymaps.new(name='Pivot FLow Tweak', space_type='VIEW_3D')
        km.keymap_items.new('gizmogroup.gizmo_tweak', type='LEFTMOUSE', value='CLICK_DRAG')
        return km

    def setup(self, context):
        mo_a = Matrix.Translation(Vector((0.0, 0.0, 0.5)))
        sizeGizmo = 1.5
        lwDot = 3
        lengthArrow = 0.2
        alphaGizmo = 0.9
        highlight_alpha_gizmo = 0.9
        color_x = (1.0, 0.13, 0.24)
        color_y = (0.27, 1.0, 0.0)
        color_z = (0.0, 0.4, 1.0)
        selectColor = (0.2, 0.2, 0.2)
        elementsColor = (0.0, 1.0, 0.24) #(1.0, 0.13, 0.24)

        # --- Arrow
        self.arrow_x = self.gizmos.new('GIZMO_GT_arrow_3d')
        self.arrow_x.use_tooltip = False
        self.arrow_x.use_draw_offset_scale = True
        self.arrow_x.use_draw_modal = True
        self.arrow_x.alpha_highlight = highlight_alpha_gizmo
        self.arrow_x.alpha = alphaGizmo
        self.arrow_x.color = color_x
        self.arrow_x.color_highlight = selectColor
        self.arrow_x.line_width = sizeGizmo * 2
        self.arrow_x.scale_basis = sizeGizmo
        self.arrow_x.length = lengthArrow
        self.arrow_x.matrix_offset = mo_a
        self.op_arx = self.arrow_x.target_set_operator('transform.transform')
        self.op_arx.mode = 'TRANSLATION'
        self.op_arx.constraint_axis = (True, False, False)
        self.op_arx.release_confirm = True
        self.arrow_x.use_event_handle_all = True

        self.arrow_y = self.gizmos.new('GIZMO_GT_arrow_3d')
        self.arrow_y.use_tooltip = False
        self.arrow_y.use_draw_offset_scale = True
        self.arrow_y.use_draw_modal = True
        self.arrow_y.alpha_highlight = highlight_alpha_gizmo
        self.arrow_y.alpha = alphaGizmo
        self.arrow_y.color = color_y
        self.arrow_y.color_highlight = selectColor
        self.arrow_y.line_width = sizeGizmo * 2
        self.arrow_y.scale_basis = sizeGizmo
        self.arrow_y.length = lengthArrow
        self.arrow_y.matrix_offset = mo_a
        self.op_ary = self.arrow_y.target_set_operator('transform.transform')
        self.op_ary.mode = 'TRANSLATION'
        self.op_ary.constraint_axis = (False, True, False)
        self.op_ary.release_confirm = True
        

        self.arrow_z = self.gizmos.new('GIZMO_GT_arrow_3d')
        self.arrow_z.use_tooltip = False
        self.arrow_z.use_draw_offset_scale = True
        self.arrow_z.use_draw_modal = True
        self.arrow_z.alpha_highlight = highlight_alpha_gizmo
        self.arrow_z.alpha = alphaGizmo
        self.arrow_z.color = color_z
        self.arrow_z.color_highlight = selectColor
        self.arrow_z.line_width = sizeGizmo * 2
        self.arrow_z.scale_basis = sizeGizmo
        self.arrow_z.length = lengthArrow
        self.arrow_z.matrix_offset = mo_a
        self.op_arz = self.arrow_z.target_set_operator('transform.transform')
        self.op_arz.mode = 'TRANSLATION'
        self.op_arz.constraint_axis = (False, False, True)
        self.op_arz.release_confirm = True

        
        # --- Dial
        self.dial_x = self.gizmos.new('GIZMO_GT_dial_3d')
        self.dial_x.use_tooltip = False
        self.dial_x.use_draw_modal = True
        self.dial_x.draw_options = {'CLIP'}
        self.dial_x.alpha_highlight = highlight_alpha_gizmo
        self.dial_x.alpha = alphaGizmo
        self.dial_x.color = color_x
        self.dial_x.color_highlight = selectColor
        self.dial_x.line_width = sizeGizmo * 2
        self.dial_x.scale_basis = sizeGizmo / 2
        self.op_dx = self.dial_x.target_set_operator('transform.transform')
        self.op_dx.mode = 'ROTATION'
        self.op_dx.constraint_axis = (True, False, False)
        self.op_dx.release_confirm = True


        self.dial_y = self.gizmos.new('GIZMO_GT_dial_3d')
        self.dial_y.use_tooltip = False
        self.dial_y.use_draw_modal = True
        self.dial_y.draw_options = {'CLIP'}
        self.dial_y.alpha_highlight = highlight_alpha_gizmo
        self.dial_y.alpha = alphaGizmo
        self.dial_y.color = color_y
        self.dial_y.color_highlight = selectColor
        self.dial_y.line_width = sizeGizmo * 2
        self.dial_y.scale_basis = sizeGizmo / 2
        self.op_dy = self.dial_y.target_set_operator('transform.transform')
        self.op_dy.mode = 'ROTATION'
        self.op_dy.constraint_axis = (False, True, False)
        self.op_dy.release_confirm = True


        self.dial_z = self.gizmos.new('GIZMO_GT_dial_3d')
        self.dial_z.use_tooltip = False
        self.dial_z.use_draw_modal = True
        self.dial_z.draw_options = {'CLIP'}
        self.dial_z.alpha_highlight = highlight_alpha_gizmo
        self.dial_z.alpha = alphaGizmo
        self.dial_z.color = color_z
        self.dial_z.color_highlight = selectColor
        self.dial_z.line_width = sizeGizmo * 2
        self.dial_z.scale_basis = sizeGizmo / 2
        self.op_dz = self.dial_z.target_set_operator('transform.transform')
        self.op_dz.mode = 'ROTATION'
        self.op_dz.constraint_axis = (False, False, True)
        self.op_dz.release_confirm = True


        # --- DOT
        self.dot = self.gizmos.new('GIZMO_GT_move_3d')
        self.dot.use_tooltip = False
        self.dot.use_draw_modal = True
        self.dot.draw_options = {'FILL_SELECT', 'ALIGN_VIEW'}
        self.dot.alpha_highlight = highlight_alpha_gizmo
        self.dot.alpha = alphaGizmo
        self.dot.color = elementsColor
        self.dot.color_highlight = selectColor
        self.dot.scale_basis = sizeGizmo / 7
        self.dot.line_width = sizeGizmo * lwDot
        self.ar_dot = self.dot.target_set_operator('transform.transform')
        self.ar_dot.mode = 'TRANSLATION'
        self.ar_dot.release_confirm = True


    def invoke_prepare(self, context, gizmo):
        loc = gizmo.matrix_basis.translation
        self.ar_dot.center_override = loc
        self.op_arx.center_override = loc
        self.op_ary.center_override = loc
        self.op_arz.center_override = loc
        self.op_dx.center_override = loc
        self.op_dy.center_override = loc
        self.op_dz.center_override = loc

        matOrient = get_orient_matrix(gizmo.matrix_basis, axis='X')
        self.op_arx.orient_matrix = matOrient
        self.op_dx.orient_matrix = matOrient

        matOrient = get_orient_matrix(gizmo.matrix_basis, axis='Y')
        self.op_ary.orient_matrix = matOrient
        self.op_dy.orient_matrix = matOrient

        matOrient = get_orient_matrix(gizmo.matrix_basis, axis='Z')
        self.op_arz.orient_matrix = matOrient
        self.op_dz.orient_matrix = matOrient


    def draw_prepare(self, context):
        mX, mY, mZ = get_orient_from_type(context)
        self.arrow_x.matrix_basis = mX
        self.arrow_y.matrix_basis = mY
        self.arrow_z.matrix_basis = mZ
        self.dial_x.matrix_basis = mX
        self.dial_y.matrix_basis = mY
        self.dial_z.matrix_basis = mZ
        self.dot.matrix_basis = mZ



classes = (
    PIVOT_GT_preselect,
    PIVOT_GGT_flow_xform,
    PIVOT_GGT_flow,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)