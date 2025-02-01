import bpy
from bpy.types import Menu
from ..icons import icons_collections


def pivot_apply(context, layout):
    props = context.preferences.addons['Pivot_Transform'].preferences

    icoll = icons_collections['main']
    update = icoll['update' ]
    pa_location_icon = icoll[ 'pa_location']
    pa_rotation_icon = icoll['pa_rotation']
    pa_scale_icon = icoll['pa_scale']
    pa_xf_icon = icoll['pa_xf']
    pa_rotation_scale_icon = icoll['pa_rotation_scale']
    normals_icon = icoll['normals']

    box = layout.box()
    box.scale_x = 1.0
    box.scale_y = 1.3

    if props.update:
        box.label(text='New Version Is Available ' + str(props.version) +'!!!', icon_value=update.icon_id)

    row = box.row(align=True)
    row.operator('apply.location', text='Loc.', icon_value=pa_location_icon.icon_id)
    row.operator('apply.rotation', text='Rot.', icon_value=pa_rotation_icon.icon_id)
    row.operator('apply.scale', text='Sca.', icon_value=pa_scale_icon.icon_id)

    box.operator('apply.all', text='Apply All Transform', icon_value=pa_xf_icon.icon_id)

    row = box.row(align=True)
    row.operator('apply.rotation_scale', text='Rotation & Scale', icon_value=pa_rotation_scale_icon.icon_id)
    if props.flip_normals:
        row.operator('pt.flip_normals', text='', icon_value=normals_icon.icon_id) 


def obj_ops(context, layout):
    props = context.preferences.addons['Pivot_Transform'].preferences
    settings = context.scene.pivot_set

    icoll = icons_collections[ 'main' ]
    cursor_icon = icoll[ 'cursor' ]
    mesh_to_pivot_icon = icoll[ 'mesh_to_pivot' ]
    geom_icon = icoll[ 'geom' ]
    bbox_icon = icoll[ 'bbox' ]
    tg_on = icoll[ 'tg_on' ]
    tg_off = icoll[ 'tg_off' ]
    ps_save_icon = icoll[ 'ps_save' ]
    cs_save_icon = icoll['cur_save']
    flow_icon = icoll[ 'flow' ]


    col = layout.column(align=True)
    col.scale_x = 0.9
    col.scale_y = 1.2

    box = col.box()
    box.operator('pt.origin_set', text='Pivot To 3d Cursor', icon_value=cursor_icon.icon_id).type = 'ORIGIN_CURSOR'
    box.operator('pt.origin_set', text='Mesh To Pivot', icon_value=mesh_to_pivot_icon.icon_id).type = 'GEOMETRY_ORIGIN'
    row = box.row()
    row.label(icon_value=geom_icon.icon_id)
    row.operator('pt.origin_set', text='Mesh').type = 'ORIGIN_GEOMETRY'
    row.operator('pt.origin_set', text='Mass').type = 'ORIGIN_CENTER_OF_MASS'
    row.operator('pt.origin_set', text='Volume').type = 'ORIGIN_CENTER_OF_VOLUME'

    
    box = col.box()
    if props.bbox:
        box = box.box()
        box.prop(props, 'bbox', text='BBox', icon_value=bbox_icon.icon_id)
    else:
        box.prop(props, 'bbox', text='BBox', icon_value=bbox_icon.icon_id)


    row = box.row()
    
    flow_col = row.column()
    if settings.flow:
        flow_col.alert = True
        flow_col.operator('pt.flow', text='Exit Flow', icon_value=flow_icon.icon_id)
    else:
        flow_col.alert = False
        flow_col.operator('pt.flow', text='Flow', icon_value=flow_icon.icon_id)
        
    box = col.box()
    box.popover(panel='PT_PT_save', icon_value=ps_save_icon.icon_id)
    box.popover(panel='PT_PT_cursor_save', icon_value=cs_save_icon.icon_id)


def bbox(context, layout):
    props = context.preferences.addons['Pivot_Transform'].preferences

    icoll = icons_collections[ 'main' ]
    bbox_icon = icoll[ 'bbox' ]
    tg_on = icoll[ 'tg_on' ]
    tg_off = icoll[ 'tg_off' ]

    if props.bbox:
        box = layout.box()
        box.prop( props, 'bbox', text='BBox', icon_value=bbox_icon.icon_id )
        if props.bbForActive:
            box.prop( props, 'bbForActive', icon_value=tg_on.icon_id, emboss=False )
        else:
            box.prop( props, 'bbForActive', icon_value=tg_off.icon_id, emboss=False ) 

        if props.bbCloseAfter:
            box.prop( props, 'bbCloseAfter', icon_value=tg_on.icon_id, emboss=False )
        else:
            box.prop( props, 'bbCloseAfter', icon_value=tg_off.icon_id, emboss=False )

    else:
        layout.prop( props, 'bbox', text='BBox', icon_value=bbox_icon.icon_id )



class VIEW3D_MT_pie_pivot(Menu):
    bl_idname = 'VIEW3D_MT_pie_pivot'
    bl_label = 'Pie Menu'


    @classmethod
    def poll(cls, context):
        mesh_type = {'MESH', 'CURVE', 'SURFACE', 'META', 'ARMATURE', 'LATTICE', 'GPENCIL', 'EMPTY'}
        return context.active_object and context.object.type in mesh_type
        

    def draw(self, context):
        props = context.preferences.addons['Pivot_Transform'].preferences
        settings = context.scene.pivot_set

        layout = self.layout
        icoll = icons_collections['main']
        flow_icon = icoll['flow']
        drop_icon = icoll['drop']
        apply_icon = icoll['apply']
        run_icon = icoll['run']
        normals_icon = icoll['normals']
        select_icon = icoll['select']
        to_bottom_icon = icoll['to_bottom']
        mesh_to_pivot_icon = icoll['mesh_to_pivot']
        to_pivot_icon = icoll['to_pivot']
        bbox_icon = icoll['bbox']
        tg_on = icoll['tg_on']
        tg_off = icoll['tg_off']

        pie = layout.menu_pie()
        
        if settings.flow:
            #1
            pie.operator('pt.flow', text='Flow', icon_value=flow_icon.icon_id)

            #2
            pie.operator('pt.reset_position')

            #3
            pie.operator('pt.reset_rotation')
        elif props.bbox:
            #1
            pie.prop(props, 'bbox', text='BBox', icon_value=bbox_icon.icon_id)

            """ #2
            pie.prop(props, 'bbForActive', emboss=False)

            #3
            pie.prop(props, 'bbCloseAfter', emboss=False) """
            if props.bbForActive:
                pie.prop(props, 'bbForActive', icon_value=tg_on.icon_id, emboss=False) # --- For Active
            else:
                pie.prop(props, 'bbForActive', icon_value=tg_off.icon_id, emboss=False) 

            if props.bbCloseAfter:
                pie.prop(props, 'bbCloseAfter', icon_value=tg_on.icon_id, emboss=False) # --- Close After
            else:
                pie.prop(props, 'bbCloseAfter', icon_value=tg_off.icon_id, emboss=False) #expand=True, emboss=True,

        else:
            #if context.active_object != None and context.object.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'ARMATURE', 'LATTICE', 'GPENCIL', 'EMPTY'}:
            #1
            if context.scene.tool_settings.use_transform_data_origin:
                pie.operator('pivot.transform_off', text='Apply', icon_value=apply_icon.icon_id) 
            else:
                pie.operator('pivot.transform_on', text='Transform', icon_value=run_icon.icon_id) 
            

            #2
            if context.mode == 'OBJECT':
                obj_ops(context, pie)
            else:
                pie.operator('pt.flow', text='Flow', icon_value=flow_icon.icon_id)
                

            #3
            if context.object.type in {'MESH', 'ARMATURE', 'CURVE'}:
                pie.operator('pt.to_bottom', text='Pivot To Bottom', icon_value=to_bottom_icon.icon_id)


            else:
                pie.separator()


            #4
            if props.apply_panel:
                pivot_apply(context, pie)
            else:
                if props.update:
                    box = pie.box()
                    box.label(text='New Version Is Available ' + str(props.version) + '!!!')
                else:
                    pie.separator()


            #5
            pie.operator('pivot.drop', text='Drop', icon_value=drop_icon.icon_id)


            #6
            if context.mode == 'EDIT_MESH':
                bbox(context, pie)
            else:
                pie.separator()


            #7
            if context.mode == 'OBJECT':
                row = pie.row(align=True)
                row.scale_y = 1.3
                row.scale_x = 1.3

                sub = row.row(align=True)
                sub.scale_x = 0.75
                sub.operator('pivot.to_active', text='X').axis = 'X'
                sub.operator('pivot.to_active', text='Y').axis = 'Y'
                sub.operator('pivot.to_active', text='Z').axis = 'Z'
                row.operator('pivot.to_active', text='To Active', icon_value=to_pivot_icon.icon_id).axis = 'ALL'
                


            else:
                if context.object.type in {'MESH', 'ARMATURE', 'CURVE'}:
                    row = pie.row(align=True)
                    row.scale_x = 1.3
                    row.scale_y = 1.3
                    row.prop(props, 'align_to', text='', icon_value=normals_icon.icon_id)
                    row.separator(factor=0.2)
                    row.operator('pt.to_select', text='To Select', icon_value=select_icon.icon_id) 
                else:
                    pie.separator()


            #8
            if context.mode == 'OBJECT':
                pie.separator()
            else:
                pie.operator('pt.origin_set', text='Mesh To Pivot', icon_value=mesh_to_pivot_icon.icon_id).type = 'GEOMETRY_ORIGIN'


                
            
            """ else:
                other = pie.column()
                other_menu = other.box().column()
                other_menu.label( text = 'This Is Not An MESH, CURVE, SURFACE, META, ARMATURE, LATTICE, GPENCIL !!!', icon_value = fix_icon.icon_id )    
            """



















classes = [
    VIEW3D_MT_pie_pivot,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)