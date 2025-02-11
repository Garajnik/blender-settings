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
import bmesh
import numpy as np
import random
from mathutils import Vector
from ZenUV.utils.bounding_box import BoundingBox2d
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.ops.transform_sys.transform_utils.tr_utils import Cursor2D


class ZUV_OT_NewTrim(bpy.types.Operator):
    bl_idname = "uv.zenuv_new_trim"
    bl_label = "New Trim"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Add Trim to Trimsheet'

    creation_mode: bpy.props.EnumProperty(
        name='Mode',
        description="Creation Mode",
        items=[
            ('DEFAULT', 'Default', 'Creates trim in trimsheet without bounding to geometry'),
            # Mesh Mode
            ("ISLAND", "Islands", "Creates trims from selected islands"),
            ("SELECTION", "Selection", "Creates Trims from selected elements (vertices, edges, faces). Each separate group of selections will create a separate island"),
            ("VERTS", "Vertices", "Creates a single island from all selected vertices"),
            ("FACES", "Faces", "Creates an Island from each selected face"),
        ],
        default="DEFAULT"
    )

    size: bpy.props.FloatProperty(
        name='Size',
        description='Size of the Trim',
        min=0.0,
        default=0.0
    )

    color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Trim color",
        subtype='COLOR',
        default=(0.0, 0.0, 0.0),
        size=3,
        min=0,
        max=1,
        options={'HIDDEN'}
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        b_is_edit_mesh = context.mode == 'EDIT_MESH'

        r_split = layout.row(align=False)
        r1 = r_split.row(align=True)
        r1.ui_units_x = 4
        r1.alignment = 'RIGHT'
        r1.label(text=self.properties.bl_rna.properties['creation_mode'].name)

        r2 = r_split.column(align=True)
        r_split.separator()

        col = r2.column(align=True)
        col.prop_enum(self, 'creation_mode', 'DEFAULT')
        if self.creation_mode == 'DEFAULT':
            col.prop(self, 'size')

        r2.separator()

        col = r2.column(align=True)
        col.active = b_is_edit_mesh
        for it in self.properties.bl_rna.properties['creation_mode'].enum_items:
            if it.identifier not in {'DEFAULT', 'CLONE'}:
                col.prop_enum(self, 'creation_mode', it.identifier)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self.action = 'CREATE'
        if event.shift:
            self.action = 'CLONE'
        self.color = (random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0))
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        if self.color[:] == (0.0, 0.0, 0.0):
            self.color = (random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0))

        if self.creation_mode == 'DEFAULT':
            if bpy.ops.uv.zuv_trim_add_sized.poll():
                return bpy.ops.uv.zuv_trim_add_sized('INVOKE_DEFAULT', size=self.size, color=self.color)
        else:
            if context.mode != 'EDIT_MESH':
                s_creation_mode = bpy.types.UILayout.enum_item_name(self, 'creation_mode', self.creation_mode)
                self.report({'INFO'}, f'Creation mode not available now: {s_creation_mode}')
                return {'FINISHED'}

            objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
            if not objs:
                self.report({'INFO'}, "There are no selected objects.")
                return {'CANCELLED'}

            bboxes = []
            for obj in objs:
                bm = bmesh.from_edit_mesh(obj.data).copy()
                try:
                    uv_layer = bm.loops.layers.uv.verify()

                    if self.creation_mode == 'ISLAND':
                        loops = island_util.LoopsFactory.loops_by_islands(context, bm, uv_layer)
                    elif self.creation_mode == 'SELECTION':
                        loops = island_util.LoopsFactory.loops_by_sel_mode(context, bm, uv_layer, groupped=True)
                    elif self.creation_mode == 'VERTS':
                        loops = island_util.LoopsFactory.loops_by_sel_mode(context, bm, uv_layer, groupped=False)
                        if len(loops):
                            loops = [loops]
                    elif self.creation_mode == 'FACES':
                        loops = island_util.LoopsFactory.loops_by_sel_mode(context, bm, uv_layer, groupped=False, per_face=True)
                    else:
                        raise RuntimeError("creation_mode not in {'iSLAND', 'SELECTION', 'FACES'}")

                    bboxes.extend([BoundingBox2d(points=([lp[uv_layer].uv for lp in region])) for region in loops])
                finally:
                    bm.free()

            if not len(bboxes):
                self.report({'WARNING'}, "There is no Selection.")
                return {'FINISHED'}

            stat = []
            for bbox in self.sort_bboxes_by_pos(bboxes):
                if round(bbox.len_x, 4) == 0.0 or round(bbox.len_y, 4) == 0.0:
                    stat.append(False)
                    continue
                if not Trim.new_generic_from_bbox(context, bbox):
                    self.report({'WARNING'}, "It is impossible to create Trim in this state of the scene")
                    return {'CANCELLED'}
                stat.append(True)

            if False in stat:
                self.report({'WARNING'}, f"Some trims with zero dimensions were not created. Number of incorrect trims {len([1 for i in stat if i is False])}")

            return {"FINISHED"}

    def sort_bboxes_by_pos(self, bboxes):
        return [bboxes[i] for i in np.lexsort(np.array(([bb.center.x for bb in bboxes], [bb.center.y for bb in bboxes])) * -1)]


class ZUV_OT_TrimCreateGrid(bpy.types.Operator):
    bl_idname = "uv.zuv_trim_create_grid"
    bl_label = 'Add Trim Grid'
    bl_description = 'Create Grid of Trims inside active, selected Trims, from Zero coordinates or 2D cursor position'
    bl_options = {'REGISTER', 'UNDO'}

    def get_lim_count_x(self):
        return self.get('trims_count_x', 2)

    def set_lim_count_x(self, value):
        if value * self.trims_count_y >= self.limit:
            self['trims_count_x'] = self.limit // self.trims_count_y
        else:
            self['trims_count_x'] = value

    def get_lim_count_y(self):
        return self.get('trims_count_y', 2)

    def set_lim_count_y(self, value):
        if value * self.trims_count_x >= self.limit:
            self['trims_count_y'] = self.limit // self.trims_count_x
        else:
            self['trims_count_y'] = value

    start_position: bpy.props.EnumProperty(
        name='Start Position',
        items=[
            ("ZERO_WORLD", "Zero Coordinates", "Start from zero coordinates x=0, y=0"),
            ("CURSOR_2D", "2D Cursor", "Start from 2D Cursor"),
            ("INSIDE_ACTIVE", "Inside of active Trim", "Creates a grid of Trims within the active Trim"),
            ("BBOX_SELECTION", "Inside of selected Trims", "Creates a grid of Trims within the selected Trims bounding box")
            ],
        default='ZERO_WORLD')
    trims_count_x: bpy.props.IntProperty(
        name='Trims Count U',
        description='Trims count Horizontal',
        set=set_lim_count_x,
        get=get_lim_count_x,
        min=1,
        default=2)
    trims_count_y: bpy.props.IntProperty(
        name='Trims Count V',
        description='Trims count Horizontal',
        set=set_lim_count_y,
        get=get_lim_count_y,
        min=1,
        default=2)
    grid_size: bpy.props.FloatVectorProperty(
        name="Grid Size",
        description="Size of the grid",
        subtype='COORDINATES',
        default=(1.0, 1.0),
        size=2,
        min=0)
    margin: bpy.props.FloatProperty(
        name='Margin',
        description='The gap between Trims',
        min=0.0,
        default=0.0,
        precision=3)
    remove_template: bpy.props.BoolProperty(
        name='Remove Template',
        default=False,
        description='Delete the Trim that served as a template')
    total: bpy.props.IntProperty(name='Count', default=1)
    limit: bpy.props.IntProperty(name='Trim Count Limit', description='Limit the number of trims', default=100, min=1)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'start_position')
        layout.prop(self, 'limit')
        layout.label(text='Count:')
        box = layout.box()
        row = box.row()
        row.alert = self.total >= self.limit
        p_alert_message = ' Limit reached' if row.alert else ''
        row.label(text='Total: ' + str(self.total) + p_alert_message)
        box.prop(self, 'trims_count_x')
        box.prop(self, 'trims_count_y')

        row = layout.row()
        row.enabled = self.start_position != 'INSIDE_ACTIVE'
        row.prop(self, 'grid_size')
        layout.prop(self, 'margin')
        row = layout.row()
        row.enabled = self.start_position in {'INSIDE_ACTIVE', 'BBOX_SELECTION'}
        row.prop(self, 'remove_template')

    def execute(self, context: bpy.types.Context):
        p_data = ZuvTrimsheetUtils.getTrimsheetOwner(context)
        if p_data is not None:
            if self.start_position == 'INSIDE_ACTIVE':
                p_a_trim = ZuvTrimsheetUtils.getActiveTrim(context)
                a_index = p_data.trimsheet_index
                if p_a_trim is None:
                    self.report({'WARNING'}, "There are no Active Trim.")
                    return {'FINISHED'}
                else:
                    p_a_trim.selected = True
                    init_position = p_a_trim.left_bottom.copy()
                    self.grid_size.x = p_a_trim.width
                    self.grid_size.y = p_a_trim.height

            elif self.start_position == 'ZERO_WORLD':
                init_position = Vector((0.0, 0.0))

            elif self.start_position == 'CURSOR_2D':
                init_position = Cursor2D(context).uv_cursor_pos
            elif self.start_position == 'BBOX_SELECTION':
                p_trims_sel_idxs = ZuvTrimsheetUtils.getTrimsheetSelectedIndices(p_data.trimsheet)

                if not len(p_trims_sel_idxs):
                    self.report({'WARNING'}, "There are no Selected Trims.")
                    return {'FINISHED'}

                points = sum([[p_data.trimsheet[idx].left_bottom, p_data.trimsheet[idx].top_right] for idx in p_trims_sel_idxs], [])
                bbox = BoundingBox2d(points=points)
                init_position = bbox.bot_left.copy()
                self.grid_size.x = bbox.len_x
                self.grid_size.y = bbox.len_y
            else:
                init_position = Vector((0.0, 0.0))

            self.total = self.trims_count_x * self.trims_count_y

            margin = self.margin
            if margin * (self.trims_count_x - 1) >= self.grid_size.x:
                margin = self.grid_size.x / (self.trims_count_x - 1) + 0.0001
                self.margin = margin

            gap_x = margin * (self.trims_count_x - 1)
            gap_y = margin * (self.trims_count_y - 1)

            try:
                x_size = (self.grid_size.x - gap_x) / self.trims_count_x
            except ZeroDivisionError:
                x_size = 0.0
            try:
                y_size = (self.grid_size.y - gap_y) / self.trims_count_y
            except ZeroDivisionError:
                y_size = 0.0

            p_trim_size = Vector((x_size, y_size))

            if self.total >= self.limit:
                self.report({'WARNING'}, 'The limit of the number of Trims has been reached.')

            for i in range(self.trims_count_x):
                p_trim_bl = init_position
                p_trim_tr = init_position + p_trim_size
                bbox = BoundingBox2d(points=(p_trim_bl, p_trim_tr))
                Trim.new_generic_from_bbox(context, bbox)

                init_y = Vector((init_position.x, init_position.y + p_trim_size.y + margin))
                for k in range(self.trims_count_y - 1):
                    p_trim_bl = init_y
                    p_trim_tr = init_y + p_trim_size
                    bbox = BoundingBox2d(points=(p_trim_bl, p_trim_tr))
                    Trim.new_generic_from_bbox(context, bbox)
                    init_y += Vector((0.0, margin + p_trim_size.y))

                init_position += Vector((margin + p_trim_size.x, 0.0))

            if self.start_position == 'INSIDE_ACTIVE':
                p_data.trimsheet_index = a_index

            if self.start_position == 'INSIDE_ACTIVE' and self.remove_template:
                p_data.trimsheet.remove(a_index)

            if self.start_position == 'BBOX_SELECTION' and self.remove_template:
                for idx in reversed(p_trims_sel_idxs):
                    p_data.trimsheet.remove(idx)

            return {'FINISHED'}

        return {'CANCELLED'}


class Trim:

    @classmethod
    def new_generic_from_bbox(cls, context: bpy.types.Context, bbox: BoundingBox2d) -> bool:
        res = bpy.ops.uv.zuv_trim_add('INVOKE_DEFAULT')
        if 'FINISHED' in res:
            p_new_trim = ZuvTrimsheetUtils.getActiveTrim(context)
            if p_new_trim:
                p_new_trim.rect = bbox.rect
            return True
        else:
            return False


trim_creation_classes = (
    ZUV_OT_NewTrim,
    ZUV_OT_TrimCreateGrid
)


def register_trim_create():
    from bpy.utils import register_class
    for cl in trim_creation_classes:
        register_class(cl)


def unregister_trim_create():
    from bpy.utils import unregister_class
    for cl in trim_creation_classes:
        unregister_class(cl)
