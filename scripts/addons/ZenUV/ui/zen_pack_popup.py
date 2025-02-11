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

import bpy
from ZenUV.ui.labels import ZuvLabels


class ZUV_MT_ZenPack_Uvp_Popup(bpy.types.Menu):
    bl_label = "Zen Unwrap"
    bl_idname = "ZUV_MT_ZenPack_Uvp_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout.label(text="Nothing is produced.")
        layout.label(text="It looks like UVPackmaster addon")
        layout.label(text="is not installed on your system.")
        layout.separator()

        layout.operator("wm.url_open",
                        text="Buy UVPackmaster addon",
                        icon="HELP").url = 'https://uvpackmaster.com/'

        layout.separator()
        row = layout.row(align=True)
        row.label(text="Or you can change Pack Engine:")
        row = layout.row(align=True)
        layout.prop(addon_prefs, "packEngine", text="")


class ZUV_MT_ZenPack_Uvpacker_Popup(bpy.types.Menu):
    bl_label = "Zen Unwrap"
    bl_idname = "ZUV_MT_ZenPack_Uvpacker_Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences
        layout.label(text="Nothing is produced.")
        layout.label(text="It looks like UV-Packer addon")
        layout.label(text="is not installed on your system.")
        layout.separator()

        layout.operator("wm.url_open",
                        text="Get UV-Packer addon",
                        icon="HELP").url = "https://www.uv-packer.com/blender/"

        layout.separator()
        row = layout.row(align=True)
        row.label(text="Or you can change Pack Engine:")
        row = layout.row(align=True)
        layout.prop(addon_prefs, "packEngine", text="")


class ZUV_MT_ZenWarningV36Popup(bpy.types.Menu):
    bl_label = "Zen Pack"
    bl_idname = "ZUV_MT_ZenWarningV36Popup"
    bl_icon = "KEYTYPE_EXTREME_VEC"

    def draw(self, context):
        layout = self.layout
        # addon_prefs = context.preferences.addons[ZuvLabels.ADDON_NAME].preferences

        layout.label(text="In Blender v3.6.0, the Blender Pack Engine")
        layout.label(text="cannot be used because the engine has become modal.")
        layout.label(text="Use the Pack operator as a standalone tool")
        layout.label(text="or install Blender v3.6.1")

        layout.separator()

        layout.operator("wm.url_open",
                        text="Download Blender",
                        icon="HELP").url = 'https://www.blender.org/download/'


classes = [
    ZUV_MT_ZenPack_Uvp_Popup,
    ZUV_MT_ZenPack_Uvpacker_Popup,
    ZUV_MT_ZenWarningV36Popup
]


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    pass
