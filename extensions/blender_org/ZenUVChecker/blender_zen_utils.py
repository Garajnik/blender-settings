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

# Copyright 2021, Alex Zhornyak

""" Zen Blender Utils """

import bpy
import uuid

app_version = bpy.app.version


class ZenPolls:
    version_since_3_2_0 = app_version >= (3, 2, 0)

    version_lower_3_4_0 = app_version < (3, 4, 0)

    version_lower_3_5_0 = app_version < (3, 5, 0)
    version_equal_3_6_0 = app_version == (3, 6, 0)
    version_greater_3_6_0 = app_version > (3, 6, 0)

    # GPU unique shaders names, operators only through 'temp_override'
    version_since_4_0_0 = app_version >= (4, 0, 0)

    # Will be taken from bl_info['doc_url'] !!!
    doc_url = ''

    # Will be taken from 'ZenMastersTeam/Zen-UV/main/README.md'
    new_addon_version = None

    SESSION_UUID = None

    @classmethod
    def register_session(cls):
        cls.SESSION_UUID = str(uuid.uuid4())

    @classmethod
    def unregister_session(cls):
        cls.SESSION_UUID = None
