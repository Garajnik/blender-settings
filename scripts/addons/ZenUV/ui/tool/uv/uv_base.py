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

# Copyright 2023, Alex Zhornyak, Valeriy Yatsenko

import bpy

from mathutils import Vector, Matrix
from timeit import default_timer as timer
import numpy as np
from functools import partial

from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetGroup, TrimColorSettings
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.ui.gizmo_draw import LITERAL_ZENUV_GENERAL_UPDATE
from ZenUV.utils.constants import UV_AREA_BBOX
from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens, ZenPolls, rgetattr
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils.vlog import Log
from ZenUV.utils.inject import is_modal_procedure
from ZenUV.ops.event_service import get_blender_event


class ZuvUVGizmoBase():

    tool_mode = None

    pivot_prop = ''

    CAGE_DEFAULT_COLOR = (1, 0, 0)

    CURSOR_UNDEFINED = (-10000, -10000)

    def _setup_dragged(self, context: bpy.types.Context):
        pass

    def _setup_dragged_position(self, context: bpy.types.Context):
        pass

    def _reset_dragged(self, context: bpy.types.Context):
        self.setup_position(context)

    def _drag_completed(self, context: bpy.types.Context):
        p_scene = context.scene
        if 'RESIZE' == p_scene.zen_uv.ui.uv_tool.mode:
            p_trim = ZuvTrimsheetUtils.getActiveTrim(context)
            if p_trim:
                def update_trim():
                    p_trim.geometry_uuid_update(context)
                    ZuvTrimsheetUtils.fix_undo()
                    bpy.ops.ed.undo_push(message='Resize Trim')
                bpy.app.timers.register(update_trim)
        self._reset_dragged(context)

    def _check_and_set_drag_completed(self):
        b_drag_completed = False

        for k, v in self.gizmo_drag.items():
            if v != k.is_modal:
                self.gizmo_drag[k] = k.is_modal
                if not k.is_modal:
                    b_drag_completed = True
                else:
                    # some gizmo are still in dragging mode, quit
                    b_drag_completed = False
                    break

        return b_drag_completed

    @classmethod
    def getUVSelectedCenter(cls, ctx_override: dict) -> Vector:
        space = ctx_override['space_data']
        was_cursor = Vector(space.cursor_location)
        space.cursor_location = cls.CURSOR_UNDEFINED
        if ZenPolls.version_since_3_2_0:
            with bpy.context.temp_override(**ctx_override):
                if bpy.ops.uv.snap_cursor.poll():
                    bpy.ops.uv.snap_cursor(target='SELECTED')
        else:
            bpy.ops.uv.snap_cursor(ctx_override, target='SELECTED')
        new_cursor = Vector(space.cursor_location)
        space.cursor_location = was_cursor

        return new_cursor

    @classmethod
    def poll_edit_mesh_selected(cls, context: bpy.types.Context):
        return (
            context.mode == 'EDIT_MESH' and
            any(
                sum(p_obj.data.count_selected_items())
                for p_obj in context.objects_in_mode_unique_data if p_obj.type == 'MESH'
            )
        )

    @classmethod
    def is_workspace_tool_active(cls, context: bpy.types.Context):
        _id = getattr(context.workspace.tools.from_space_image_mode('UV', create=False), 'idname', None)
        return isinstance(_id, str) and _id == 'zenuv.uv_tool'

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if cls.is_workspace_tool_active(context):
            p_scene = context.scene
            if p_scene.zen_uv.ui.uv_tool.mode in cls.tool_mode:
                return True
        return False

    def is_uv_selected(self):
        return self.uv_selection_center[:] != self.CURSOR_UNDEFINED

    def is_general_update_valid(self):
        return self.general_update == bpy.app.driver_namespace.get(LITERAL_ZENUV_GENERAL_UPDATE, '')

    def enqueue_gizmo_check(self, context: bpy.types.Context):
        if not self.uv_center_detection_started and not self.are_gizmos_modal() and not is_modal_procedure(context):
            self.uv_center_detection_started = True
            bpy.app.timers.register(partial(self.zenuv_internal_gizmo_uv_check, context.copy()))
            return True
        else:
            return False

    def is_hide_required(self, context: bpy.types.Context):
        b_require_hide = not self.is_uv_selected()

        if not b_require_hide:
            if not self.is_general_update_valid():
                if self.enqueue_gizmo_check(context):
                    b_require_hide = True

        return b_require_hide

    def zenuv_internal_gizmo_uv_check(self, ctx_override: dict):
        try:
            p_event = get_blender_event(force=True)
            p_event_value = p_event.get('value', '')
            if p_event_value in {'PRESS'}:
                # we are disabling while mouse is pressed or key is hold
                return 0.01

            v_sel_center = self.getUVSelectedCenter(ctx_override)
            if v_sel_center != self.uv_selection_center or not self.is_general_update_valid():
                self.uv_selection_center = v_sel_center
                self.general_update = bpy.app.driver_namespace.get(LITERAL_ZENUV_GENERAL_UPDATE, '')

                ctx_override['area'].tag_redraw()

            self.uv_center_detection_started = False
        except Exception:
            pass

    def setup(self, context: bpy.types.Context):
        self.gizmo_drag = {}
        self.trim_mtx = Matrix()
        self.drag_started = False
        self.trimsheet_uuid = ''
        self.active_trim_uuid = ''
        self.active_trim_index = -1
        self.last_setup_position = 0
        self.uv_selection_center = Vector(self.CURSOR_UNDEFINED)
        self.general_update = 'UNDEFINED'
        self.uv_center_detection_started = False
        self.handled_text_rects = set()

        # Clear all Gizmos
        self.gizmos.clear()

        # Start creating Gizmos

        self.mpr_trim_align = {}
        self.mpr_trim_fitflip = {}

        self.mpr_box_select = self.gizmos.new("UV_GT_zenuv_trim_box_select")
        self.mpr_box_select.hide_select = True
        self.mpr_box_select.use_select_background = False
        self.mpr_box_select.use_draw_scale = False
        self.mpr_box_select.color = (0.5, 0.5, 0.5)
        self.mpr_box_select.alpha = 0.3

        self.mpr_select_background = self.gizmos.new("UV_GT_zenuv_trim_select_background")
        self.mpr_select_background.hide_select = True
        self.mpr_select_background.use_select_background = False
        self.mpr_select_background.use_draw_scale = False
        self.mpr_select_background.color = (0.5, 0.5, 0.5)
        self.mpr_select_background.alpha = 0.3

        if self.bl_idname != 'ZUV_GGT_UVTrimDisplay':
            for k in UV_AREA_BBOX.bbox_all_handles:

                self.mpr_trim_fitflip[k] = self.gizmos.new("UV_GT_zenuv_trim_fitflip")
                self.mpr_trim_fitflip[k].alpha = 1.0
                self.mpr_trim_fitflip[k].color = (0.8, 0.8, 0.8)
                self.mpr_trim_fitflip[k].color_highlight = (0.8, 0.8, 0.8)
                self.mpr_trim_fitflip[k].alpha_highlight = 1.0
                self.mpr_trim_fitflip[k].hide_select = True
                self.mpr_trim_fitflip[k].use_draw_scale = True
                self.mpr_trim_fitflip[k].scale_basis = 0.2  # used when 'draw is scaled only'
                self.mpr_trim_fitflip[k].direction = k
                # create shapes when we know the direction
                self.mpr_trim_fitflip[k].setup()

                self.mpr_trim_align[k] = self.gizmos.new("UV_GT_zenuv_trim_align")
                self.mpr_trim_align[k].alpha = 0.0
                self.mpr_trim_align[k].color_highlight = 1.0, 1.0, 1.0
                self.mpr_trim_align[k].alpha_highlight = 1.0
                self.mpr_trim_align[k].hide_select = False
                self.mpr_trim_align[k].use_draw_scale = True
                self.mpr_trim_align[k].scale_basis = 0.2
                self.mpr_trim_align[k].direction = k
                op_props = self.mpr_trim_align[k].target_set_operator('zenuv.tool_trim_handle')
                op_props.direction = k
                op_props.pivot_prop = self.pivot_prop

        self._setup_dragged(context)

        self.mpr_trim = self.gizmos.new("GIZMO_GT_cage_2d")
        self.mpr_trim.color = 1.0, 0.0, 0.0
        self.mpr_trim.alpha = 0.5
        self.mpr_trim.color_highlight = 1.0, 1.0, 1.0
        self.mpr_trim.alpha_highlight = 1
        self.mpr_trim.transform = {'TRANSLATE', 'SCALE'}
        self.mpr_trim.hide_select = False
        self.mpr_trim_sca = (1, 1, 1)

        self.gizmo_drag[self.mpr_trim] = False

        def move_get_cb():
            return [c for row in self.trim_mtx.transposed() for c in row]

        def move_set_cb(value):
            import numpy as np
            arr = np.array(value)
            self.trim_mtx = Matrix(np.reshape(arr, (4, 4)))
            ctx = bpy.context

            p_trim_data = ZuvTrimsheetUtils.getActiveTrimData(ctx)

            if p_trim_data and self.mpr_trim_sca[0] > 0 and self.mpr_trim_sca[1] > 0:
                idx, p_trim, p_trimsheet = p_trim_data
                _, _, sca1 = self.trim_mtx.decompose()

                loc, _, _ = self.mpr_trim.matrix_world.decompose()
                x, y = ctx.region.view2d.region_to_view(loc.x, loc.y)

                width = self.mpr_trim_sca[0] * sca1.x
                height = self.mpr_trim_sca[1] * sca1.y

                if width > 0 and height > 0:

                    w_left, w_top, w_right, w_bottom = p_trim.rect

                    left = x - width / 2
                    bottom = y - height / 2
                    right = left + width
                    top = bottom + height

                    inc_l = left - w_left
                    inc_t = top - w_top
                    inc_r = right - w_right
                    inc_b = bottom - w_bottom

                    p_trim.set_rectangle(left, bottom + height, left + width, bottom)

                    if p_trim.selected:
                        p_selected_trims = ZuvTrimsheetUtils.getSelectedTrims(p_trimsheet)
                        if p_selected_trims:
                            for it_trim in p_selected_trims:
                                if it_trim == p_trim:
                                    continue
                                it_l, it_t, it_r, it_b = it_trim.rect
                                it_trim.set_rectangle(
                                        it_l + inc_l, it_t + inc_t,
                                        it_r + inc_r, it_b + inc_b)

                    update_areas_in_all_screens(bpy.context)
                self.trim_mtx = Matrix()

        self.mpr_trim.target_set_handler("matrix", get=move_get_cb, set=move_set_cb)

        # self.mpr_trim.use_draw_scale = False

        self.mpr_trim_select = {}

        # ALL GIZMOS MUST BE SET TILL THIS EVENT
        self._reset_dragged(context)

    def are_gizmos_modal(self):
        n_gizmo_count = len(self.gizmos)
        if n_gizmo_count:
            p_arr = np.empty(n_gizmo_count, 'b')
            self.gizmos.foreach_get('is_modal', p_arr)
            return np.any(p_arr)
        return False

    @classmethod
    def is_around_gizmo(cls, p_scene: bpy.types.Scene):
        return p_scene.zen_uv.ui.uv_tool.tr_handles == 'GIZMO' and p_scene.zen_uv.ui.uv_tool.mode in {'MOVE', 'SCALE', 'ROTATE'}

    def setup_position(self, context: bpy.types.Context, update_drag=True):
        p_cage_color = self.CAGE_DEFAULT_COLOR

        if update_drag:
            self._setup_dragged_position(context)

        # Trimsheet Section
        was_active_trim_uuid = self.active_trim_uuid
        self.active_trim_uuid = ''
        self.active_trim_index = -1

        p_trimsheet_owner = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        p_trimsheet = None

        def clear_select_gizmos():
            for p_gizmo in self.mpr_trim_select.values():
                self.gizmos.remove(p_gizmo)

            self.mpr_trim_select.clear()

        if p_trimsheet_owner:
            p_trimsheet = p_trimsheet_owner.trimsheet
            p_trim = ZuvTrimsheetUtils.getActiveTrimFromOwner(p_trimsheet_owner)

            b_need_to_update_trims = False

            if self.trimsheet_uuid != p_trimsheet_owner.trimsheet_geometry_uuid:
                self.trimsheet_uuid = p_trimsheet_owner.trimsheet_geometry_uuid
                b_need_to_update_trims = True

            p_new_uuid = p_trim.uuid if p_trim else ''
            if was_active_trim_uuid != p_new_uuid:
                b_need_to_update_trims = True

            n_trimsheet_count = len(p_trimsheet) if p_trimsheet else 0
            if len(self.mpr_trim_select) != n_trimsheet_count:
                b_need_to_update_trims = True

            if b_need_to_update_trims:
                clear_select_gizmos()

                for idx, it_trim in enumerate(p_trimsheet):
                    self.mpr_trim_select[idx] = self.gizmos.new("UV_GT_zenuv_trim_select")

                    self.mpr_trim_select[idx].hide_select = False
                    self.mpr_trim_select[idx].use_draw_scale = False
                    self.mpr_trim_select[idx].text = it_trim.name
                    self.mpr_trim_select[idx].active = it_trim == p_trim

                    op_props = self.mpr_trim_select[idx].target_set_operator('wm.zuv_trim_box_select')
                    op_props.trimsheet_index = idx

            if p_trim:
                self.active_trim_uuid = p_trim.uuid
                self.active_trim_index = p_trimsheet_owner.trimsheet_index
                p_cage_color = p_trim.color[:]

            self.mpr_trim.use_draw_scale = False
            self.mpr_trim.dimensions = (1, 1)
        else:
            self.trimsheet_uuid = ''
            clear_select_gizmos()

        self._setup_trimsheet_colors(context, p_trimsheet, p_cage_color)

        self.last_setup_position = timer()

    def _setup_trimsheet_colors(self, context: bpy.types.Context, p_trimsheet, p_active_color):
        n_trim_count = 0
        if p_trimsheet:
            n_trim_count = len(p_trimsheet)

        p_scene = context.scene
        addon_prefs = get_prefs()

        s_tool_mode = p_scene.zen_uv.ui.uv_tool.mode
        b_is_create_mode = s_tool_mode == 'CREATE'
        b_is_resize_mode = s_tool_mode == 'RESIZE'
        b_is_display_mode = self.bl_idname == 'ZUV_GGT_UVTrimDisplay'
        b_is_select_mode = s_tool_mode == 'SELECT'

        b_interactive_enabled = self.is_workspace_tool_active(context)
        b_text_enabled = addon_prefs.trimsheet.display_name

        self.handled_text_rects = set()

        self.mpr_box_select.hide = not (
            p_scene.zen_uv.ui.uv_tool.display_trims and
            p_scene.zen_uv.ui.uv_tool.select_trim) or b_is_display_mode
        self.mpr_select_background.hide = self.mpr_box_select.hide

        if not self.mpr_select_background.hide:
            self.mpr_select_background.color = addon_prefs.trimsheet.background_color[:3]
            self.mpr_select_background.alpha = addon_prefs.trimsheet.background_color[-1]

        for k, v in self.mpr_trim_select.items():
            b_active = self.active_trim_index == k

            b_trim_visible = (
                p_scene.zen_uv.ui.uv_tool.display_trims and
                (b_active or p_scene.zen_uv.ui.uv_tool.display_all))

            v.hide = not b_trim_visible
            if not v.hide and k < n_trim_count:
                p_trim: ZuvTrimsheetGroup = p_trimsheet[k]

                p_color_settings: TrimColorSettings = p_trim.get_draw_color_settings(addon_prefs.trimsheet, b_active, p_trim.selected)

                v.fill_color = p_color_settings.color[:]
                v.fill_alpha = p_color_settings.color_alpha
                v.border_color = p_color_settings.border[:]
                v.border_alpha = p_color_settings.border_alpha
                v.text_color = p_color_settings.text_color[:]
                v.active = b_active
                v.text_enabled = b_text_enabled

                v.hide_select = (
                    not b_interactive_enabled or
                    b_is_display_mode or
                    b_is_create_mode or
                    not p_scene.zen_uv.ui.uv_tool.display_trims or
                    not p_scene.zen_uv.ui.uv_tool.select_trim)

        b_handles_enabled = p_scene.zen_uv.ui.uv_tool.tr_handles != 'OFF'
        b_is_align_available = b_handles_enabled and s_tool_mode in {'MOVE', 'ROTATE', 'SCALE'}
        b_is_cage_available = p_scene.zen_uv.ui.uv_tool.display_trims or s_tool_mode in {'RESIZE', 'CREATE'}

        b_around_gizmo = self.is_around_gizmo(p_scene)

        self.mpr_trim.hide = not b_is_cage_available or self.active_trim_index not in range(n_trim_count)
        if not self.mpr_trim.hide:
            p_trim = p_trimsheet[self.active_trim_index]

            p_color_settings = p_trim.get_draw_color_settings(addon_prefs.trimsheet, True, p_trim.selected)  # type: TrimColorSettings

            self.mpr_trim.color = p_color_settings.border[:]
            self.mpr_trim.alpha = p_color_settings.color_alpha

            self.mpr_trim.color_highlight = (1, 1, 1)
            self.mpr_trim.alpha_highlight = p_color_settings.border_alpha

            s_box_transfrom = 'CIRCLE' if bpy.app.version < (3, 5, 0) else 'BOX_TRANSFORM'

            self.mpr_trim.draw_style = s_box_transfrom if s_tool_mode == 'RESIZE' else 'BOX'
            self.mpr_trim.hide_select = not b_is_resize_mode or not b_interactive_enabled

        for k, v in self.mpr_trim_align.items():
            v.hide = not b_is_align_available and not b_is_display_mode and not b_is_select_mode
            v.hide_select = not b_is_align_available or not b_interactive_enabled
            self.mpr_trim_fitflip[k].hide = v.hide or v.is_highlight
            if not v.hide:
                v.color = self.CAGE_DEFAULT_COLOR if b_around_gizmo else p_active_color
                v.color_highlight = v.color

                self.mpr_trim_fitflip[k].color = v.color

    def setup_colors(self, context: bpy.types.Context):
        p_trimsheet = None
        p_active_color = self.CAGE_DEFAULT_COLOR

        p_trimsheet_owner = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_trimsheet_owner:
            p_trimsheet = p_trimsheet_owner.trimsheet
            p_trim = ZuvTrimsheetUtils.getActiveTrimFromOwner(p_trimsheet_owner)
            if p_trim:
                p_active_color = p_trim.color[:]

        self._setup_trimsheet_colors(context, p_trimsheet, p_active_color)

    def _setup_matrices_final(self, context: bpy.types.Context) -> bool:
        rgn2d = context.region.view2d

        if not self.mpr_box_select.hide:

            ui_scale = context.preferences.view.ui_scale

            p_offsets = ZuvTrimsheetUtils.get_area_offsets(context.area)
            n_top_offset = p_offsets.get('top')
            n_right_offset = 30 * ui_scale
            n_left_offset = p_offsets.get('left')
            n_bottom_offset = p_offsets.get('bottom') + 10 * ui_scale

            v_sca = Vector((context.area.width - n_left_offset - n_right_offset, context.area.height - n_top_offset - n_bottom_offset, 1.0))

            v_region_center = Vector((v_sca.x / 2 + n_left_offset, v_sca.y / 2 + n_bottom_offset, 0))
            self.mpr_box_select.matrix_basis = (
                Matrix.Translation(v_region_center) @
                Matrix.Diagonal(v_sca).to_4x4())

        p_trimsheet_owner = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        p_trimsheet = None
        if p_trimsheet_owner:
            p_trimsheet = p_trimsheet_owner.trimsheet
            for k, v in self.mpr_trim_select.items():
                if not v.hide:
                    p_select_trim = p_trimsheet[k]
                    x_cen, y_cen, x_width, y_height = p_select_trim.get_rgn2d_origin_dimensions(rgn2d)

                    self.mpr_trim_select[k].matrix_basis = Matrix.Translation((x_cen, y_cen, 0))
                    self.mpr_trim_select[k].dimensions = (x_width, y_height)

        p_trim = ZuvTrimsheetUtils.getActiveTrim(context)
        if p_trim:
            if not self.mpr_trim.is_modal and not self.mpr_trim.hide:
                x_cen, y_cen, x_width, y_height = p_trim.get_rgn2d_origin_dimensions(rgn2d)

                mtx_scale = (
                    Matrix.Diagonal((x_width, y_height, 1.0)).to_4x4() if x_width and y_height else Matrix())

                self.mpr_trim.matrix_basis = Matrix.Translation((x_cen, y_cen, 0)) @ mtx_scale
                self.trim_mtx = Matrix()
                self.mpr_trim.matrix_offset = Matrix()
                self.mpr_trim.dimensions = (1.0, 1.0)
                self.mpr_trim_sca = (p_trim.width, p_trim.height)

        p_scene = context.scene
        b_around_gizmo = self.is_around_gizmo(p_scene)

        b_is_move_mode = p_scene.zen_uv.ui.uv_tool.mode == 'MOVE'

        p_UV_AREA_DEFAULT = UV_AREA_BBOX()
        for k, v in self.mpr_trim_align.items():
            if not v.hide:

                v_p = getattr(p_UV_AREA_DEFAULT, k)  # type: Vector

                from ..view3d_trim import ZuvTrimFitFlipGizmo

                if b_around_gizmo:
                    if not self.are_gizmos_modal() and self.is_uv_selected():
                        rgn2d = context.region.view2d

                        x, y, = rgn2d.view_to_region(self.uv_selection_center.x, self.uv_selection_center.y, clip=False)

                        mtx = Matrix.Translation(Vector((x, y, 0)))

                        ui_scale = context.preferences.view.ui_scale
                        d_gizmo_size = context.preferences.view.gizmo_size
                        radius = d_gizmo_size * 0.2

                        if b_is_move_mode:
                            d_gizmo_size += radius

                        d_gizmo_size *= ui_scale

                        if b_is_move_mode:
                            d_gizmo_size *= 2.5
                        else:
                            d_gizmo_size *= 3.0

                        v.matrix_basis = mtx @ Matrix.Translation((v_p.x * d_gizmo_size - d_gizmo_size / 2, v_p.y * d_gizmo_size - d_gizmo_size / 2, 0.0))
                else:
                    if p_trim:
                        v_p2 = Vector((p_trim.left + v_p.x * p_trim.width, p_trim.bottom + v_p.y * p_trim.height))
                    else:
                        v_p2 = v_p

                    v_rgn_dir = Vector(rgn2d.view_to_region(v_p2.x, v_p2.y, clip=False))
                    v_rgn_dir.resize_3d()

                    v.matrix_basis = Matrix.Translation(v_rgn_dir)

                self.mpr_trim_fitflip[k].matrix_basis = (
                    v.matrix_basis @ ZuvTrimFitFlipGizmo.get_direction_rotation_matrix(self.mpr_trim_fitflip[k].direction)
                )
        return True

    def is_trimsheet_modified(self, context: bpy.types.Context) -> bool:
        b_modified = False
        p_trimsheet_owner = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_trimsheet_owner:
            if p_trimsheet_owner.trimsheet_geometry_uuid != self.trimsheet_uuid:
                b_modified = True
            else:
                p_uuid = ''
                p_trim = ZuvTrimsheetUtils.getActiveTrimFromOwner(p_trimsheet_owner)
                if p_trim:
                    p_uuid = p_trim.uuid
                if self.active_trim_uuid != p_uuid:
                    b_modified = True
        else:
            if self.trimsheet_uuid != '':
                b_modified = True

        return b_modified

    def _check_object_data_before_draw(self, context: bpy.types.Context):
        # This method is required only for Gizmos working with mesh
        pass

    def draw_prepare(self, context: bpy.types.Context):
        b_was_setup = False


        if not self.are_gizmos_modal():
            if self.is_trimsheet_modified(context):
                self.setup_position(context, update_drag=False)
                b_was_setup = True
            else:
                b_was_setup = self._check_object_data_before_draw(context)

        if not b_was_setup:
            self.setup_colors(context)

        # Must be used after base matrices were setup
        self._setup_matrices_final(context)

    def _check_object_data_after_refresh(self, context: bpy.types.Context):
        if self.is_trimsheet_modified(context):
            self.setup_position(context, update_drag=False)

    def refresh(self, context: bpy.types.Context):

        if is_modal_procedure(context):
            return


        # Are we in drag mode
        b_drag_completed = self._check_and_set_drag_completed()

        if b_drag_completed:
            self._drag_completed(context)
        else:
            self._check_object_data_after_refresh(context)

    def setup_operator_pivot(self, context: bpy.types.Context):
        if not self.are_gizmos_modal():
            p_scene = context.scene

            pivot = rgetattr(p_scene, self.pivot_prop)

            for v in self.mpr_trim_align.values():
                v.is_pivot = v.direction == pivot
