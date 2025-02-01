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

import os
import bpy
import bpy.utils.previews

ZENUV_ICONS = None


def _icon_register(fileName, base_name, prefix=''):
    name = fileName.split('.')[0]   # Don't include file extension
    ZENUV_ICONS.load(prefix + name, os.path.join(base_name, fileName), 'IMAGE')


def icon_get(name) -> int:
    global ZENUV_ICONS
    if ZENUV_ICONS is None:
        # We must not never come here !
        raise RuntimeError('It is a bug! Send log to the developers, pls :)')
    else:
        return ZENUV_ICONS[name].icon_id


# Register Icons
icons = [
    "unmark-seams_32.png",
    "mark-seams_32.png",
    "zen-unwrap_32.png",
    "Discord-Logo-White_32.png",
    "quadrify_32.png",
    "checker_32.png",
]


def register():
    global ZENUV_ICONS
    if ZENUV_ICONS is None:
        ZENUV_ICONS = bpy.utils.previews.new()

        icons_base_dir = os.path.dirname(__file__)

        for icon in icons:
            _icon_register(icon, icons_base_dir)


def unregister():
    global ZENUV_ICONS
    if ZENUV_ICONS:
        b_icon_debug = False  # Set 'True' when you are debugging icons
        if b_icon_debug:
            bpy.utils.previews.remove(ZENUV_ICONS)
            ZENUV_ICONS = None
