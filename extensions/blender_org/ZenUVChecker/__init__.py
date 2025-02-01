# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2023, Valeriy Yatsenko, Alex Zhornyak

""" Init Zen Checker """

import bpy

from . import constants
from . import ico
from .preferences import register_addon_preferences, get_prefs
from .preferences import unregister_addon_preferences

from .checker import register as register_operators
from .checker import unregister as unregister_operators

from .files import register as register_files_operators, dumps, update_files_info
from .files import unregister as unregister_files_operators

from .ui import register as register_ui
from .ui import unregister as unregister_ui

bl_info = {
    "name": "Zen UV Checker",
    "author": "Valeriy Yatsenko, Alex Zhornyak, Sergey Tyapkin, Viktor [VAN] Teplov",
    "description": "Add/Remove UV Checker Texture to the mesh",
    "blender": (2, 80, 0),
    "version": (1, 4, 12),
    "location": "View3D > Sidebar > Zen UV Checker",
    "warning": "",
    "category": "UV"
}

addon_keymaps = []


def register():
    # NOTE: do not remove 'constants' import
    print("Registering:", constants.ADDON_NAME)

    """ Register classes """
    from .checker import ZTCHK_OT_CheckerToggle

    ico.register()
    register_addon_preferences()
    register_operators()
    register_files_operators()
    register_ui()

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Window', space_type='EMPTY')
        kmi = km.keymap_items.new(ZTCHK_OT_CheckerToggle.bl_idname, 'T', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi))

    try:
        # WARNING! It may slow down addon loading !!!
        addon_prefs = get_prefs()
        addon_prefs.files_dict = dumps(update_files_info(addon_prefs.assetspath))
    except Exception as e:
        print('UPDATE CHECKER IMAGES:', e)


def unregister():
    """ Unregister classes """
    unregister_operators()
    unregister_files_operators()
    unregister_ui()
    unregister_addon_preferences()
    ico.unregister()

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()
