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

""" Zen UV Generic Functions"""

import bpy

_checker_previews = None


def get_checker_previews():
    global _checker_previews
    if _checker_previews is None:
        import bpy.utils.previews
        _checker_previews = bpy.utils.previews.new()
    return _checker_previews


def get_current_shading_style(context):
    """ Return Shading Style from current viewport """
    from .preferences import get_scene_props
    if context.area.type == 'IMAGE_EDITOR':
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        return space.shading.color_type
    elif context.area.type == 'VIEW_3D':
        for space in context.area.spaces:
            if space.type == 'VIEW_3D':
                return space.shading.color_type
    else:
        return get_scene_props(context).prev_color_type


def update_image_in_uv_layout(context, _image):
    from .preferences import get_prefs

    for area in context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            if get_prefs().ShowCheckerInUVLayout and _image:
                area.spaces.active.image = _image
            else:
                area.spaces.active.image = None


def switch_shading_style(context, style, switch):
    """ Switch Shading style in current viewport """
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if space.shading.color_type == "VERTEX" and style == "VERTEX" and switch:
                        style = "MATERIAL"
                    if space.shading.type != 'WIREFRAME':
                        space.shading.color_type = style

                    return True
    return False


def resort_by_type_mesh_in_edit_mode_and_sel(context: bpy.types.Context):
    """ Return objects in edit mode and selected
        without instances """
    if context.mode == 'EDIT_MESH':
        return {
            obj for obj in context.objects_in_mode_unique_data
            if obj.type == 'MESH' and len(obj.data.polygons) != 0
            and obj.hide_get() is False
            and obj.hide_viewport is False
        }
    else:
        t_objects = {
            obj.data: obj for obj in context.selected_objects
            if obj.type == 'MESH'
            and len(obj.data.polygons) != 0
            and obj.hide_get() is False
            and obj.hide_viewport is False
        }
        return t_objects.values()


if __name__ == "__main__":
    pass
