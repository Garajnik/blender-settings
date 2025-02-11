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

""" Zen Unwrap Operator """

import bpy
import bmesh

from ZenUV.utils.generic import fit_uv_view

from ZenUV.utils.mark_utils import zuv_mark_seams

from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.hops_integration import show_uv_in_3dview
from .ui import ZENUNWRAP_PT_Properties
from .utils import (
    uObject,
    UIslandsManager
)
from .props import ZenUnwrapState, LiveUnwrapPropManager
from ZenUV.utils.vlog import Log
from ZenUV.utils.global_report import ZuvReporter
from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel


CAT = "ZenUnwrap"


class ZUV_OT_ZenUnwrap(bpy.types.Operator, ZuvReporter):
    """ Zen Unwrap Operator """
    bl_idname = "uv.zenuv_unwrap"
    bl_label = ZuvLabels.ZEN_UNWRAP_LABEL
    bl_description = ZuvLabels.ZEN_UNWRAP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    action: bpy.props.EnumProperty(
        items=[
            ("DEFAULT", "Zen Unwrap", "Default Zen Unwrap Mode."),
            ("AUTO", "Auto Seams Mode", "Perform Auto Seams Before Zen Unwrap."),
            ("CONTINUE", "Continue Mode", "Perform Unwrap with no respect to warnings."),
            ("LIVE_UWRP", "Live Unwrap Mode", "Perform Unwrap in No Selection Mode")
            ],
        default="DEFAULT",
        options={'HIDDEN'}
    )

    def draw(self, context):
        context.scene.zen_uv.op_zen_unwrap_sc_props.draw_zen_unwrap(self.layout, context)

    @classmethod
    def poll(cls, context):
        """ Validate context """
        is_active_object = context.active_object is not None and context.active_object.type == 'MESH'
        is_sync_mode = context.area.type == "VIEW_3D" or context.area.type == "IMAGE_EDITOR" and context.scene.tool_settings.use_uv_select_sync
        return is_active_object and context.mode == 'EDIT_MESH' and is_sync_mode

    def execute(self, context):
        from .props import ZenUnwrapProps
        self.report_clear()
        Log.debug_header(" Zen Unwrap Processing ")
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}
        objs = [uObject(context, obj) for obj in objs]
        STATE = ZenUnwrapState(context, objs)
        STATE.set_operator_mode(self.action)
        PROPS: ZenUnwrapProps = STATE.PROPS

        STATE.objs_count = len(objs)

        if PROPS.ActivateSyncUV:
            context.scene.tool_settings.use_uv_select_sync = True
            STATE.update_sync_mode(context)

        # # In the EDGE Selection mode Mark will do anyway.
        # if STATE.bl_selection_mode == "EDGE":
        #     # context.scene.zen_uv.op_zen_unwrap_sc_props.MarkUnwrapped = True
        #     # PROPS.Mark = True
        #     pass
        # STATE.bl_selection_mode == "VERTEX" and
        if PROPS.ProcessingMode == 'URP_VERTICES':
            self.unwrap_selected_vertices(context, objs, STATE)
            return {'FINISHED'}

        if self.action == "LIVE_UWRP":
            # LiveUnwrapPropManager.show_args()
            LiveUnwrapPropManager.store_props(STATE)
            LiveUnwrapPropManager.set_live_unwrap_preset(STATE)
        else:
            context.scene.tool_settings.use_edge_path_live_unwrap = False

        # Detect Operator Processing Mode
        if STATE.OPM == "ALL" and PROPS.ProcessingMode == 'SEL_ONLY' and not STATE.selection_exist:
            STATE.set_selected_only(context, 'WHOLE_MESH')
            bpy.ops.wm.call_menu(name="ZUV_MT_ZenUnwrap_ConfirmPopup")
            return {'CANCELLED'}

        # Filtering objects without selection
        if STATE.OPM == 'SELECTION' and PROPS.ProcessingMode == 'SEL_ONLY':  # not STATE.is_pack_allowed():
            objs = [obj for obj in objs if obj.sel_exist]
            STATE.objs_count = len(objs)
        else:
            pass

        # Full Automatic Unwrap Mode. First Perform Auto Seams
        if STATE.operator_mode == "AUTO":
            bpy.ops.uv.zenuv_auto_mark("INVOKE_DEFAULT")
            STATE.update_seams_exist(objs)
            STATE.skip_warning = True

        if STATE.operator_mode == "CONTINUE":
            STATE.skip_warning = True

        if STATE.is_all_ready_to_unwrap(objs) is False and STATE.skip_warning is False:
            bpy.ops.wm.call_menu(name="ZUV_MT_ZenUnwrap_Popup")
            STATE.skip_warning = True
            return {'CANCELLED'}

        # Unwrapping Phase
        result = self._unwrap(context, objs, STATE)
        if result == {'CANCELLED'}:
            return result

        # Pack Phase
        if STATE.is_pack_allowed():
            kp_st = PROPS.KeepStacks
            PROPS.KeepStacks = '0'
            bpy.ops.uv.zenuv_pack('INVOKE_DEFAULT', display_uv=False, disable_overlay=True, fast_mode=True)
            PROPS.KeepStacks = kp_st

        # Sortig Phase
        if STATE.is_sorting_allowed():
            for uobj in objs:
                uobj.sorting_finished(context)

        # Restore Initial Selection if works in Selection Mode
        self.restore_init_selection(objs, STATE, PROPS)

        fit_uv_view(context, mode=STATE.fit_view)

        # Display UV Widget from HOPS addon
        if PROPS.ProcessingMode == 'SEL_ONLY':
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=True)
        else:
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=False)

        # Reset self values to default
        self.reset_values(context, STATE)

        if STATE.finished_came_across:
            s_message = "Zen UV: Finised Islands is came across. They were not unwrapped."
            self.report_ex({'WARNING'}, s_message)

        return {'FINISHED'}

    def restore_init_selection(self, objs, STATE, PROPS):
        if STATE.selection_exist:
            for uobj in objs:
                uobj.restore_selection(STATE.bl_selection_mode)

            if len(objs) == 1:
                STATE.fit_view = "selected"
            else:
                STATE.fit_view = "all"

        else:
            bpy.ops.mesh.select_all(action='DESELECT')
            if PROPS.SortFinished:
                STATE.fit_view = "checker"
            else:
                STATE.fit_view = "all"

    def unwrap_selected_vertices(self, context, objs, STATE):
        from .props import ZenUnwrapProps
        PROPS: ZenUnwrapProps = STATE.PROPS
        view_layer = context.view_layer
        active_obj = view_layer.objects.active

        bpy.ops.object.mode_set(mode='OBJECT')

        for obj in objs:
            obj.select_set(state=False)

        for uobj in objs:
            obj = uobj.obj
            Log.debug_header_short(f" Processed Object --> {obj.name} ")
            view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')

            me = obj.data
            bm = bmesh.from_edit_mesh(me)
            bm.edges.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()

            IM = UIslandsManager(uobj, bm, uv_layer, STATE)

            uobj.seam_state = [e.seam for e in bm.edges]
            result = IM.set_seams_in_vertex_processing_mode(context, uobj, bm)
            if not result:
                pass

            IM.pin_all_but_not_sel()
            bpy.ops.mesh.select_all(action='SELECT')
            IM._unwrap(context, bm)
            IM.restore_pins()
            bpy.ops.mesh.select_all(action='DESELECT')

            uobj.restore_seams(bm)

            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(state=False)

        self.finish_objs_processing(objs, view_layer, active_obj)

        self.restore_init_selection(objs, STATE, PROPS)

    def reset_values(self, context, STATE):
        from .props import ZenUnwrapProps
        if self.action == "LIVE_UWRP":
            LiveUnwrapPropManager.restore_props(STATE)

        STATE.set_operator_mode("DEFAULT")
        STATE.one_by_one = False

        PROPS: ZenUnwrapProps = STATE.PROPS
        PROPS.Mark = True
        context.scene.tool_settings.use_edge_path_live_unwrap = STATE.bl_live_unwrap

    def _unwrap(self, context, objs, STATE):
        from .props import ZenUnwrapProps
        PROPS: ZenUnwrapProps = STATE.PROPS
        view_layer = context.view_layer
        active_obj = view_layer.objects.active

        bpy.ops.object.mode_set(mode='OBJECT')

        for obj in objs:
            obj.select_set(state=False)

        for uobj in objs:
            obj = uobj.obj
            Log.debug_header_short(f" Processed Object --> {obj.name} ")
            view_layer.objects.active = obj
            obj.select_set(state=True)
            bpy.ops.object.mode_set(mode='EDIT')

            me = obj.data
            if not me.uv_layers:
                me.uv_layers.new()

            bm = bmesh.from_edit_mesh(me)
            uv_layer = bm.loops.layers.uv.verify()

            if uobj.is_pack_excluded:
                uobj.hide_pack_excluded(bm)

            # Clear Finished and Vcolor
            uobj.clear_finished_and_vcolor(bm)

            if PROPS.ProcessingMode == "SEAM_SWITCH" or STATE.OPM == "SELECTION" and PROPS.Mark and not STATE.bl_selection_mode == 'VERTEX':
                if STATE.is_mark_allowed():

                    mark_seam = True if PROPS.ProcessingMode == "SEAM_SWITCH" else STATE.mSeam
                    result = zuv_mark_seams(
                        context,
                        bm,
                        mark_seam,
                        STATE.mSharp,
                        silent_mode=True,
                        switch=PROPS.ProcessingMode == "SEAM_SWITCH")

                    if result is False:
                        uobj.closed_mesh = True
                        if STATE.objs_init_count == 1:
                            bpy.ops.wm.call_menu(name="ZUV_MT_ZenMark_Popup")
                            return {'CANCELLED'}

            IM = UIslandsManager(uobj, bm, uv_layer, STATE)

            bm.faces.ensure_lookup_table()

            if STATE.bl_selection_mode == 'EDGE' and not PROPS.ProcessingMode == "SEAM_SWITCH" and not STATE.operator_mode == "LIVE_UWRP":
                bpy.ops.mesh.mark_seam(clear=False)

            IM.create_islands(context)

            IM.z_unuwrap(context, bm)

            IM.restore_pins()

            if STATE.bl_selection_mode == 'EDGE' and not STATE.is_mark_allowed():
                if not PROPS.ProcessingMode == "SEAM_SWITCH":
                    if not STATE.operator_mode == "LIVE_UWRP":
                        uobj.clear_temp_seams()

            bpy.ops.mesh.select_all(action='DESELECT')

            IM.set_averaged_td(context, uobj, bm, uv_layer)
            IM.set_islands_positions(offset=True)

            if uobj.is_pack_excluded:
                uobj.unhide_pack_excluded(bm)

            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(state=False)

        self.finish_objs_processing(objs, view_layer, active_obj)

        return {'FINISHED'}

    def finish_objs_processing(self, objs, view_layer, active_obj):
        for obj in objs:
            obj.select_set(state=True)

        view_layer.objects.active = active_obj
        bpy.ops.object.mode_set(mode='EDIT')


ZenUnwrapClasses = [
    ZUV_OT_ZenUnwrap,
    ZENUNWRAP_PT_Properties
]

if __name__ == '__main__':
    pass
