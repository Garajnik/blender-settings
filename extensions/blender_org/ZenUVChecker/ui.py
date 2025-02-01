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

""" Zen Checker Main Panel """

import bpy
import addon_utils

from .constants import ADDON_SHORT


def zen_message(context, message="", title="Zen UV Info", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    context.window_manager.popup_menu(draw, title=title, icon=icon)


class ZMeshButtonsPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    # bl_context = "data"

    @classmethod
    def poll(cls, context):
        engine = context.engine
        if context.active_object:
            return context.active_object.type == "MESH" and (engine in cls.COMPAT_ENGINES)


class ZTCHK_UL_uvmaps(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        # assert(isinstance(item, (bpy.types.MeshTexturePolyLayer, bpy.types.MeshLoopColorLayer)))
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='GROUP_UVS')
            icon = 'RESTRICT_RENDER_OFF' if item.active_render else 'RESTRICT_RENDER_ON'
            layout.prop(item, "active_render", text="", icon=icon, emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class ZTCHK_PT_UV_Maps(ZMeshButtonsPanel, bpy.types.Panel):

    bl_category = "Zen UV Checker"
    bl_idname = "ZTCHK_PT_UV_Maps"
    bl_label = "UV Maps"
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = ""

    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    def draw(self, context):
        layout = self.layout

        me = context.object.data

        row = layout.row()
        col = row.column()

        col.template_list(
            "ZTCHK_UL_uvmaps",
            "uvmaps",
            me,
            "uv_layers",
            me.uv_layers,
            "active_index",
            rows=2)

        col = row.column(align=True)
        col.operator("mesh.uv_texture_add", icon='ADD', text="")
        col.operator("mesh.uv_texture_remove", icon='REMOVE', text="")


def draw_filtration_sys(addon_prefs, layout):
    col = layout.column(align=True)
    row = col.row(align=True)
    col = row.column(align=True)
    row.prop(addon_prefs, "SizesX", text="", index=0)
    col = row.column(align=True)
    if addon_prefs.lock_axes:
        lock_icon = "LOCKED"
    else:
        lock_icon = "UNLOCKED"
    col.prop(addon_prefs, "lock_axes", icon=lock_icon, icon_only=True)
    col = row.column(align=True)
    col.enabled = not addon_prefs.lock_axes
    col.prop(addon_prefs, "SizesY", text="", index=0)
    row.prop(addon_prefs, "chk_orient_filter", icon="EVENT_O", icon_only=True)


def draw_checker_panel_3D(self, context: bpy.types.Context):
    from .preferences import get_prefs, get_scene_props
    from . import checker
    addon_prefs = get_prefs()
    addon_scene_props = get_scene_props(context)
    layout = self.layout  # type: bpy.types.UILayout

    col = layout.column(align=True)
    row = col.row(align=True)
    checker.ZTCHK_OT_CheckerToggle.draw_toggled(row, context)
    row.popover(panel=ZTCHK_PT_Popover.bl_idname, text="", icon="PREFERENCES")
    col.operator(checker.ZTCHK_OT_Remove.bl_idname)  # "view3d.zenuv_checker_remove")

    # Filtration System
    if addon_prefs.chk_rez_filter:
        draw_filtration_sys(addon_prefs, layout)

    row = layout.row(align=True)

    row.prop(addon_scene_props, "tex_checker_interpolation", icon_only=True, icon="NODE_TEXTURE")
    row.prop(addon_prefs, "ZenCheckerImages", index=0)
    row.prop(addon_prefs, "chk_rez_filter", icon="FILTER", icon_only=True)
    box = layout.box()
    b_is_active = context.area is not None and context.area.type == 'VIEW_3D' and len(context.area.spaces) and context.area.spaces[0].shading.type in {'RENDERED', 'MATERIAL'}
    box.enabled = b_is_active
    if not b_is_active:
        col = box.column(align=True)
        col.label(text='Available in Viewport Shading:')
        col.separator()
        col.label(text='Material Preview', icon='MATERIAL')
        col.label(text='Rendered', icon='SHADING_RENDERED')

    box.prop(addon_scene_props, "tex_checker_tiling")
    box.prop(addon_scene_props, "tex_checker_offset")






class ZTCHK_PT_Checker(bpy.types.Panel):
    bl_idname = "ZTCHK_PT_Checker"
    bl_label = "Zen UV Checker"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "Zen UV Checker"

    def draw(self, context):
        draw_checker_panel_3D(self, context)


class ZTCHK_PT_Popover(bpy.types.Panel):
    """ Zen Checker Properties Popover """
    bl_idname = "ZTCHK_PT_Popover"
    bl_label = "Zen Checker Properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        from .preferences import get_prefs
        from . import files
        from . import checker
        addon_prefs = get_prefs()
        layout = self.layout
        layout.label(text="Checker Library folder:")

        col = layout.column(align=True)
        row = col.row()
        col = row.column(align=True)
        col.prop(addon_prefs, "assetspath", text="")
        col = row.column(align=True)
        col.operator(files.ZTCHK_OT_ResetPath.bl_idname, text="Reset Folder")

        layout.operator(files.ZTCHK_OT_AppendCheckerFile.bl_idname, icon="FILEBROWSER")
        layout.operator(files.ZTCHK_OT_CollectImages.bl_idname, icon="FILE_REFRESH")
        layout.prop(addon_prefs, "dynamic_update", )
        layout.operator(checker.ZTCHK_OT_OpenEditor.bl_idname)
        layout.operator(checker.ZTCHK_OT_Reset.bl_idname)


class ZTCHK_PT_Help(bpy.types.Panel):
    bl_idname = "ZTCHK_PT_Help"
    bl_label = "Help"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Zen UV Checker"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.operator(ZTCHK_OT_Keymaps.bl_idname)

        layout.operator(
            "wm.url_open",
            text="Documentation",
            icon="HELP"
        ).url = "https://zenmastersteam.github.io/Zen-UV/latest/checker/"

        try:
            # row = col.row(align=True)
            layout.label(text='Version: ' + str([addon.bl_info.get('version', (-1, -1, -1)) for addon in addon_utils.modules() if addon.bl_info['name'] == "Zen UV Checker"][0]))
        except Exception as e:
            print(e)
            print('Zen UV Checker: No version found. There may be several versions installed. Try uninstalling everything and installing the latest version.')


class ZTCHK_OT_Keymaps(bpy.types.Operator):
    bl_idname = f"ops.{ADDON_SHORT}_keymaps"
    bl_label = "Checker Keymaps"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set Shortcuts for Zen UV Checker"

    def execute(self, context):
        context.preferences.active_section = "KEYMAP"
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        context.space_data.filter_type = "NAME"
        context.space_data.filter_text = ADDON_SHORT

        return {'FINISHED'}


classes = (
    ZTCHK_PT_Checker,
    ZTCHK_UL_uvmaps,
    ZTCHK_PT_Popover,
    ZTCHK_PT_UV_Maps,
    ZTCHK_PT_Help,
    ZTCHK_OT_Keymaps
)


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)


if __name__ == '__main__':
    pass
