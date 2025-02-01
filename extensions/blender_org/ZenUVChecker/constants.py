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

import bpy

ADDON_ID = "ZenUVChecker"

addon: bpy.types.Addon
for addon in bpy.context.preferences.addons:
    t_parts = addon.module.split(".")
    if ADDON_ID in t_parts:
        ADDON_NAME = addon.module
        break

ADDON_SHORT = 'zen_tex_chkr'

ZEN_IMAGE_NODE_NAME = "ZenUV_Texture_node"
ZEN_IMAGE_NAME = "zen-checker@4x.png"
ZEN_GENERATED_IMAGE_NAME = "BlenderChecker"
ZEN_GLOBAL_OVERRIDER_NAME = "Zen UV Checker"
ZEN_GLOBAL_OVERRIDER_NAME_OLD = "ZenUV_Checker"
ZEN_OVERRIDER_NAME = "ZenUV_Override"
ZEN_GENERIC_MAT_NAME = "ZenUV_Generic_Material"
ZEN_NODE_COLOR = (0.701, 0.017, 0.009)
ZEN_TILER_NODE_NAME = "ZenUV_Tiler_node"
ZEN_OFFSETTER_NODE_NAME = "ZenUV_Offsetter_node"


MES_NO_INP_CHANNELS = 'Zen Checker node group has no input channels. Need to reset the Checker'
MES_NO_OUT_CHANNELS = 'Zen Checker node group has no output channels. Need to reset the Checker'
