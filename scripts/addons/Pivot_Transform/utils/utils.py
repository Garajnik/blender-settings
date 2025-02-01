import bpy
import bmesh
from bpy.types import Operator
from mathutils import Matrix, Vector, Euler
from bpy.props import BoolProperty




def bone_select():
    C = bpy.context

    if C.mode in {'EDIT_ARMATURE'}:
        viewlayer = C.view_layer
        collection = C.scene.statistics(viewlayer).split(" | ")

        verts_sel = collection[1]
        verts_str = verts_sel[6:].replace(',', '')
        verts_get = verts_str.split("/")[0]

        bone_sel = collection[2]
        bone_str = bone_sel[6:].replace(',', '')
        bone_get = bone_str.split("/")[0]

        verts, bones = int(verts_get), int(bone_get)

    elif C.mode in {'POSE'}:
        viewlayer = C.view_layer
        collection = C.scene.statistics(viewlayer).split(" | ")

        bone_sel = collection[1]
        bone_str = bone_sel[6:].replace(',', '')
        bone_get = bone_str.split("/")[0]
        
        verts, bones = 0, int(bone_get)

    else:
        verts, bones = 0, 0
    

    return verts, bones


def activate():
    context = bpy.context
    
    obj = context.object
    if obj is not None:
        obSel = context.selected_objects
        edObj = context.objects_in_mode_unique_data

        if context.mode == 'OBJECT':
            return len(obSel) > 0


        elif context.mode == 'EDIT_MESH' and len(edObj) > 0:
            s = context.scene.statistics(context.view_layer)
            v = s.split('Verts:')[1].split(' ')[0]
            return v[0] != '0'


        elif context.mode == 'EDIT_ARMATURE':
            verts, bone = bone_select()
            if verts > 0:
                items = [ verts ]
            elif bone > 0:
                items = [ bone ]
            v = len(items)
            return v != 0


        elif context.mode == 'POSE':
            bone = bone_select()[1]
            if bone > 0:
                items = [ bone ]
            v = len(items)
            return v != 0


        elif context.mode == 'EDIT_CURVE':
            items = []
            for obj in context.selected_objects:
                for s in obj.data.splines:
                    for p in s.bezier_points:
                        if p.select_control_point:
                            items.append(p)
                        else:
                            if p.select_left_handle:
                                items.append(p)
                            if p.select_right_handle:
                                items.append(p)
            v = len(items)
            return v != 0
        
        else:
            return False

    else:
        return False


# Delete Duplicate Vector
def del_duplicate(list):
    newList = []
    for i in list:
        if i not in newList:
            newList.append(i)
    return newList


# Change Pivot From Cursor
def cursorPivot(loc):
    context = bpy.context

    cursor_pos = context.scene.cursor.location.copy()
    context.scene.cursor.location = loc

    if context.mode == 'OBJECT':
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        context.scene.cursor.location = cursor_pos


    else:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        context.scene.cursor.location = cursor_pos
        bpy.ops.object.mode_set(mode='EDIT')


# FLIP NORMALS 
def flip_normals(operator=False):
    C = bpy.context
    for ob in C.selected_objects:
        if ob.type == 'MESH':
            if (ob.scale[0] < 0 or ob.scale[1] < 0 or ob.scale[2] < 0) or operator:
                
                me = ob.data
                if C.mode == 'EDIT_MESH':
                    bm = bmesh.from_edit_mesh(me)

                    for f in bm.faces:
                        f.normal_flip()

                    bmesh.update_edit_mesh(me) 

                else:
                    bm = bmesh.new()
                    bm.from_mesh(me)

                    #bm.normal_update()
                    for f in bm.faces:
                        f.normal_flip()

                    bm.to_mesh(me)
                    bm.free()
            else:
                pass

class PT_OT_flip_normals(Operator):
    bl_idname = 'pt.flip_normals'
    bl_label = 'Flip Normals'
    bl_description = 'Flip Normals'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    #flip_normals: BoolProperty(default=False, name='Flip Normals')

    @classmethod
    def poll(self, context):
        return context.active_object

    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.flip_normals:
            if activate():
                flip_normals(operator=True)
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, 'None Selected!')
                return {'CANCELLED'}  
        else:
            return {'CANCELLED'}       




# --- GET COORDINATES 
def co_elements(obj, edit): # TODO FIXME это не используется
    co = []

    mw = obj.matrix_world
    
    if obj.type == 'MESH':
        co = [mw @ v.co for v in obj.data.vertices] 


    elif obj.type == 'ARMATURE':
        coOld = []
        if edit == True:
            for bone in obj.data.bones:
                coOld.append(mw @ bone.head_local)
                coOld.append(mw @ bone.tail_local)
        else:
            for bone in obj.pose.bones:
                coOld.append(mw @ bone.head)
                coOld.append(mw @ bone.tail)


        co = del_duplicate(coOld)


    elif obj.type == 'CURVE':
        co = []
        for s in obj.data.splines:
            for p in s.bezier_points:
                co.append(mw @ p.co)


    elif obj.type == 'SURFACE':
        co = []
        for s in obj.data.splines:
            for p in s.points:
                co.append(mw @ p.co)


    elif obj.type == 'META':
        co = []
        for e in obj.data.elements:
            co.append(mw @ e.co)


    elif obj.type == 'LATTICE':
        co = []
        for p in obj.data.points:
            co.append(mw @ p.co)


    else:
        return False


    return co






# --- Set Pivot Location For Select Object
def set_pivot_location( 
    self,
    context,
    location = None,
    cursor = False,
    cursorReset = True,
    undoPush = False,
    message = 'Set Pivot Location',
    ):

    _cursor = context.scene.cursor
    if cursorReset and cursor is False:
        cursorPos = _cursor.location.copy()
    
    # --- Set Cursor Location
    if location:
        _cursor.location = Vector(location)
    else:
        bpy.ops.view3d.snap_cursor_to_selected()


    if cursor is False:
        # --- Check Edit Mode
        editMode = False
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set( mode = 'OBJECT' )
            editMode = True
        
        # --- Set Pivot Location
        bpy.ops.object.origin_set( type = 'ORIGIN_CURSOR', center = 'MEDIAN' )

        # --- Update Undo
        if undoPush:
            bpy.ops.ed.undo_push( message = message )
        
        # --- Restore Mode
        if editMode:
            bpy.ops.object.mode_set( mode = 'EDIT' )
    
    # --- Restore Cursor
    if cursorReset and cursor is False:
        _cursor.location = cursorPos


# --- Set Pivot Rotation For Select Object
def set_pivot_rotation( 
    self,
    context,
    rotation = None,
    cursor = False,
    cursorReset = True,
    undoPush = False,
    message = 'Set Pivot Rotation',
    ):

    _cursor = context.scene.cursor
    rotation_mode = _cursor.rotation_mode
    _cursor.rotation_mode = 'XYZ'
    cursor_rot = _cursor.rotation_euler.copy()
    userOrient = context.scene.transform_orientation_slots[0].type
    utdo = context.scene.tool_settings.use_transform_data_origin
    
    if rotation:
        _cursor.rotation_euler = Euler((rotation[0], rotation[1], rotation[2]), 'XYZ')

    if cursor is False:
        if rotation is None:
            bpy.ops.transform.create_orientation( name = 'PivotTransform', use = True, overwrite = True )
        
        # --- Check Edit Mode
        editMode = False
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set( mode = 'OBJECT' )
            editMode = True
        

        # --- Set Pivot Rotation
        if rotation:
            context.scene.tool_settings.use_transform_data_origin = True
            bpy.ops.transform.transform( mode = 'ALIGN', orient_type = 'CURSOR', orient_matrix_type = 'CURSOR' )
        else:
            context.scene.tool_settings.use_transform_data_origin = True
            bpy.ops.transform.transform( mode = 'ALIGN', orient_type = 'PivotTransform', orient_matrix_type = 'PivotTransform' )
            

        # --- Restore UTDO
        context.scene.tool_settings.use_transform_data_origin = utdo

        # --- Update Undo
        if undoPush:
            bpy.ops.ed.undo_push( message = message )

        # --- Restore Mode
        if editMode:
            bpy.ops.object.mode_set( mode = 'EDIT' )

    else:
        _cursor.rotation_mode = 'QUATERNION'
        bpy.ops.transform.create_orientation( name = 'PivotTransform', use = True, overwrite = True )
        mat = context.scene.transform_orientation_slots[0].custom_orientation.matrix.to_4x4()
        _cursor.rotation_quaternion = mat.decompose()[1]

        
    # --- Restore Cursor
    if cursorReset and cursor is False:
        _cursor.rotation_euler = cursor_rot
        _cursor.rotation_mode = rotation_mode


    # --- Сброс к начальным настройкам пользовательских настроек
    if rotation is None:
        context.window.scene.transform_orientation_slots[0].type = 'PivotTransform'
        bpy.ops.transform.delete_orientation( 'INVOKE_DEFAULT' )
        context.window.scene.transform_orientation_slots[0].type = userOrient






# --- CURSOR TO ACTIVE
class PT_OT_cursor_to_active(Operator):
    bl_idname = 'pt.cursor_to_active'
    bl_label = '3D Cursor To Active'
    bl_description = 'To Selected'
    bl_options = {'UNDO', 'INTERNAL'} # 'REGISTER', 


    position: BoolProperty(name='Position', default=True)
    rotation: BoolProperty(name='Rotation', default=True)
    to_pivot: BoolProperty(name='Snap To Pivot', default=True)


    def __init__(self):
        scene = bpy.context.window.scene
        cursor = scene.cursor

        self.init_mat = cursor.matrix
        self.init_orient = scene.transform_orientation_slots[0].type


    @staticmethod
    def cursor_orient(self, context):
        scene = context.window.scene
        cursor = scene.cursor
        cursor_pos = cursor.location.copy()
        name = 'GizmoPRO-3D_Cursor'
        scene.transform_orientation_slots[0].type = 'NORMAL'
        bpy.ops.transform.create_orientation(name=name, use=True, overwrite=True)
        user_matrix = scene.transform_orientation_slots[0].custom_orientation.matrix.to_4x4()
        cursor.matrix = Matrix.Translation(cursor_pos) @ user_matrix
        scene.transform_orientation_slots[0].type = name
        bpy.ops.transform.delete_orientation('INVOKE_DEFAULT')
        scene.transform_orientation_slots[0].type = self.init_orient


    def execute(self, context):
        scene = context.window.scene
        cursor = scene.cursor
        cursor.matrix = self.init_mat


        if self.position:
            objs = context.selected_objects
            if context.mode=='EDIT_MESH' and len(objs)>0:
                s = context.scene.statistics(context.view_layer)
                v = s.split('Verts:')[1].split(' ')[0]
                if v[0] == '0':
                    loc = [o.location for o in objs]
                    mid = sum(loc, Vector()) / len(loc)
                    cursor.location = mid
                else:
                    bpy.ops.view3d.snap_cursor_to_selected()
            else:
                bpy.ops.view3d.snap_cursor_to_selected()
         
        if self.rotation:
            objs = context.selected_objects
            if context.mode=='EDIT_MESH' and len(objs)>0:
                s = context.scene.statistics(context.view_layer)
                v = s.split('Verts:')[1].split(' ')[0]
                if v[0] == '0':
                    l = cursor.location.copy()
                    q = context.active_object.matrix_world.decompose()[1]
                    s = Vector((1,1,1))
                    cursor.matrix = Matrix.LocRotScale(l, q, s)
                else:
                    self.cursor_orient(self, context)
            else:
                self.cursor_orient(self, context)
        return {'FINISHED'}
    

    def invoke(self, context, event):
        if event.ctrl and event.shift:
            self.position = True
            self.rotation = True
        elif event.ctrl:
            self.position = False
            self.rotation = True
        elif event.shift:
            self.position = True
            self.rotation = False
        else:
            self.position = True
            self.rotation = True
        return self.execute(context)

# --- ALIGN FROM VIEW
class PT_OT_align_from_view(Operator):
    bl_idname = 'pt.align_from_view'
    bl_label = '3D Cursor Align From View'
    bl_description = 'Align From View'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        cursor = context.scene.cursor
        rotation_mode = cursor.rotation_mode
        cursor.rotation_mode = 'QUATERNION'
        cursor.rotation_quaternion =  context.region_data.view_rotation
        cursor.rotation_mode = rotation_mode
        return {'FINISHED'}


# --- RESET 3D CURSOR
class PT_OT_reset_cursor(Operator):
    bl_idname = 'pt.reset_cursor'
    bl_label = 'Reset 3D Cursor'
    bl_description = 'Ctrl+LMB: Selected Objects To Cursor'
    bl_options = {'UNDO'} # 'REGISTER', 

    loc: BoolProperty( name = 'Location', default = True )
    rot: BoolProperty( name = 'Position', default = True )


    @classmethod
    def description(self, context, properties):
        if properties.loc and properties.rot:
            return 'Location & Rotation (Ctrl+LMB: Selected Objects To Cursor)' 
        elif properties.loc:
            return 'Location (Ctrl+LMB: Selected Objects To Cursor)'
        elif properties.rot:
            return 'Rotation (Ctrl+LMB: Selected Objects To Cursor)'
    

    def invoke(self, context, event):

        if self.loc:
            if event.ctrl:
                cursorLoc = context.scene.cursor.location
                objs = context.selected_objects
                for ob in objs:
                    ob.location = cursorLoc
            else:
                context.scene.cursor.location = Vector()
            
        if self.rot:
            cursor = context.scene.cursor
            cursorMode = cursor.rotation_mode
            cursor.rotation_mode = 'XYZ'

            if event.ctrl:
                objs = context.selected_objects
                for ob in objs:
                    obMode = ob.rotation_mode
                    ob.rotation_mode = 'XYZ'
                    ob.rotation_euler = cursor.rotation_euler
                    ob.rotation_mode = obMode
            else:
                cursor.rotation_euler = Euler()

            cursor.rotation_mode = cursorMode
        return {'FINISHED'}




classes = [
    PT_OT_flip_normals,

    PT_OT_cursor_to_active,
    PT_OT_align_from_view,
    PT_OT_reset_cursor,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)