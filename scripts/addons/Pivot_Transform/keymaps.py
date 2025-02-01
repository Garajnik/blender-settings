import bpy


def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if properties == 'name':
                if km.keymap_items[i].properties.name == kmi_value:
                    return km_item
            elif properties == 'tab':
                if km.keymap_items[i].properties.tab == kmi_value:
                    return km_item
            elif properties == 'none':
                return km_item
    return None


pt_keymaps = []


def register():
    # --- Keymap
    wm = bpy.context.window_manager
    key_conf = wm.keyconfigs.addon
    active_key_conf = wm.keyconfigs.active
   
    if not key_conf:
        return

   


    # --- All
    km = key_conf.keymaps.new(name='3D View', space_type='VIEW_3D')
    # --- Pie
    kmi = km.keymap_items.new('wm.call_menu_pie', type='A', value='PRESS', ctrl=False, alt=True, shift=True)
    kmi.properties.name = 'VIEW3D_MT_pie_pivot'
    pt_keymaps.append((km, kmi))


    kmi = km.keymap_items.new('pt.flow', type='D', value='CLICK', shift=False, repeat=False)
    pt_keymaps.append((km, kmi))


    kmi = km.keymap_items.new( 'pivot.transform_on', type = 'T', value='PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))
    kmi = km.keymap_items.new( 'pivot.transform_off', type = 'Z', value='PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))



    kmi = km.keymap_items.new( 'pivot.drop', type = 'Q', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'pt.to_bottom', type = 'X', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'pivot.align_from_sel', type = 'P', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'pt.to_select', type = 'D', value = 'DOUBLE_CLICK', ctrl = False, alt = False, shift = False)
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'apply.location', type = 'J', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'apply.rotation', type = 'K', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'apply.scale', type = 'L', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'apply.rotation_scale', type = 'T', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'apply.all', type = 'E', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))

    kmi = km.keymap_items.new( 'pivot.to_active', type = 'Y', value = 'PRESS', ctrl = True, alt = True, shift = True )
    kmi.active = False
    pt_keymaps.append((km, kmi))
        
    """ kmi = km.keymap_items.new( 'wm.context_toggle', type = 'C', value = 'CLICK', ctrl = True, alt = True, shift = True )
    kmi.properties.data_path = 'preferences.bbox'
    kmi.properties.module = 'Pivot Transform'
    pt_keymaps.append((km, kmi)) """
  


def unregister():
    # --- Remove Keymap
    for km, kmi in pt_keymaps:
        km.keymap_items.remove(kmi)

    pt_keymaps.clear()