import bpy
from bpy.types import Operator
from mathutils import Vector


from ..utils.utils import del_duplicate, cursorPivot

from bpy.props import EnumProperty, BoolProperty



#====================== Thanks Diong Wen-Han ;)



# --- Get Coord
def co_elements(obj, edit):
    #props = bpy.context.preferences.addons['Pivot_Transform'].preferences

    co = []

    mw = obj.matrix_world
    
    if obj.type == 'MESH':
        #if props.TB_orient == 'WORLD':
        co = [mw @ v.co for v in obj.data.vertices] 
        """ else:
            co = [v.co for v in obj.data.vertices]  """

    elif obj.type == 'ARMATURE':
     
        coOld = []
        if edit == True:
            for bone in obj.data.bones:
                #if props.TB_orient == 'WORLD':
                coOld.append(mw @ bone.head_local)
                coOld.append(mw @ bone.tail_local)
                """ else:
                    coOld.append(bone.head_local)
                    coOld.append(bone.tail_local) """
        else:
            for bone in obj.pose.bones:
                #if props.TB_orient == 'WORLD':
                coOld.append(mw @ bone.head)
                coOld.append(mw @ bone.tail)
                """ else:
                    coOld.append(bone.head)
                    coOld.append(bone.tail) """
    

        co = del_duplicate(coOld)


    elif obj.type == 'CURVE':
        co = []
        for s in obj.data.splines:
            for p in s.bezier_points:
                #if props.TB_orient == 'WORLD':
                co.append(mw @ p.co)
                """ else:
                    co.append(p.co) """

    elif obj.type == 'SURFACE':
        co = []
        for s in obj.data.splines:
            for p in s.points:
                #if props.TB_orient == 'WORLD':
                co.append(mw @ p.co)
                """ else:
                    co.append(p.co) """

    elif obj.type == 'META':
        co = []
        for e in obj.data.elements:
            #if props.TB_orient == 'WORLD':
            co.append(mw @ e.co)
            """ else:
                co.append(e.co) """

    elif obj.type == 'LATTICE':
        co = []
        for p in obj.data.points:
            #if props.TB_orient == 'WORLD':
            co.append(mw @ p.co)
            """ else:
                co.append(p.co) """

    else:
        return False


    return co





class PT_OT_to_bottom(Operator):             
    bl_idname = 'pt.to_bottom'
    bl_label = 'Pivot/Cursor To Bottom'
    bl_description = 'Pivot To Bottom Of Selected Object (Ctrl+LMB - Set 3D Cursor)'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}


    drop_to_x: BoolProperty( name = 'Drop To X', default = False )
    drop_to_y: BoolProperty( name = 'Drop To Y', default = False )
    drop_to_z: BoolProperty( name = 'Drop To Z', default = False )

    mode: EnumProperty(
        name = 'Mode',
        items=[
            ("LOWEST_CENTER_POINT", "Lowest Median Center Point", ""),
            ("LOWEST_ORIGIN_POINT", "Lowest Origin Point", ""),
            ("LOWEST_VERT_POINT", "Lowest Vertex Point", ""),
            ],
            )
    """ orientation: EnumProperty(
        name = 'Orientation',
        items = [
            ('WORLD', 'World', 'World'),
            ('OBJECT', 'Object', 'Object'),
            ],
            ) """
    #offset: BoolProperty(name="Offset")

    use_modifier: BoolProperty( name = 'Use Modifier' )
    drop_to_active: BoolProperty( name = 'Drop To Active', default = False )

    cursor: BoolProperty( name = '3D Cursor', description = 'Only Affects The 3D Cursor', default = False  )
    """ direction: EnumProperty(
        name="Direction", 
        items=[
            ("XP", "X+", " "),
            ("XN", "X-", " "),
            ("YP", "Y+", " "),
            ("YN", "Y-", " "),
            ("ZP", "Z+", " "), 
            ("ZN", "Z-", " "),
            ],
        default="ZN", 
        ) """


    @classmethod
    def poll(self, context):
        return context.object.type in {'MESH', 'ARMATURE', 'CURVE', 'SURFACE', 'META', 'LATTICE'}


    """ def __init__(self):
        
        #self.selObject = None """


    def execute(self, context):
        #props = context.preferences.addons['Pivot_Transform'].preferences
       
        # --- Edit Mode
        edit = False
        if context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode = 'OBJECT')
            edit = True
        else:
            edit = False

        

        activeObj = context.active_object
        selObject = context.selected_objects

        """ if self.start:
            for obj in selObject:
                self.location_store[obj] = obj.location
            self.start = False """


        bpy.ops.object.select_all(action='DESELECT')

        for obj in selObject:
            

            """ if self.offset: # --- Offset
                location_store[obj] = obj.location """
            obj.select_set(state=True)
            
            # --- Get Co
            if self.use_modifier and obj.type == 'MESH':
                depsgraph = context.evaluated_depsgraph_get()
                object_eval = obj.evaluated_get(depsgraph)

                co = co_elements(object_eval, edit=edit)
            else:
                co = co_elements(obj, edit=edit)

            # --- Set Pivot
            if co:
                if self.mode == 'LOWEST_CENTER_POINT':
                    x = (min([v.x for v in co]) + max([v.x for v in co])) / 2
                    y = (min([v.y for v in co]) + max([v.y for v in co])) / 2
                    z = min([v.z for v in co])
                    global_origin = Vector((x, y, z))

                elif self.mode == 'LOWEST_ORIGIN_POINT':
                    loc = obj.location
                    x = loc[0] #sum([v.x for v in co]) / len(co)
                    y = loc[1] #sum([v.y for v in co]) / len(co)
                    z = min([v.z for v in co])
                    global_origin = Vector((x, y, z))

                elif self.mode == 'LOWEST_VERT_POINT':
                    z = min([v.z for v in co])
                    x = sum([v.x for v in co if v.z == z]) / len([v.x for v in co if v.z == z])
                    y = sum([v.y for v in co if v.z == z]) / len([v.y for v in co if v.z == z])
                    global_origin = Vector((x, y, z))
               

                if self.cursor:
                    context.scene.cursor.location = global_origin
                else:
                    cursorPivot(global_origin)
                    obj.select_set(state=False)

        #print(self.location_store)

        # --- Restore
        if self.cursor == False:
            for obj in selObject:
                obj.select_set(state=True)

                if self.drop_to_x:
                    obj.location[0] = 0.0
                if self.drop_to_y:
                    obj.location[1] = 0.0
                if self.drop_to_z:
                    obj.location[2] = 0.0

                """ if self.offset: # --- Offset
                    obj.location = self.location_store[obj] """

        context.view_layer.objects.active = activeObj

        if self.drop_to_active and self.cursor == False:
            bpy.ops.pivot.to_active( axis = 'ALL' )

      
        if edit: # --- Edit Mode
            bpy.ops.object.mode_set( mode = 'EDIT' )

          
        return {'FINISHED'}


    def invoke(self, context, event):
        props = context.preferences.addons['Pivot_Transform'].preferences
        
        self.cursor = event.ctrl

        #print("111")
        self.drop_to_x = props.drop_to_x
        self.drop_to_y = props.drop_to_y
        self.drop_to_z = props.drop_to_z

        self.mode = props.TB_mode
        #self.orientation = props.TB_orient
        #self.offset = props.TB_offset

        self.use_modifier = props.TB_use_modifier
        self.drop_to_active = props.drop_to_active

        
        # --- Offset
        #self.location_store = {} # --- Offset
        #self.start = True

    
        """ if self.offset: 
            for obj in context.selected_objects:
                self.location_store[obj] = obj.location """

        return self.execute(context)


    def draw(self, context):
        layout = self.layout
        
        row = layout.row( align = True )
        row.label( text = 'Drop To' ) 
        row.prop( self, 'drop_to_x', text = 'X', toggle = True )
        row.prop( self, 'drop_to_y', text = 'Y', toggle = True )
        row.prop( self, 'drop_to_z', text = 'Z', toggle = True )

        layout.prop( self, 'mode' )
        #layout.prop( self, 'orientation' )
        #layout.prop(self, 'offset')

        layout.prop( self, 'use_modifier' )
        layout.prop( self, 'drop_to_active' )

        layout.prop( self, 'cursor')
        #layout.row().prop(self, 'direction', expand=True)



classes = [ 
    PT_OT_to_bottom,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)   