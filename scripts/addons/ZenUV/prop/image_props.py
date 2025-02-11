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

# Copyright 2023, Alex Zhornyak

import bpy

import uuid

from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetGroup
from ZenUV.ops.trimsheets.trimsheet_preview import (
    get_enum_previews,
    enum_previews_from_directory_items)
from ZenUV.ops.trimsheets.trimsheet_props import ZuvTrimsheetOwnerProps
from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens
from ZenUV.prop.world_scale_props import ZUV_WorldScaleProps


def on_zenuv_trimsheet_previews_update(self, context):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = enum_previews_from_directory_items(self, context)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        if self.trimsheet_previews in p_trimsheet_names:
            p_index = p_trimsheet_names.index(self.trimsheet_previews)
            if self.trimsheet_index != p_index:
                self.trimsheet_index = p_index


def get_trimsheet_previews(self):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = get_enum_previews(self)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        return self.trimsheet_index
    else:
        return -1


def set_trimsheet_previews(self, value):
    p_trimsheet_names = [p_trim.get_preview_name() for p_trim in self.trimsheet]
    p_previews = get_enum_previews(self)

    p_preview_names = [item[0] for item in p_previews]

    if p_preview_names == p_trimsheet_names:
        self.trimsheet_index = value
        update_areas_in_all_screens(bpy.context)


class ZuvImageProperties(bpy.types.PropertyGroup):
    trimsheet: bpy.props.CollectionProperty(name='Trimsheet', type=ZuvTrimsheetGroup)
    trimsheet_index: ZuvTrimsheetOwnerProps.trimsheet_index
    trimsheet_index_ui: ZuvTrimsheetOwnerProps.trimsheet_index_ui
    trimsheet_geometry_uuid: ZuvTrimsheetOwnerProps.trimsheet_geometry_uuid

    # image properties only
    trimsheet_previews: bpy.props.EnumProperty(
        name='Trimsheet Previews', items=enum_previews_from_directory_items,
        get=get_trimsheet_previews,
        set=set_trimsheet_previews,
        update=on_zenuv_trimsheet_previews_update)

    def trimsheet_mark_geometry_update(self):
        self.trimsheet_geometry_uuid = str(uuid.uuid4())

    world_scale: bpy.props.PointerProperty(name='World Scale', type=ZUV_WorldScaleProps)
