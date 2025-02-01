import bpy
from bpy.types import UIList, Operator, PropertyGroup
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty, CollectionProperty, EnumProperty
from ..icons import icons_collections



class PTG3_UL_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icoll = icons_collections[ 'main' ]
        pos_res = icoll[ 'cur_location' ]
        rot_res = icoll[ 'cur_rotation' ]

        row = layout.row( align = True )
    
        pos = row.operator( 'ptg3.set', text = '', icon_value = pos_res.icon_id )
        pos.index = index
        pos.action = 'POS'

        rot = row.operator( 'ptg3.set', text = '', icon_value = rot_res.icon_id )
        rot.index = index
        rot.action = 'ROT'

        allAct = row.operator( 'ptg3.set', text = 'All' )
        allAct.index = index
        allAct.action = 'ALL'

        layout.prop( item, 'name', text = '', emboss = False )
        


class PTG3_OT_set(Operator):
    bl_idname = 'ptg3.set'
    bl_label = 'Set'
    bl_description = 'Set Transformation 3D Cursor From The List'
    bl_options= {'REGISTER'}
    
    index: IntProperty()
    
    action: EnumProperty(
        name='Axis',
        items=[
            ('POS', 'Set Position', '', '', 0),
            ('ROT', 'Set Rotation', '', '', 1),
            ('ALL', 'Set Position & Rotation', '', '', 2)],
        default='ALL',
        )


    def execute(self, context):
        saved_props = context.scene
        
     
        try:
            point = saved_props.cursor_transformation_[self.index].position
            rotate = saved_props.cursor_transformation_[self.index].rotation

            if self.action in {'POS', 'ALL'}:
                context.scene.cursor.location = point
            
            if self.action in {'ROT', 'ALL'}:
                context.scene.cursor.rotation_euler = rotate
            
        except:
            saved_props.cursor_Active_Index = -1
            point = saved_props.cursor_transformation_[self.index].position
            rotate = saved_props.cursor_transformation_[self.index].rotation

            if self.action in {'POS', 'ALL'}:
                context.scene.cursor.location = point
            
            if self.action in {'ROT', 'ALL'}:
                context.scene.cursor.rotation_euler = rotate

     
        return {'FINISHED'}        
        

        
class PTG3_OT_move(Operator):
    bl_idname = 'ptg3.move'
    bl_label = 'Move'
    bl_description = 'Move The Transformation 3D Cursor In The List'
    bl_options= {'REGISTER'}
    
    isUp: BoolProperty()
    
    def execute(self, context):
        saved_props = context.scene
       
        idx = saved_props.cursor_Active_Index
        
        if self.isUp and idx >= 1:
    
            saved_props.cursor_transformation_.move(idx, idx-1)
            saved_props.cursor_Active_Index -= 1
            
        if self.isUp==False and idx < len(saved_props.cursor_transformation_) - 1:
    
            saved_props.cursor_transformation_.move(idx, idx+1)
            saved_props.cursor_Active_Index += 1


        return {'FINISHED'}


        
class PTG3_OT_add(Operator):
    bl_idname = 'ptg3.add'
    bl_label = 'Add'
    bl_description = 'Save A New Transformation 3D Cursor In The List'
    bl_options= {'REGISTER'}
    

    def execute(self, context):
        saved_props = context.scene

        point = saved_props.cursor_transformation_.add()
        point.name = "3D Cursor " + str(saved_props.cursor_Active_Index+2)
        point.position = context.scene.cursor.location
        point.rotation = context.scene.cursor.rotation_euler
            
        saved_props.cursor_Active_Index = len(saved_props.cursor_transformation_)-1

        return {'FINISHED'}
    
      
    
class PTG3_OT_remove(Operator):
    bl_idname = 'ptg3.remove'
    bl_label = 'Remove'
    bl_description = 'Remove An Transformation 3D Cursor In The List'
    bl_options= {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        saved_props = context.scene
        
        if len(saved_props.cursor_transformation_) > 0:
            saved_props.cursor_transformation_.remove(saved_props.cursor_Active_Index)
            
            if saved_props.cursor_Active_Index == 0:
                saved_props.cursor_Active_Index += 1
            
            if saved_props.cursor_Active_Index > -1:
                saved_props.cursor_Active_Index = 0
                

        return {'FINISHED'}



class PTG3_store(PropertyGroup):
    position: FloatVectorProperty()
    rotation: FloatVectorProperty()



classes = (
    PTG3_UL_items,
    PTG3_OT_set,
    PTG3_OT_move,
    PTG3_OT_add,
    PTG3_OT_remove,
    PTG3_store,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.cursor_transformation_ = CollectionProperty( type = PTG3_store )
    bpy.types.Scene.cursor_Active_Index = IntProperty()
    
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.cursor_transformation_
    del bpy.types.Scene.cursor_Active_Index