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

# Copyright 2023, Valeriy Yatsenko

""" Zen Texel Density UI """

import bpy
from ZenUV.utils.generic import (
    ZUV_SPACE_TYPE,
    ZUV_REGION_TYPE,
    ZUV_PANEL_CATEGORY,
    ZUV_CONTEXT
    )
from ZenUV.ui.labels import ZuvLabels
from ZenUV.ico import icon_get
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.prop.common import get_combo_panel_order

from ZenUV.ops.texel_density.td_utils import TdUtils
from ZenUV.ops.texel_density.td_presets import ZUV_PT_ZenTDPresets, ZUV_PT_UVL_ZenTDPresets

from .td_tools import (
    ZUV_OT_TD_Calculator,
    ZUV_OT_Bake_TD_to_VC,
    ZUV_OT_Clear_Baked_TD
)

from .td_props import TdProps
from .world_scale import (
    register_world_scale,
    unregister_world_scale,
    ZUV_PT_3DV_SubWorldSize,
    ZUV_PT_UVL_SubWorldSize)


class ZUV_PT_Texel_Density(bpy.types.Panel):
    bl_space_type = ZUV_SPACE_TYPE
    bl_idname = "ZUV_PT_Texel_Density"
    bl_label = ZuvLabels.PANEL_TEXEL_DENSITY_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('VIEW_3D', 'ZUV_PT_Texel_Density')
    # bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def get_icon(cls):
        return icon_get('pn_TD')

    @classmethod
    def poll(cls, context: bpy.types.Context):
        addon_prefs = get_prefs()
        return addon_prefs.float_VIEW_3D_panels.enable_pt_texel_density and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context: bpy.types.Context):
        return context.mode in {'EDIT_MESH', 'OBJECT'}

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit and Object Modes'

    def draw(self, context: bpy.types.Context):
        draw_texel_density(self, context)


class ZUV_PT_UVL_Texel_Density(bpy.types.Panel):
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_UVL_Texel_Density"
    bl_label = ZuvLabels.PANEL_TEXEL_DENSITY_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_order = get_combo_panel_order('UV', 'ZUV_PT_UVL_Texel_Density')

    @classmethod
    def get_icon(cls):
        return icon_get('pn_TD')

    @classmethod
    def poll(cls, context):
        addon_prefs = get_prefs()
        return addon_prefs.float_UV_panels.enable_pt_texel_density and cls.combo_poll(context)

    @classmethod
    def combo_poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_texel_density(self, context)


def draw_texel_density(self, context: bpy.types.Context):
    ''' @Draw Texel Density '''

    layout: bpy.types.UILayout = self.layout

    b_is_edit_mesh = context.mode == 'EDIT_MESH'

    col = layout.column(align=False)

    td_props = context.scene.zen_uv.td_props

    draw_td_panel(context, col, td_props)

    if td_props.td_use_pivot:
        draw_enum_pivot_selector(context, col, pivot_system='TD')

    draw_td_ranges(context, col)

    box = col.box()
    box.operator(ZUV_OT_TD_Calculator.bl_idname, text='Calculate TD', icon='DESKTOP')

    if b_is_edit_mesh:
        box = col.box()
        col = box.column(align=False)
        row = col.row(align=True)
        from ZenUV.zen_checker.check_utils import draw_checker_display_items, DisplayItem
        draw_checker_display_items(
            row, context,
            {'TEXEL_DENSITY': DisplayItem({'EDIT_MESH'}, {'UV', '3D'}, '', 'Display TD')})

        row = col.row(align=True)
        row.prop(context.scene.zen_uv.td_draw_props, 'influence', text='')
        row.separator()
        row.prop(context.scene.zen_uv.td_draw_props, 'display_method', text='')


def draw_td_panel(context: bpy.types.Context, layout: bpy.types.UILayout, td_props):
    b_is_edit_mode = context.mode == 'EDIT_MESH'

    col = layout.column(align=True)
    row = col.row(align=True)
    r1 = row.row(align=True)
    r1.enabled = b_is_edit_mode
    draw_select_operator(context, r1)
    r2 = row.row(align=True)
    r2.prop(td_props, 'prp_current_td', text="")
    r2.prop(td_props, 'td_unit', text='')

    row.popover(panel="TD_PT_Properties", text="", icon="PREFERENCES")

    p_td_props: TdProps = context.scene.zen_uv.td_props

    col = layout.column(align=True)
    row = col.row(align=True)
    if b_is_edit_mode:
        row.operator('uv.zenuv_get_texel_density')
        op = row.operator('uv.zenuv_set_texel_density')
        op.td_value = p_td_props.prp_current_td
        op.island_pivot = td_props.td_set_pivot if td_props.td_use_pivot is True else 'cen'
        op.td_set_mode = td_props.td_set_mode
    else:
        row.operator('uv.zenuv_get_texel_density_obj')

        if p_td_props.td_im_size_presets == 'Custom':
            image_size = (
                p_td_props.TD_TextureSizeX,
                p_td_props.TD_TextureSizeY)
        else:
            image_size = (
                p_td_props.SZ_TextureSizeX,
                p_td_props.TD_TextureSizeY)

        gtd = row.operator("uv.zenuv_set_texel_density_obj")
        gtd.td = p_td_props.prp_current_td
        gtd.u = image_size[0]
        gtd.v = image_size[1]
        gtd.units = p_td_props.td_unit
        gtd.mode = p_td_props.td_set_mode

    row = col.row(align=True)
    row.prop(td_props, "td_set_mode", text="")
    row.prop(td_props, 'td_use_pivot', icon='EVENT_P', text='')

    box = col.box()
    # box.use_property_split = True
    draw_td_image_size(context, box)


def draw_enum_pivot_selector(context: bpy.types.Context, layout: bpy.types.UILayout, pivot_system: str):
    from ZenUV.utils.bounding_box import DirMatrixStr
    from ZenUV.ico import icon_get
    if pivot_system == 'TD':
        prop = 'td_set_pivot'
    elif pivot_system == 'SZ':
        prop = 'sz_set_pivot'
    else:
        layout.label(text='Pivot system error')

    main_row = layout.row(align=False)
    main_row.alignment = 'CENTER'
    main_col = main_row.column(align=True)

    rows = [main_col.row(align=True), main_col.row(align=True), main_col.row(align=True)]
    grid = [
        rows[0], rows[0], rows[0],
        rows[1], rows[1], rows[1],
        rows[2], rows[2], rows[2]]

    for p, i, row in zip(DirMatrixStr.all_directions, DirMatrixStr.all_directions_icons, grid):
        b_is_enabled = getattr(context.scene.zen_uv.td_props, prop) == p
        op = row.operator('wm.context_set_enum', text='', depress=b_is_enabled, icon_value=icon_get(i))
        op.data_path = 'scene.zen_uv.td_props.' + prop
        op.value = p


def draw_td_ranges(context: bpy.types.Context, layout: bpy.types.UILayout):

    from .td_ops import ZUV_OT_GetTdRange
    from . td_display_utils import TdDisplayLimits

    b_is_edit_mesh = context.mode == 'EDIT_MESH'

    box = layout.box()
    is_td_uniform = TdDisplayLimits.lower_limit == TdDisplayLimits.upper_limit
    label = 'TD is uniform' if is_td_uniform else 'TD range'
    row = box.row()
    r1 = row.row(align=True)
    r1.label(text=f'{label}')
    # TdDrawUI.draw_current_td_limits(context, box)
    r1.prop(context.scene.zen_uv.td_props, 'td_range_mode', text='')
    r2 = row.row(align=True)
    r2.alignment = 'RIGHT'
    r2.operator(ZUV_OT_GetTdRange.bl_idname, text='', icon="FILE_REFRESH")

    row = box.row(align=True)
    row.enabled = b_is_edit_mesh
    s_mode = bpy.types.UILayout.enum_item_name(context.scene.zen_uv.td_props, "td_range_mode", context.scene.zen_uv.td_props.td_range_mode) + '. Press for select'

    t_values = {
        'Minimal': TdDisplayLimits.lower_limit,
        'Middle': TdDisplayLimits.middle,
        'Maximal': TdDisplayLimits.upper_limit
    }

    for k, v in t_values.items():
        draw_select_operator(
            context, row, value_as_button=True,
            value=v, desc=f'{k} TD value of the {s_mode}')


def draw_select_operator(context, layout: bpy.types.UILayout, value_as_button: bool = False, value: float = 0.0, inbox=False, desc=None):
    from ZenUV.ops.texel_density.td_ops import ZUV_OT_SelectByTd
    if value_as_button:
        if inbox:
            _lt = layout.box()
        else:
            _lt = layout

        r2 = _lt.row(align=True)
        op_sel_by_td = r2.operator(
            ZUV_OT_SelectByTd.bl_idname,
            text=f"{value}",
            # icon=icon,
            # emboss=False,
            # depress=True
            )
        p_td = value
    else:
        op_sel_by_td = layout.operator(
            ZUV_OT_SelectByTd.bl_idname,
            text="",
            icon="RESTRICT_SELECT_OFF"
            )
        p_td = context.scene.zen_uv.td_props.prp_current_td
    op_sel_by_td.selection_mode = 'TRESHOLD'
    op_sel_by_td.texel_density = p_td
    op_sel_by_td.treshold = 0.01
    op_sel_by_td.sel_underrated = False
    op_sel_by_td.sel_overrated = False
    op_sel_by_td.clear_selection = True

    if desc is not None:
        op_sel_by_td.desc = desc


def draw_td_global_preset(context, layout: bpy.types.UILayout):

    box = layout.box()
    td_global_preset = round(context.scene.zen_uv.td_props.td_global_preset, 2)

    row = box.row(align=True)
    r1 = row.row(align=True)
    r1.label(text="Global TD Preset:")

    r2 = row.row(align=True)
    r2.alignment = 'RIGHT'
    draw_select_operator(
        context,
        r1,
        value_as_button=True,
        value=td_global_preset,
        desc='Desired averaged Texel Density value for project. Press for select')
    r2.label(text=TdUtils.get_current_units_string(context))

    r2.separator()
    r2.popover(panel="TD_PT_Project_Properties", text="", icon="PREFERENCES")


def draw_td_tools(self, context: bpy.types.Context, layout: bpy.types.UILayout):
    from .td_ops import ZUV_OT_SelectByTd

    col = layout.column(align=True)
    col.operator(ZUV_OT_SelectByTd.bl_idname)

    col.separator()
    row = col.row(align=True)
    row.operator(ZUV_OT_Bake_TD_to_VC.bl_idname, text='Bake TD to VC')
    row.operator(ZUV_OT_Clear_Baked_TD.bl_idname, text='Clear VC').map_type = "ALL"


class ZUV_PT_TdTools(bpy.types.Panel):
    """  Zen TD Tools Panel """
    bl_label = "Tools"
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Texel_Density"
    bl_idname = "ZUV_PT_TdTools"

    def draw(self, context):
        draw_td_tools(self, context, self.layout)


class ZUV_PT_UVL_TdTools(bpy.types.Panel):
    """  Zen TD Tools Panel """
    bl_label = "Tools"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_UVL_Texel_Density"
    bl_idname = "ZUV_PT_UVL_TdTools"

    def draw(self, context):
        draw_td_tools(self, context, self.layout)


class ZUV_PT_TdDraw(bpy.types.Panel):
    """  Zen TD Draw Panel """
    bl_label = "Advanced Display Settings"
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Texel_Density"
    bl_idname = "ZUV_PT_TdDraw"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        if context.mode != 'EDIT_MESH':
            return 'Available in Edit Mesh Mode'
        return ''

    def draw(self, context: bpy.types.Context):
        layout: bpy.types.UILayout = self.layout
        context.scene.zen_uv.td_draw_props.draw(context, layout)


class ZUV_PT_UVL_TdDraw(bpy.types.Panel):
    """  Zen TD Draw Panel """
    bl_label = ZUV_PT_TdDraw.bl_label
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_UVL_Texel_Density"
    bl_idname = "ZUV_PT_UVL_TdDraw"

    poll = ZUV_PT_TdDraw.poll

    poll_reason = ZUV_PT_TdDraw.poll_reason

    def draw(self, context):
        context.scene.zen_uv.td_draw_props.draw(context, self.layout)


def draw_td_image_size(context, layout):
    row = layout.row(align=True)
    row.label(text='Texture Size:')
    row.prop(context.scene.zen_uv.td_props, 'td_im_size_presets', text='')
    if context.scene.zen_uv.td_props.td_im_size_presets == 'Custom':
        col = layout.column(align=True)
        col.prop(context.scene.zen_uv.td_props, 'TD_TextureSizeX', text="Custom Res X")
        col.prop(context.scene.zen_uv.td_props, 'TD_TextureSizeY', text="Custom Res Y")


class ZUV_PT_TdSize(bpy.types.Panel):
    bl_label = "Island Size"
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Texel_Density"
    bl_idname = "ZUV_PT_TdSize"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        if context.mode != 'EDIT_MESH':
            return 'Available in Edit Mesh Mode'
        return ''

    def draw(self, context):
        draw_sizes_panel_mode(self, context, self.layout)


class ZUV_PT_UVL_TdSize(bpy.types.Panel):
    bl_label = ZUV_PT_TdSize.bl_label
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_UVL_Texel_Density"
    bl_idname = "ZUV_PT_UVL_TdSize"

    poll = ZUV_PT_TdSize.poll

    poll_reason = ZUV_PT_TdSize.poll_reason

    def draw(self, context):
        draw_sizes_panel_mode(self, context, self.layout)


def draw_sizes_panel_mode(self, context: bpy.types.Context, layout: bpy.types.UILayout):

    from .td_ops import ZUV_OT_GetIslandSize, ZUV_OT_SetIslandSize, ZUV_OT_SelectBySize
    from .td_props import ZUV_TdProperties

    td_props: ZUV_TdProperties = context.scene.zen_uv.td_props

    row = layout.row(align=True)
    col = row.column(align=True)

    r_x = col.row(align=True)
    r_x.active = td_props.sz_active_x
    r_x.prop(td_props, 'sz_current_size', index=0, text='')
    r_x.prop(td_props, 'sz_active_x', text='', toggle=1, icon='EVENT_X')

    r_y = col.row(align=True)
    r_y.active = td_props.sz_active_y
    r_y.prop(td_props, 'sz_current_size', index=1, text='')
    r_y.prop(td_props, 'sz_active_y', text='', toggle=1, icon='EVENT_Y')

    r_2 = row.row(align=True)
    r_2.prop(td_props, 'sz_units', text='')

    op = r_2.operator(ZUV_OT_SelectBySize.bl_idname, text='', icon="RESTRICT_SELECT_OFF")
    op.selection_mode = 'TRESHOLD'
    if op.units != td_props.sz_units:
        op.units = td_props.sz_units

    if td_props.sz_active_x is True and td_props.sz_active_y is False:
        op.size = td_props.sz_current_size[0]
    elif td_props.sz_active_x is False and td_props.sz_active_y is True:
        op.size = td_props.sz_current_size[1]
    else:
        op.size = td_props.sz_current_size[0]

    if op.active_x != td_props.sz_active_x:
        op.active_x = td_props.sz_active_x
    if op.active_y != td_props.sz_active_y:
        op.active_y = td_props.sz_active_y

    col = layout.column(align=True)
    row = col.row(align=True)
    row.operator(ZUV_OT_GetIslandSize.bl_idname, text='Get')

    op = row.operator(ZUV_OT_SetIslandSize.bl_idname, text='Set')
    sz_props = context.scene.zen_uv.td_props
    if op.units != sz_props.sz_units:
        op.units = sz_props.sz_units
    if op.size != sz_props.sz_current_size:
        op.size = sz_props.sz_current_size
    if op.active_x != sz_props.sz_active_x:
        op.active_x = sz_props.sz_active_x
    if op.active_y != sz_props.sz_active_y:
        op.active_y = sz_props.sz_active_y

    row = col.row(align=True)
    row.prop(td_props, "sz_set_mode", text="")
    row.prop(td_props, 'sz_use_pivot', icon='EVENT_P', text='')

    if td_props.sz_use_pivot:
        draw_enum_pivot_selector(context, layout, pivot_system='SZ')

    box = layout.box()
    row = box.row(align=True)
    row.label(text='Texture Size:')
    row.prop(td_props, 'sz_im_size_presets', text='')
    if td_props.sz_im_size_presets == 'Custom':
        col = box.column(align=True)
        col.prop(td_props, 'SZ_TextureSizeX')
        col.prop(td_props, 'SZ_TextureSizeY')


class TD_PT_Project_Properties(bpy.types.Panel):
    """ Internal Popover Zen UV Texel Density Properties"""
    bl_idname = "TD_PT_Project_Properties"
    bl_label = "Texel Checker Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Project TD: ")
        row.prop(context.scene.zen_uv.td_props, "td_global_preset", text="")
        # layout.prop(context.scene.zen_uv.td_props, "td_calc_precision")


class TD_PT_Properties(bpy.types.Panel):
    bl_idname = "TD_PT_Properties"
    bl_label = "Texel Density Properties"
    bl_context = "mesh_edit"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.zen_uv.td_props, "td_calc_precision")


td_ui_classes = [
    ZUV_PT_Texel_Density,
    ZUV_PT_UVL_Texel_Density,

    TD_PT_Project_Properties,
    TD_PT_Properties
]

# Order is important
td_parented_panels = [
    ZUV_PT_TdDraw,
    ZUV_PT_UVL_TdDraw,
    ZUV_PT_ZenTDPresets,
    ZUV_PT_UVL_ZenTDPresets,

    ZUV_PT_TdSize,
    ZUV_PT_UVL_TdSize,
    ZUV_PT_3DV_SubWorldSize,
    ZUV_PT_UVL_SubWorldSize,

    ZUV_PT_TdTools,
    ZUV_PT_UVL_TdTools
]


def register():
    for cl in td_ui_classes:
        bpy.utils.register_class(cl)

    register_world_scale()


def unregister():
    unregister_world_scale()

    for cl in reversed(td_ui_classes):
        bpy.utils.unregister_class(cl)
