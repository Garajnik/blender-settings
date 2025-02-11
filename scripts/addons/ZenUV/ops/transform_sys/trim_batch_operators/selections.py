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

import bpy
import bmesh
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.utils.bounding_box import BoundingBox2d
from ZenUV.utils.generic import (
    resort_by_type_mesh_in_edit_mode_and_sel,
    get_mesh_data,
    deselect_by_context,
    select_by_context
)
from ZenUV.utils.constants import UV_AREA_BBOX
from ZenUV.utils import get_uv_islands as island_util


class ZUV_OT_TrimSelectByFace(bpy.types.Operator):
    bl_idname = "uv.zenuv_trim_select_by_face"
    bl_label = "Select Trim by Face"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Select and make Trim Active by selected Face"

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'INFO'}, "There are no active object")
            return {'CANCELLED'}

        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is None:
            self.report({'INFO'}, "There are no TrimSheet Data.")
            return {'CANCELLED'}

        p_trimsheet = p_data.trimsheet
        bm = bmesh.from_edit_mesh(obj.data)
        p_face = bm.faces.active
        uv_layer = bm.loops.layers.uv.active
        if p_face is not None and uv_layer is not None:
            p_f_cen = BoundingBox2d(points=[lp[uv_layer].uv for lp in p_face.loops]).center
            scope = [
                trim for trim in p_trimsheet
                if trim.left_bottom.x < p_f_cen.x and
                trim.left_bottom.y < p_f_cen.y and
                trim.top_right.x > p_f_cen.x and
                trim.top_right.y > p_f_cen.y
                ]
            if not len(scope):
                self.report({'INFO'}, "The Active Face is not located in any of the Trims")
                return {'CANCELLED'}
            elif len(scope) > 1:
                self.report({'INFO'}, "An Active Face belongs to several Trims. The first one will be selected")

            bpy.ops.wm.zuv_trim_set_index(trimsheet_index=scope[0].get_index())

        return {"FINISHED"}


class ZUV_OT_TrimSelectIslandsByTrim(bpy.types.Operator):
    bl_idname = "uv.zenuv_select_island_by_trim"
    bl_label = "Select Island by Trim"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Select Islands inside active Trim"

    clear_sel: bpy.props.BoolProperty(
        name="Clear",
        description="Clear previous selection",
        default=True
    )
    mode: bpy.props.EnumProperty(
        name='Mode',
        description='Selection case',
        items=[
            ('INSIDE', 'Inside', 'The Bounding Box of Island are located entirely in the Trim'),
            ('OVERLAP', 'Overlap', 'The Bounding Box of Island partially overlap with Trim')
        ],
        default='INSIDE'
    )

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}

        if self.clear_sel:
            deselect_by_context(context)

        trim = ZuvTrimsheetUtils.getActiveTrim(context)
        if trim is not None:
            tr_bbox = BoundingBox2d(points=(trim.left_bottom, trim.top_right))
        else:
            tr_bbox = BoundingBox2d(points=(UV_AREA_BBOX().bl, UV_AREA_BBOX().tr))

        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()

            for island in island_util.get_islands(context, bm):
                if self.mode == 'INSIDE':
                    if BoundingBox2d(islands=[island, ], uv_layer=uv_layer).inside_of_bbox(tr_bbox):
                        select_by_context(context, bm, [island], state=True)
                elif self.mode == 'OVERLAP':
                    if BoundingBox2d(islands=[island, ], uv_layer=uv_layer).overlapped_with_bbox(tr_bbox):
                        select_by_context(context, bm, [island], state=True)
                else:
                    pass
            bmesh.update_edit_mesh(me, loop_triangles=False)

        return {"FINISHED"}


classes = (
    ZUV_OT_TrimSelectByFace,
    ZUV_OT_TrimSelectIslandsByTrim

)


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)
