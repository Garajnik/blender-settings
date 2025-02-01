bl_info = {
    'name': 'Pivot Transform',
    "description": "Pivot and 3d cursor transformation",
    'author': 'Max Derksen',
    'version': (4, 0, 0),
    'blender': (4, 2, 0),
    'location': 'VIEW 3D > Right Panel > Pivot Transform',
    #"warning": "This is a test version of the addon. Write in the discord channel(link below) about the errors.",
    'support': 'COMMUNITY',
    'category': '3D View',
    #'tracker_url': 'https://discord.gg/97q8PtB95s', # TODO
    'doc_url': 'https://max-derksen.gitbook.io/pivot-transform/',
}

import bpy
from . import icons
from . import preferences
from . import keymaps
from .preferences import update_panel

from .operators import (
    cursor_gizmo,
    cursor_save,
    ops,
    pivot_apply,
    pivot_bb, 
    pivot_save, 
    pivot_drop,
    pivot_transform, 
    pivot_to_active,
    pivot_to_select,
    pt_origin_set,
    transform_switcher, 
    pt_to_bottom, 
)

from .utils import (
    utils,
    draw,
    check_updates,
)

from .ui import (
    pie, 
    panel,
)

from .operators.pivot_flow import (
    flow,
    op,
)

from .utils.check_updates import update_version


def register():
    icons.register()
    preferences.register()
    check_updates.register()

    panel.register()
    pie.register()

    cursor_gizmo.register()
    cursor_save.register()
    ops.register()
    pivot_transform.register()
    pivot_to_active.register()
    pivot_to_select.register()
    pivot_apply.register()
    pivot_bb.register()
    pivot_save.register()
    pivot_drop.register()
    pt_to_bottom.register()
    pt_origin_set.register()
    transform_switcher.register()
    utils.register()
    draw.register()

    # --- Pivot Flow
    op.register()
    flow.register()

    keymaps.register()

    update_panel(None, bpy.context)


    props = bpy.context.preferences.addons['Pivot_Transform'].preferences
    try:
        if props.check_updates:
            check, version = update_version()
        else:
            check, version = False, False

        if check:
            props.update = True
            props.version = version
        else:
            props.update = False
    except:
        props.update = False


def unregister():
    icons.unregister()
    preferences.unregister()
    keymaps.unregister()
    check_updates.unregister()

    panel.unregister()
    pie.unregister()

    cursor_gizmo.unregister()
    cursor_save.unregister()
    ops.unregister()
    pivot_transform.unregister()
    pivot_to_active.unregister()
    pivot_to_select.unregister()
    pivot_apply.unregister()
    pivot_bb.unregister()
    pivot_save.unregister()
    pivot_drop.unregister()
    pt_to_bottom.unregister()
    pt_origin_set.unregister()
    transform_switcher.unregister()
    utils.unregister()
    draw.unregister()

    # --- Pivot Flow
    op.unregister()
    flow.unregister()