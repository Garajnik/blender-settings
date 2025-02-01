import bpy
from bpy.types import UIList, Operator, PropertyGroup
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty, CollectionProperty, EnumProperty
from ..icons import icons_collections
from ..utils.utils import set_pivot_location, set_pivot_rotation



class PT_UL_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icoll = icons_collections[ 'main' ]
        location_icon = icoll[ 'ps_location' ]
        rotate_icon = icoll[ 'ps_rotation' ]


        row = layout.row(align=True)

        pos = row.operator("pt.set", text = '', icon_value = location_icon.icon_id )
        pos.index = index
        pos.action = 'POS'

        rot = row.operator( 'pt.set', text = '', icon_value = rotate_icon.icon_id )
        rot.index = index
        rot.action = 'ROT'

        allAct = row.operator( 'pt.set', text = 'All' )
        allAct.index = index
        allAct.action = 'ALL'

        layout.prop( item, 'name', text='', emboss = False )
        


class PT_OT_set(Operator):
    bl_idname = 'pt.set'
    bl_label = 'Set Pivot'
    bl_description = 'Set Pivot From The List. CTRL - Paste Transform'
    bl_options= {'INTERNAL'}
    
    index: IntProperty()
    
    action: EnumProperty(
        name='Axis',
        items=[
            ('POS', 'Set Position', '', '', 0),
            ('ROT', 'Set Rotation', '', '', 1),
            ('ALL', 'Set Position & Rotation', '', '', 2)],
        default='ALL',
        )

    setPos: BoolProperty(name='Paste Transform', default=False)

    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences

        if props.global_save:
            saved_props = context.scene
        else:
            saved_props = context.object


        #cursor = context.scene.cursor
        try:
            point = saved_props.pivots_[self.index].position
            rotate = saved_props.pivots_[self.index].rotation

            if self.setPos:
                objs = context.selected_objects
                for ob in objs:
                    if self.action == 'POS':
                        ob.location = point
                    elif self.action == 'ROT':
                        ob.rotation_euler = rotate
                    else:
                        ob.location = point
                        ob.rotation_euler = rotate
            else:
                if self.action in {'POS', 'ALL'}:
                    #cursor.location = point
                    set_pivot_location( self, context, location = point, undoPush = True, message = 'Pivot From Save'  )
                if self.action in {'ROT', 'ALL'}:
                    #cursor.rotation_euler = rotate
                    set_pivot_rotation( self, context, rotation = rotate, undoPush = True, message = 'Pivot From Save' )
                

            
        except:
            saved_props.pivots_Active_Index = -1
            point = saved_props.pivots_[self.index].position
            rotate = saved_props.pivots_[self.index].rotation


            if self.setPos:
                objs = context.selected_objects
                for ob in objs:
                    if self.action == 'POS':
                        ob.location = point
                    elif self.action == 'ROT':
                        ob.rotation_euler = rotate
                    else:
                        ob.location = point
                        ob.rotation_euler = rotate
            else:
                if self.action in {'POS', 'ALL'}:
                    #cursor.location = point
                    set_pivot_location( self, context, location = point, undoPush = True, message = 'Pivot From Save'  )
                if self.action in {'ROT', 'ALL'}:
                    #cursor.rotation_euler = rotate
                    set_pivot_rotation( self, context, rotation = rotate, undoPush = True, message = 'Pivot From Save' )

     
        return {'FINISHED'}        


    def invoke(self, context, event):
        self.setPos = event.ctrl
        return self.execute(context)




class PT_OT_move(Operator):
    bl_idname = 'pt.move'
    bl_label = 'Move Pivot'
    bl_description = 'Move The Pivot In The List'
    bl_options= {'REGISTER'}
    
    isUp: BoolProperty()
    
    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.global_save:
            saved_props = context.scene
        else:
            saved_props = context.object

    
        idx = saved_props.pivots_Active_Index
        
        if self.isUp and idx >= 1:
            saved_props.pivots_.move(idx, idx-1)
            saved_props.pivots_Active_Index -= 1
            
        if self.isUp==False and idx < len(saved_props.pivots_) - 1:
            saved_props.pivots_.move(idx, idx+1)
            saved_props.pivots_Active_Index += 1


        return {'FINISHED'}


        
class PT_OT_add(Operator):
    bl_idname = 'pt.add'
    bl_label = 'Add Pivot'
    bl_description = 'Save A New Pivot In The List'
    bl_options= {'REGISTER'}
    

    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.global_save:
            saved_props = context.scene
        else:
            saved_props = context.object

        point = saved_props.pivots_.add()
        point.name = "Pivot " + str(saved_props.pivots_Active_Index+2)
        point.position = context.object.location
        point.rotation = context.object.rotation_euler
        saved_props.pivots_Active_Index = len(saved_props.pivots_)-1

        return {'FINISHED'}
    
      
    
class PT_OT_remove(Operator):
    bl_idname = 'pt.remove'
    bl_label = 'Remove Pivot'
    bl_description = 'Remove An Pivot In The List'
    bl_options= {'REGISTER'}
    
    def execute(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.global_save:
            saved_props = context.scene
        else:
            saved_props = context.object


        if len(saved_props.pivots_) > 0:
            saved_props.pivots_.remove(saved_props.pivots_Active_Index)
            
            if saved_props.pivots_Active_Index == 0:
                saved_props.pivots_Active_Index += 1
            
            if saved_props.pivots_Active_Index > -1:
                saved_props.pivots_Active_Index = 0
                

        return {'FINISHED'}




class PT_store(PropertyGroup):
    position: FloatVectorProperty()
    rotation: FloatVectorProperty()

















classes = (
    PT_UL_items,
    PT_store,
    PT_OT_add,
    PT_OT_remove,

    PT_OT_set,
    PT_OT_move,
)


def register():
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.pivots_ = CollectionProperty(type=PT_store)
    bpy.types.Scene.pivots_Active_Index = IntProperty()
    
    bpy.types.Object.pivots_ = CollectionProperty(type=PT_store)
    bpy.types.Object.pivots_Active_Index = IntProperty()
    

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.pivots_
    del bpy.types.Scene.pivots_Active_Index

    del bpy.types.Object.pivots_
    del bpy.types.Object.pivots_Active_Index