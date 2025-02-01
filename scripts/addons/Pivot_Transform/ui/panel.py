import bpy
from bpy.types import Operator, Panel
import re

from ..icons import icons_collections



def draw_apply(self, context):
    icoll = icons_collections['main']
    apply_icon = icoll['apply']
    layout = self.layout
    layout.separator()
    if context.scene.tool_settings.use_transform_data_origin:
        layout.operator('pivot.transform_off', text='Apply Pivot Transform',  icon_value=apply_icon.icon_id)
        

class PT_PT_to_bottom_set(Panel):
    bl_label = 'Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_idname = 'PT_PT_to_bottom_set'

    def draw(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        layout = self.layout
        
        row = layout.row(align=True)
        row.label(text="Drop To")
        row.prop(props, 'drop_to_x', text='X', toggle=True)
        row.prop(props, 'drop_to_y', text='Y', toggle=True)
        row.prop(props, 'drop_to_z', text='Z', toggle=True)

        layout.prop(props, 'TB_mode')
        #layout.prop(props, 'TB_orient')
        #layout.prop(props, 'TB_offset')

        layout.prop(props, 'TB_use_modifier')
        layout.prop(props, 'drop_to_active')
      

class PT_PT_drop(Panel):
    bl_label = "Pivot Drop"
    bl_idname = 'PT_PT_drop'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        icoll = icons_collections[ 'main' ]
        save_icon = icoll[ 'pt_save' ]

        props = context.preferences.addons['Pivot_Transform'].preferences
        layout = self.layout
        col = layout.column()
        col.prop( props, 'snap_elements', expand = True )
        col.separator()
        col.operator( 'wm.save_userpref', text = 'Save Preferences', icon_value = save_icon.icon_id )


def panel_save_pivot(layout):
    icoll = icons_collections["main"]
    up_icon = icoll[ 'ps_up' ]
    down_icon = icoll[ 'ps_down' ]
    add_icon = icoll[ 'ps_add' ]
    remove_icon = icoll[ 'ps_remove' ]
    global_icon = icoll[ 'ps_global' ]
    location_icon = icoll[ 'ps_location' ]
    rotate_icon = icoll[ 'ps_rotation' ]
    save_icon = icoll[ 'ps_save' ]
    

    props = bpy.context.preferences.addons['Pivot_Transform'].preferences

    if props.global_save:
        saved_props = bpy.context.scene
    else:
        saved_props = bpy.context.object

    if len(saved_props.pivots_) > 0:
        row = layout.row()
        row.template_list( 'PT_UL_items', '', saved_props, 'pivots_', saved_props, 'pivots_Active_Index' )
        
        col = row.column( align = True )
        col.operator( 'pt.add', text = '', icon_value = add_icon.icon_id )
        col.operator('pt.remove', text = '', icon_value = remove_icon.icon_id )
        col.separator()
        col.operator( 'pt.move', text = '', icon_value = up_icon.icon_id ).isUp = True
        col.operator( 'pt.move', text = '', icon_value = down_icon.icon_id ).isUp = False
        col.separator()
        if props.global_save:
            col.prop( props, 'global_save', text = '', icon_value = global_icon.icon_id )
        else:
            col.prop( props, 'global_save', text = '', icon_value = global_icon.icon_id )



        # данные позиции и вращения
        col = layout.column( align = True )
        row = col.row( align = True )
        row.label( icon_value = location_icon.icon_id )
        row.prop( saved_props.pivots_[saved_props.pivots_Active_Index], 'position', text = '' )

        row = col.row( align = True )
        row.label( icon_value = rotate_icon.icon_id )
        row.prop( saved_props.pivots_[saved_props.pivots_Active_Index], 'rotation', text = '' )

    else:
        row = layout.row()
        row.operator( 'pt.add', text = 'Save Pivot', icon_value = save_icon.icon_id )
        row.prop( props, 'global_save', text = '', icon_value = global_icon.icon_id )


class PT_PT_save(Panel):
    bl_label = 'Pivot Save'
    bl_idname = 'PT_PT_save'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'PT_PT_transform_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        panel_save_pivot(self.layout)


def panel_save_cursor(layout):
    icoll = icons_collections['main']
    add = icoll['cur_add']
    remove = icoll['cur_remove']
    up = icoll['cur_up']
    down = icoll['cur_down']
    pos_res = icoll['cur_location']
    rot_res = icoll['cur_rotation']
    save = icoll['cur_save']

    saved_props = bpy.context.scene
    if len(saved_props.cursor_transformation_) > 0:
        row = layout.row()
        row.template_list( 'PTG3_UL_items', '', saved_props, 'cursor_transformation_', saved_props, 'cursor_Active_Index' )
        
        col = row.column(align=True)
        col.operator( 'ptg3.add', text = '', icon_value = add.icon_id )
        col.operator( 'ptg3.remove', text = '', icon_value = remove.icon_id )
        col.separator()
        col.operator( 'ptg3.move', text = '', icon_value = up.icon_id ).isUp = True
        col.operator( 'ptg3.move', text = '', icon_value = down.icon_id ).isUp = False


        # --- данные позиции и вращения
        col = layout.column( align = True )
        row = col.row( align = True )
        row.label( icon_value = pos_res.icon_id )
        row.prop( saved_props.cursor_transformation_[saved_props.cursor_Active_Index], 'position', text = '' )

        row = col.row( align = True )
        row.label( icon_value = rot_res.icon_id )
        row.prop( saved_props.cursor_transformation_[saved_props.cursor_Active_Index], 'rotation', text = '' )

    else:
        layout.operator( 'ptg3.add', text = 'Save Cursor', icon_value = save.icon_id )


class PT_PT_cursor_save(Panel):
    bl_label = '3d Cursor Save'
    bl_idname = 'PT_PT_cursor_save'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'PT_PT_transform_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        panel_save_cursor(self.layout)


class PT_PT_apply(Panel):
    bl_label = 'Pivot Apply'
    bl_idname = 'PT_PT_apply'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = 'PT_PT_transform_panel'
    bl_options = {'DEFAULT_CLOSED'}
    #use_pin = True

    def draw(self, context):
        icoll = icons_collections['main']
        pa_location_icon = icoll['pa_location']
        pa_rotation_icon = icoll['pa_rotation']
        pa_scale_icon = icoll['pa_scale']
        pa_xf_icon = icoll['pa_xf']
        pa_rotation_scale_icon = icoll['pa_rotation_scale']
        normals_icon = icoll['normals']

        props = context.preferences.addons['Pivot_Transform'].preferences
        layout = self.layout

        row = layout.row(align=True)
        row.operator('apply.location', text='Loc.', icon_value=pa_location_icon.icon_id)
        row.operator('apply.rotation', text='Rot.', icon_value=pa_rotation_icon.icon_id)
        row.operator('apply.scale', text='Sca.', icon_value=pa_scale_icon.icon_id)

        layout.operator('apply.all', text = 'Apply All Transform', icon_value=pa_xf_icon.icon_id)
   
        row = layout.row(align=True)
        row.operator('apply.rotation_scale', text='Rotation & Scale', icon_value=pa_rotation_scale_icon.icon_id)
        if props.flip_normals:
            row.operator('pt.flip_normals', text='', icon_value=normals_icon.icon_id) 



class PT_PT_transform_panel(Panel):
    bl_label = ''
    bl_idname = 'PT_PT_transform_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pivot Transform'


    @classmethod
    def poll(self, context):
        ob = context.object
        props = context.preferences.addons['Pivot_Transform'].preferences
        if props.bbox_run == False:
            return context.active_object and (ob.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'ARMATURE', 'LATTICE', 'GPENCIL', 'EMPTY'})

    
    def draw_header(self, context):
        if self.is_popover is False: # --- For Gizmo PRO Pie Menu
            icoll = icons_collections['main']
            pt_icon = icoll['pt']
            layout = self.layout
            layout.label(text='Pivot Transform', icon_value=pt_icon.icon_id)


    def draw_header_preset(self, context):
        #if self.is_popover is False: # --- For Gizmo PRO Pie Menu
        icoll = icons_collections['main']
        settings_icon = icoll['settings']

        props = context.preferences.addons['Pivot_Transform'].preferences
        settings = context.scene.pivot_set

        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.5

        row.operator('pt.panel_settings', text='', icon_value=settings_icon.icon_id)


    def draw(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        settings = context.scene.pivot_set

        icoll = icons_collections["main"]
        bbox_icon = icoll['bbox']
        flow_icon = icoll['flow']
        drop_icon = icoll['drop']
        apply_icon = icoll['apply']
        run_icon = icoll['run']
        normals_icon = icoll['normals']
        select_icon = icoll['select']
        cursor_icon = icoll['cursor']
        tg_on = icoll['tg_on']
        tg_off = icoll['tg_off']
        update = icoll['update']
        to_bottom_icon = icoll['to_bottom']
        mesh_to_pivot_icon = icoll['mesh_to_pivot']
        to_pivot_icon = icoll['to_pivot']
        geom_icon = icoll['geom']
        
        gg_cursor_icon = icoll['gg_cursor']
        to_sel_cursor_icon = icoll['to_sel_cursor']
        loc_cursor_icon = icoll['loc_cursor']
        rot_cursor_icon = icoll['rot_cursor']
        view_cursor_icon = icoll['view_cursor']
        
        
        
        layout = self.layout
        row = layout.column_flow(columns=4, align=False)
        #row_f.scale_y = 1.4

        transform = row.column()
        if context.scene.tool_settings.use_transform_data_origin and settings.flow is False:
            transform.alert = True
            transform.operator('pivot.transform_off', text='', icon_value=apply_icon.icon_id) 
        else:
            transform.alert = False
            transform.operator('pivot.transform_on', text='', icon_value=run_icon.icon_id) 

        flow_col = row.column()
        if settings.flow:
            flow_col.alert = True
            flow_col.operator('pt.flow', text='', icon_value=flow_icon.icon_id)
        else:
            flow_col.alert = False
            flow_col.operator('pt.flow', text='', icon_value=flow_icon.icon_id)
   
        row.prop(props, 'bbox', text='', icon_value=bbox_icon.icon_id)
        row.operator('pivot.drop', text='', icon_value=drop_icon.icon_id)


        layout.operator('pt.to_bottom', text='To Bottom', icon_value=to_bottom_icon.icon_id)
        #row.popover(panel='PT_PT_to_bottom_set', text='', icon='DOWNARROW_HLT')
        #row_top.separator(factor=0.2)
        """ row = row_t.row(align=True)
        row.operator('pivot.drop', text='Drop', icon_value=drop_icon.icon_id)   # PIVOT DROP
        row.popover(panel='PT_PT_drop', text='', icon='DOWNARROW_HLT') """






        if context.mode == 'OBJECT':
            row = layout.row(align=True)
            row.operator('pivot.to_active', text = 'To Active', icon_value = to_pivot_icon.icon_id).axis = 'ALL'
            row.scale_x = 0.2
            row.operator('pivot.to_active', text = 'X').axis = 'X'
            row.operator('pivot.to_active', text = 'Y').axis = 'Y'
            row.operator('pivot.to_active', text = 'Z').axis = 'Z'

        
            row = layout.column_flow(columns=3, align=False)
            row.operator('pt.origin_set', text='', icon_value=cursor_icon.icon_id).type = 'ORIGIN_CURSOR' # To 3D Cursor
            row.operator('pt.origin_set', text='', icon_value=geom_icon.icon_id).type = 'ORIGIN_CENTER_OF_MASS'
            row.operator('pt.origin_set', text='', icon_value=mesh_to_pivot_icon.icon_id).type = 'GEOMETRY_ORIGIN'
            
        else:
            row = layout.row()
            row.scale_x = 1.4
            row.prop(props,'align_to', text='', icon_value=normals_icon.icon_id)
            row.operator('pt.to_select', text='To Select', icon_value=select_icon.icon_id)
            row.operator('pt.origin_set', text='', icon_value=mesh_to_pivot_icon.icon_id).type = 'GEOMETRY_ORIGIN'
        

        row = layout.column_flow(columns=5, align=False)
        row.prop(settings, 'cursor_gizmo', text='', icon_value=gg_cursor_icon.icon_id)
        row.operator('pt.cursor_to_active', text='', icon_value=to_sel_cursor_icon.icon_id)
        op = row.operator('pt.reset_cursor', text='', icon_value=loc_cursor_icon.icon_id)
        op.loc = True
        op.rot = False
        op = row.operator('pt.reset_cursor', text='', icon_value=rot_cursor_icon.icon_id)
        op.loc = False
        op.rot = True
        row.operator('pt.align_from_view', text='', icon_value=view_cursor_icon.icon_id)
     
      
        # For Update
        if props.update:
            layout.label(text="New Version Is Available " + str(props.version) +"!!!", icon_value=update.icon_id)




classes = [
    PT_PT_transform_panel,
    PT_PT_drop,
    PT_PT_apply,
    PT_PT_save,
    PT_PT_cursor_save,
    PT_PT_to_bottom_set,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_editor_menus.append(draw_apply)
  
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_editor_menus.remove(draw_apply)