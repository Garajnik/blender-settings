import bpy
import os
import rna_keymap_ui
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatProperty, StringProperty, FloatVectorProperty
from .icons import icons_collections
from .keymaps import pt_keymaps, get_hotkey_entry_item



def update_panel(self, context):
    from .ui.panel import PT_PT_transform_panel, PT_PT_apply, PT_PT_save, PT_PT_to_bottom_set, PT_PT_drop, PT_PT_cursor_save
    panChange = [
        PT_PT_transform_panel,
        ]

    panReg = [
        PT_PT_apply,
        PT_PT_save,
        PT_PT_to_bottom_set,
        PT_PT_drop,
        PT_PT_cursor_save,
    ]

    message = "Pivot Transform: Updating Panel locations has failed"
    try:
        for panel in panChange:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panChange:
            props = context.preferences.addons['Pivot_Transform'].preferences
            panel.bl_category = props.category
            bpy.utils.register_class(panel)

        for panel in panReg:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panReg:
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass



class PIVOTTRANSFORM_settings(PropertyGroup):
    # --- Pivot Flow
    flow: BoolProperty(
        name = 'Pivot Flow',
        description =   'Pivot Flow\n'
                        '• LMB - Position and Orientation\n'
                        '• LMB+Shift - Position\n'
                        '• LMB+Ctrl - Orientation\n'
                        '• LMB+Shift+Ctrl - Align +X',
        default = False)

    use_cursor: BoolProperty(name='Use Cursor', description='Use Cursor', default=False)
    
    # --- 3D Cursor
    cursor_gizmo: BoolProperty(name='3D Cursor Gizmo', description='Show Gizmo For 3D Cursor', default=False)


# Addon preferences
class PIVOT_transform_preferences(AddonPreferences):
    bl_idname = __package__


    # For Update
    check_updates: BoolProperty(name="Check Update When Starting The Blender", default=False)
    update: BoolProperty(name="Update", default=False)
    version: StringProperty(name="Version", default="1.0.0")

    # Panel Category
    category: StringProperty(name="Tab Category", description="Choose A Name For The Category Of The Panel", default="Pivot Transform", update=update_panel)

    flip_normals: BoolProperty(name="Flip Normals", description="Flip Normals For Meshes If One Of The Scale Axes Is Less Than 0", default=True)
    apply_panel: BoolProperty(name="Show Apply Panel In Pie Menu.", default=True)

    # --- BB
    bbox: BoolProperty(name="BBox", description='Transformation Of The Pivot Point At The Extreme Points Of The Selected One', default=False)
    bbForActive: BoolProperty(name='For Active Object', description='Moving The Pivot Only For The Active Object', default=True)
    bbCloseAfter: BoolProperty(name='Close After Use', description='', default=False)
    flowForActive: BoolProperty( name = 'For Active Object', description = 'Moving The Pivot Only For The Active Object', default = True )
    
    
    
    # --- To Bottom
    drop_to_x: BoolProperty(name="Drop To X", default=False)
    drop_to_y: BoolProperty(name="Drop To Y", default=False)
    drop_to_z: BoolProperty(name="Drop To Z", default=False)
    drop_to_active: BoolProperty(name="Drop To Active", default=False)

    TB_mode: EnumProperty(
        name="Mode", 
        items=[
            ("LOWEST_CENTER_POINT", "Lowest Median Center Point", ""), 
            ("LOWEST_ORIGIN_POINT", "Lowest Origin Point", ""),
            ("LOWEST_VERT_POINT", "Lowest Vertex Point", ""),
            ]
            )

    TB_orient: EnumProperty(
        name="Orientation", 
        items=[
            ("WORLD", "World", "World"), 
            ("OBJECT", "Object", "Object"),
            ])

    TB_use_modifier: BoolProperty(name="Use Modifier")
    TB_offset: BoolProperty(name="Offset")


    



    # OLD
    bbox_run: BoolProperty(name="update", default=False)
    
    align_to: BoolProperty(name="Align To Normal", default=True)

    gizmo_preselect: BoolProperty(name="Gizmo", description="To Enable The Gizmo In The Transformation Pivot", default=True)
    move_giz: BoolProperty(name="Move", description="Gizmo To Adjust Location", default=True)
    rotate_giz: BoolProperty(name="Rotate", description="Gizmo To Adjust Rotation", default=True)
    scale_giz: BoolProperty(name="Scale", description="Gizmo To Adjust Scale", default=True)

    
    global_save: BoolProperty(name="Global Save", default=True)


    # --- PIVOT DROP
    def items_snap(self, context):
        items = [
            ('INCREMENT', 'Increment', '', 'SNAP_INCREMENT', 2),
            ('GRID', 'Grid', '', 'SNAP_GRID', 4),
            ('VERTEX', 'Vertex', '', 'SNAP_VERTEX', 2**3),
            ('EDGE', 'Edge', '', 'SNAP_EDGE', 2**4),
            ('FACE', 'Face', '', 'SNAP_FACE', 2**5),
            ('VOLUME', 'Volume', '', 'SNAP_VOLUME', 2**6),
            ('EDGE_MIDPOINT', 'Edge Midpoint', '', 'SNAP_MIDPOINT', 2**7),
            ('EDGE_PERPENDICULAR', 'Edge Perpendicular', '', 'SNAP_PERPENDICULAR', 2**8),

            ('FACE_PROJECT', 'Face Project', '', 'SNAP_FACE', 2**9),
            ('FACE_NEAREST', 'Face Nearest', '', 'SNAP_FACE_NEAREST', 2**10),
            ]
        return items


    snap_elements: EnumProperty(
        name = 'Snap Element', 
        items = items_snap,
        description = 'Snapping Options',
        options = {'ENUM_FLAG', 'ANIMATABLE'},
        )                                        
                                                                



    """ # --- Gizmo 3D Cursor
    def update_keymaps(self, context):
        keyconfig = context.window_manager.keyconfigs.active
        km = keyconfig.keymaps.find( name = 'Gizmo 3D Cursor Tweak', space_type = 'VIEW_3D' )
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
        #update_gizmo()

    map_type: EnumProperty(
        name = 'Tweak Gizmo With Mouse Button',
        description = '',  
        items = [
                ( 'LEFTMOUSE', 'Left Mouse', '', 0), 
                ( 'MIDDLEMOUSE', 'Middle Mouse', '', 1), 
                ( 'RIGHTMOUSE', 'Right Mouse', '', 2),
                ], 
        default = 'LEFTMOUSE',
        update = update_keymaps,
        )   """                                                    




    tabs: EnumProperty(
        name = 'Tabs', 
        items = [
            ('GENERAL', 'General', ''),
            ('PRESETS', 'Presets', ''),
            ('KEYMAPS', 'Keymaps', ''),
            ],
            default = 'GENERAL',
        )


    def draw(self, context):
        layout = self.layout
  
        row = layout.row()
        row.prop(self, "tabs", expand=True)

        box = layout.box()

        if self.tabs == "GENERAL":
            self.draw_general(context, box)

        elif self.tabs == "PRESETS":
            self.draw_presets(context, box)

        elif self.tabs == "KEYMAPS":
            self.draw_keymaps(context, box)



    def draw_general(self, context, layout):
        icoll = icons_collections['main']
        market_icon = icoll['market']
        gumroad_icon = icoll['gumroad']
        artstation_icon = icoll['artstation']
        discord_icon = icoll['discord']
        blenderboi_icon = icoll['blenderboi']
        update_icon = icoll['update']


        col = layout.column()
        row = col.row()
        row.prop(self, "check_updates")
        row.operator("pt.check_updates", text='Check For Updates')
        if self.update:
            layout.label(text="New Version Is Available " + str(self.version) +"!!!", icon_value=update_icon.icon_id)
        """ elif self.version:
            layout.label(text="There Is No Update") """
        col.separator(factor=0.5)


        col = layout.column()
        col.separator(factor=0.5)

        col.prop(self, "category")
        col.separator(factor=0.5)


        col.prop(self, "apply_panel")
        col.prop(self, "flip_normals")
        col.separator(factor=0.5)


        row = layout.row(align=True)
        row.prop(self, "gizmo_preselect",text="Enable Gizmo")
        row.prop(self, "move_giz", toggle = True)
        row.prop(self, "rotate_giz", toggle = True)
        row.prop(self, "scale_giz", toggle = True)

        col = layout.column()
        col.label(text="Links")
        row = col.row()
        row.operator("wm.url_open", text="Blender Market", icon_value=market_icon.icon_id).url = "https://blendermarket.com/creators/derksen"
        row.operator("wm.url_open", text="Gumroad", icon_value=gumroad_icon.icon_id).url = "https://derksen.gumroad.com"
        row.operator("wm.url_open", text="Artstation", icon_value=artstation_icon.icon_id).url = "https://www.artstation.com/derksen"

        col.label(text="Special thanks to TinkerBoi for testing the addon, feedback")
        col.label(text="and help in developing the feature Save Pivot in list.")
        col.operator("wm.url_open", text="TinkerBoi Store", icon_value=blenderboi_icon.icon_id).url = "https://blendermarket.com/creators/blenderboi"


    def draw_presets(self, context, layout):
        layout.label(text="Pivot To Bottom:")
        row = layout.row(align=True)
        row.label(text="Drop To")
        row.prop(self, 'drop_to_x', text='X', toggle=True)
        row.prop(self, 'drop_to_y', text='Y', toggle=True)
        row.prop(self, 'drop_to_z', text='Z', toggle=True)
        layout.prop(self, 'TB_mode')
        layout.prop(self, 'TB_use_modifier')
        layout.prop(self, 'drop_to_active')

        layout.separator()

        layout.label(text="Pivot Drop:")
        col = layout.column()
        col.prop(self, 'snap_elements', expand=True)


    def get_pie_menu(self, km, operator, menu):
        for idx, kmi in enumerate(km.keymap_items):
            if km.keymap_items.keys()[idx] == operator:
                if km.keymap_items[idx].properties.name == menu:
                    return kmi
        return None


    def draw_keymaps(self, context, layout):
        col = layout.column()
        col.label(text="Keymap")
        col = layout.column()
        
        

        wm = context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps['3D View']
        col.label(text='Pie Menu:')
        kmi = get_hotkey_entry_item(km, 'wm.call_menu_pie', 'VIEW3D_MT_pie_pivot', 'name')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')


        col.separator(factor=0.5)
        

        col.label(text='General Operators:')
        kmi = get_hotkey_entry_item(km, 'pt.flow', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')


        kmi = get_hotkey_entry_item(km, 'pivot.transform_on', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        kmi = get_hotkey_entry_item(km, 'pivot.transform_off', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')
        
        kmi = get_hotkey_entry_item(km, 'pivot.drop', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        kmi = get_hotkey_entry_item(km, 'pt.to_bottom', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        kmi = get_hotkey_entry_item(km, 'pt.to_select', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        kmi = get_hotkey_entry_item(km, 'pivot.to_active', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        
   
        col.label(text='Apply Operators:')
        # --- Reset Location
        kmi = get_hotkey_entry_item(km, 'apply.location', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        # --- Reset Rotation
        kmi = get_hotkey_entry_item(km, 'apply.rotation', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        # --- Reset Scale
        kmi = get_hotkey_entry_item(km, 'apply.scale', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        # --- Reset Rotation & Scale
        kmi = get_hotkey_entry_item(km, 'apply.rotation_scale', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

        # --- Reset All
        kmi = get_hotkey_entry_item(km, 'apply.all', 'none', 'none')
        if kmi:
            col.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text='No hotkey entry found')

      

        col.label(text="*Some hotkeys may not work because of the use of other addons!!!")









classes = [
    PIVOTTRANSFORM_settings,
    PIVOT_transform_preferences,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.pivot_set = bpy.props.PointerProperty( type = PIVOTTRANSFORM_settings )

    # --- For Pivot Drop
    props = bpy.context.preferences.addons['Pivot_Transform'].preferences
    if len(props.snap_elements) == 0:
        props.snap_elements = {'VERTEX', 'EDGE', 'FACE'}
    

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)