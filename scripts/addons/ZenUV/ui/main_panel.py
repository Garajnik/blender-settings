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

""" Zen UV Main Panel controls """
import bpy

from ZenUV.ico import icon_get
from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.generic import (
    ZUV_PANEL_CATEGORY, ZUV_REGION_TYPE,
    ZUV_SPACE_TYPE, ZenKeyEventSolver)
from ZenUV.prop.zuv_preferences import (
    draw_panels_enabler, get_prefs, get_addon_version)
from ZenUV.prop.common import uv_enblr, get_combo_panel_order
from ZenUV.ui.panel_draws import (
    draw_select,
    draw_copy_paste,
    draw_stack,
    draw_unwrap,
    draw_finished_section,
)

from ZenUV.ops.transform_sys.tr_ui import draw_transform_panel
from ZenUV.utils.clib.lib_init import StackSolver, get_zenlib_version, is_zenlib_present
from ZenUV.utils.blender_zen_utils import ZenPolls


class ZUV_PT_3DV_Transform(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_idname = "ZUV_PT_3DV_Transform"
    bl_label = ZuvLabels.PANEL_TRANSFORM_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_3DV_Transform')
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def get_icon(cls):
        return icon_get("pn_Transform")

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_VIEW_3D_panels.enable_pt_transform and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_transform_panel(self, context)


# TODO Must be removed?
class DATA_PT_Setup(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_label = "Setup"
    bl_parent_id = "ZUV_PT_Preferences"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "DATA_PT_Setup"
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text=ZuvLabels.PREF_TD_TEXTURE_SIZE_LABEL + ": ")
        row.prop(context.scene.zen_uv.td_props, 'td_im_size_presets', text="")
        if context.scene.zen_uv.td_props.td_im_size_presets == 'Custom':
            col = layout.column(align=True)
            col.prop(context.scene.zen_uv.td_props, 'TD_TextureSizeX', text="Custom Res X")
            col.prop(context.scene.zen_uv.td_props, 'TD_TextureSizeY', text="Custom Res Y")


class SYSTEM_PT_Finished(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_label = "Finished"
    bl_parent_id = "ZUV_PT_Unwrap"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "SYSTEM_PT_Finished"
    bl_options = {'DEFAULT_CLOSED'}

    # def draw_header(self, context):
    #     layout = self.layout
    #     row = layout.row(align=True)
    #     row.split()
    #     row.label(text="Finished")
    #     row.operator("uv.zenuv_tag_finished", icon='KEYFRAME_HLT', text="")
    #     row.operator("uv.zenuv_untag_finished", icon='KEYFRAME', text="")
    #     row.operator("uv.zenuv_islands_sorting", text="", icon='SORTSIZE')
    #     row.operator("uv.zenuv_select_finished", icon='RESTRICT_SELECT_OFF', text="")
    #     row.prop(context.scene.zen_display, "finished", toggle=True, icon='HIDE_OFF', text="")

    def draw(self, context):
        draw_finished_section(self, context)


class DATA_PT_Panels_Switch(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_label = "Panels"
    bl_parent_id = "ZUV_PT_Preferences"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "DATA_PT_Panels_Switch"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        draw_panels_enabler(context, layout, "VIEW_3D")

    @classmethod
    def combo_draw(cls, layout: bpy.types.UILayout, context: bpy.types.Context):
        draw_panels_enabler(context, layout, "VIEW_3D", is_combo=True)


def draw_display_panel(self, context: bpy.types.Context):
    ''' @Draw Display Panel '''
    addon_prefs = get_prefs()
    layout = self.layout
    box = layout.box()
    box.prop(addon_prefs, "pie_assist")
    box.prop(addon_prefs, "use_progress_bar")
    box = layout.box()
    box.prop(addon_prefs, "hops_uv_activate")
    if addon_prefs.hops_uv_activate:
        box.prop(addon_prefs, "hops_uv_context")
    box = layout.box()
    box.prop(addon_prefs, 'autoFitUV')
    box = layout.box()
    box.prop(addon_prefs, "show_ui_button", text="Sticky UV Editor Button")

    if context.area.type == 'VIEW_3D':
        if context.mode == 'EDIT_MESH':
            box = layout.box()
            box.prop(
                context.space_data.overlay,
                "show_edge_seams",
                text=ZuvLabels.B_PREF_SHOW_EDGE_SEAMS_LABEL)
            box.prop(
                context.space_data.overlay,
                "show_edge_sharp",
                text=ZuvLabels.B_PREF_SHOW_EDGE_SHARP_LABEL)
            box.prop(
                context.space_data.overlay,
                "show_edge_bevel_weight",
                text=ZuvLabels.B_PREF_SHOW_BEVEL_WEIGHTS_LABEL)
            box.prop(
                context.space_data.overlay,
                "show_edge_crease",
                text=ZuvLabels.B_PREF_SHOW_EDGE_CREASE_LABEL)


class DATA_PT_ZDisplay(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_label = "Display"
    bl_parent_id = "ZUV_PT_Preferences"
    bl_region_type = ZUV_REGION_TYPE
    bl_idname = "DATA_PT_ZDisplay"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        # layout = self.layout
        # layout.label(text="TEST TEXT")
        draw_display_panel(self, context)


class ZUV_PT_ZenCore(bpy.types.Panel):
    """ Internal Popover Zen UV Core """
    """ We suppose this class is used only when lib is not installed """
    bl_idname = "ZUV_PT_ZenCore"
    bl_label = ZuvLabels.PANEL_CLIB_LABEL
    bl_context = "mesh_edit"  # requires Valerii CHECK !
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        # addon_prefs = get_prefs()
        layout = self.layout

        col = layout.column(align=True)

        b_is_zenlib_present = is_zenlib_present()

        row = col.row(align=True)
        row.label(text=ZuvLabels.CLIB_NAME + (": not installed" if not b_is_zenlib_present else ": not registered"))

        row = col.row(align=True)
        s_label = ("Register " if b_is_zenlib_present else "Install ") + ZuvLabels.CLIB_NAME
        row.operator("view3d.zenuv_install_library", text=s_label)


class ZUV_PT_Help(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_Help"
    bl_label = ZuvLabels.PANEL_HELP_LABEL
    bl_context = ""
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Help')
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Help')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_VIEW_3D_panels.enable_pt_help and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode in {'EDIT_MESH', 'OBJECT'}

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit and Object Modes'

    def draw(self, context):
        layout = self.layout

        if context.active_object and not context.active_object.mode == 'EDIT':
            layout.label(text=ZuvLabels.PANEL_OBJECT_MODE_LABEL)
        col = layout.column(align=True)

        row = col.row(align=True)
        row.operator(
            "wm.url_open",
            text=ZuvLabels.PANEL_HELP_DOC_LABEL,
            icon="HELP"
        ).url = ZenPolls.doc_url
        row = col.row(align=True)
        row.operator(
            "wm.url_open",
            text=ZuvLabels.PANEL_HELP_DISCORD_LABEL,
            icon_value=icon_get(ZuvLabels.PANEL_HELP_DISCORD_ICO)
        ).url = ZuvLabels.PANEL_HELP_DISCORD_LINK
        try:
            row = col.row(align=True)
            row.label(text='Version: ' + get_addon_version())
        except Exception:
            print('Zen UV: No version found. There may be several versions installed. Try uninstalling everything and installing the latest version.')

        row = col.row(align=True)

        if not StackSolver():
            row.alert = True
            row.label(text='Core Library' + (": not installed" if not is_zenlib_present() else ": not registered"))
        else:
            result = get_zenlib_version()
            row.label(text='Core: ({}, {}, {})'.format(result[0], result[1], result[2]))
        row.alert = False
        row.operator("ops.zenuv_show_prefs", text="", icon="PREFERENCES").tabs = "MODULES"

        addon_prefs = get_prefs()
        box = layout.box()
        addon_prefs.demo.draw(box, context)


class ZUV_PT_UVL_Help(bpy.types.Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_idname = "ZUV_PT_UVL_Help"
    bl_label = ZuvLabels.PANEL_HELP_LABEL
    bl_context = ""
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Help')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_help and cls.combo_poll(context)

    get_icon = ZUV_PT_Help.get_icon

    combo_poll = ZUV_PT_Help.combo_poll

    poll_reason = ZUV_PT_Help.poll_reason

    draw = ZUV_PT_Help.draw


class ZUV_PT_Unwrap(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_Unwrap"
    bl_label = ZuvLabels.PANEL_UNWRAP_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Unwrap')

    @classmethod
    def get_icon(cls):
        return icon_get("pn_Unwrap")

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_VIEW_3D_panels.enable_pt_unwrap and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_unwrap(self, context)


class ZUV_PT_Select(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_Select"
    bl_label = ZuvLabels.PANEL_SELECT_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Select')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Select')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_VIEW_3D_panels.enable_pt_select and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_select(self, context)


class ZUV_PT_Preferences(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_Preferences"
    bl_label = ZuvLabels.PANEL_PREFERENCES_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Preferences')

    @classmethod
    def get_icon(cls):
        return icon_get("pn_Preferences")

    @classmethod
    def poll(cls, context):
        if not cls.combo_poll(context):
            return False

        addon_prefs = get_prefs()
        b_poll = addon_prefs.float_VIEW_3D_panels.enable_pt_preferences and cls.combo_poll(context)
        if not b_poll:
            b_is_any_float = any([
                (val.get('VIEW_3D') is not None and getattr(addon_prefs.float_VIEW_3D_panels, key, False))
                for key, val in uv_enblr.items()])
            if not b_is_any_float:
                b_is_any_dock = addon_prefs.dock_VIEW_3D_panels_enabled
                if not b_is_any_dock:
                    return True

        return b_poll

    @classmethod
    def combo_poll(cls, context):
        return context.mode in {'EDIT_MESH', 'OBJECT'}

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit and Object Modes'

    @classmethod
    def do_draw(cls, layout: bpy.types.UILayout, context: bpy.types.Context, is_combo=False):
        layout.operator(
            'ops.zenuv_show_prefs',
            icon_value=icon_get(ZuvLabels.ADDON_ICO),
            text="Zen UV Keymaps").tabs = "KEYMAP"

        if context.mode == 'EDIT_MESH':
            layout.operator("zenuv.reset_preferences")
            # layout = self.layout
            # row = layout.row(align=True)
            # row.label(text=ZuvLabels.PREF_GLOBAL_TEXTURE_SIZE + ": ")
            # row.prop(addon_prefs, 'td_im_size_presets', text="")
            # if addon_prefs.td_im_size_presets == 'Custom':
            #     col = layout.column(align=True)
            #     col.prop(addon_prefs, 'TD_TextureSizeX', text="Custom Res X")
            #     col.prop(addon_prefs, 'TD_TextureSizeY', text="Custom Res Y")
        elif context.mode == 'OBJECT':
            pass

    def draw(self, context):
        self.do_draw(self.layout, context, is_combo=False)

    @classmethod
    def combo_draw(cls, layout: bpy.types.UILayout, context: bpy.types.Context):
        cls.do_draw(layout, context, is_combo=True)


class ZUV_OT_resetPreferences(bpy.types.Operator):
    """ Reset Zen UV Preferences """
    bl_idname = "zenuv.reset_preferences"
    bl_label = ZuvLabels.RESET_LABEL
    bl_description = ZuvLabels.RESET_DESC
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        is_modifier_right = ZenKeyEventSolver(context, event, get_prefs()).solve()
        # event.alt
        if event.type == "LEFTMOUSE" and is_modifier_right:
            self.register_system_panel()
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=ZuvLabels.RESET_MES)
        layout.separator()

    def execute(self, context):

        addon_prefs = get_prefs()
        items = addon_prefs.__annotations__.keys()
        for pref in items:
            addon_prefs.property_unset(pref)

        # Reset Angle in Auto Seams Operator props moved to addon preferences.
        # Code below temporarily disabled
        # op = context.window_manager.operator_properties_last('uv.zenuv_auto_mark')
        # if op:
        #     op.angle = 30.03

        return {'FINISHED'}

    def register_system_panel(self):
        from bpy.utils import register_class, unregister_class
        if hasattr(bpy.types, "ZUV_PT_System"):
            unregister_class(bpy.types.ZUV_PT_System)
            unregister_class(bpy.types.ZUV_PT_System_UVL)
            print(" Zen UV: The 'System' panel is unregistered.")
        else:
            register_class(ZUV_PT_System)
            register_class(ZUV_PT_System_UVL)
            print(" Zen UV: The 'System' panel is registered.")

        # if hasattr(bpy.types, bpy.ops.uvpackeroperator.packbtn.idname()):
        from ZenUV.utils.tests.td_tests import ZUV_OT_UnitTestTexelDensity
        from ZenUV.utils.tests.td_tests import register as register_td_tests
        from ZenUV.utils.tests.td_tests import unregister as unregister_td_tests
        if hasattr(bpy.types, ZUV_OT_UnitTestTexelDensity.bl_idname):
            unregister_td_tests()
            print('Operators TD Tests UnRegistered')
        else:
            print('Operators TD Tests Registered')
            register_td_tests()


class ZUV_PT_Stack(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_Stack"
    bl_label = ZuvLabels.PANEL_STACK_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Stack')
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def get_icon(cls):
        return icon_get('pn_Stack')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_VIEW_3D_panels.enable_pt_stack and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context: bpy.types.Context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_stack(self, context)
        draw_copy_paste(self, context)
        # draw_simple_stack(self, context)


class ZUV_PT_System(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_System"
    bl_label = "System"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        from ZenUV.utils.tests.td_tests import (
            ZUV_OT_DevTestTexelDensity,
            ZUV_OT_UnitTestTexelDensity,
            ZUV_OT_TestPropertiesTexelDensity
        )
        _lt = self.layout
        _lt.operator('zenuv_test.test_checking')
        _lt.operator("zenuv_test.addon_test")
        _lt.operator("zenuv.check_sel_in_sync_states")
        _lt.operator("uv.zenuv_debug")
        _lt.operator("view3d.zenuv_check_library")

        from ZenUV.zen_checker.check_utils import draw_checker_display_items, t_draw_system_modes
        draw_checker_display_items(_lt, context, t_draw_system_modes)

        _lt.operator("uv.zenuv_show_sim_index")

        _lt.label(text='TD Section')
        box = _lt.box()
        col = box.column(align=True)
        col.operator(ZUV_OT_UnitTestTexelDensity.bl_idname)
        col.operator(ZUV_OT_DevTestTexelDensity.bl_idname)
        col.operator(ZUV_OT_TestPropertiesTexelDensity.bl_idname)

        # _lt.prop(context.scene.zen_display, "tagged", toggle=True, icon='HIDE_OFF')


class ZUV_PT_System_UVL(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_System_UVL"
    bl_label = "System"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator("zenuv_test.addon_test")
        layout.operator("zenuv.check_sel_in_sync_states")
        layout.operator("uv.zenuv_debug")
        layout.operator("view3d.zenuv_check_library")

        from ZenUV.zen_checker.check_utils import draw_checker_display_items, t_draw_system_modes
        draw_checker_display_items(layout, context, t_draw_system_modes)

        layout.operator("uv.zenuv_show_sim_index")
        # layout.prop(context.scene.zen_display, "tagged", toggle=True, icon='HIDE_OFF')


main_panel_parented_panels = [
    SYSTEM_PT_Finished,
    DATA_PT_Panels_Switch,
    DATA_PT_ZDisplay,
]

if __name__ == '__main__':
    pass
