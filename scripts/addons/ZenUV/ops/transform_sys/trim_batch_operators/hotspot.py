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

""" Zen UV The batch transformation is dependent on the Trim module """

# Copyright 2023, Valeriy Yatsenko

import bpy
import bmesh
from mathutils import Vector
from dataclasses import dataclass, field

from math import pi
from random import choice, uniform

from ZenUV.utils.generic import (
    resort_by_type_mesh_in_edit_mode_and_sel,
    select_by_context,
    deselect_by_context,
)
from ZenUV.utils.generic import get_mesh_data, Scope
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.utils.bounding_box import BoundingBox2d
from ZenUV.ops.transform_sys.transform_utils.transform_loops import TransformLoops
from ZenUV.ops.transform_sys.transform_utils.tr_rotate_utils import TrOrientProcessor
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
from ZenUV.ops.world_orient import oCluster
from ZenUV.ops.transform_sys.transform_utils.tr_utils import ActiveUvImage
from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetGroup
from ZenUV.utils.vlog import Log


CAT = 'HOTSPOT'


@dataclass
class HspTrim:

    trim: ZuvTrimsheetGroup = None
    bbox: BoundingBox2d = None
    aspect: float = None
    aspect_inverted: float = None
    _radial: bool = None

    def __hash__(self):
        return hash(tuple(self.bbox.center))

    @property
    def radial(self):
        if self.trim.get_tag_value(tag_category='HOTSPOT', default='None') == 'Radial':
            return True
        return False


@dataclass
class HspIsland:

    faces: list = field(default_factory=list)
    bbox: BoundingBox2d = None
    aspect: float = None
    aspect_inverted: float = None
    _radial: bool = None
    _loops: list = field(default_factory=list)

    def __hash__(self):
        return hash(tuple(self.faces))

    @property
    def loops(self):
        return [lp for f in self.faces for lp in f.loops]

    @property
    def radial(self):
        if self._radial is None:
            self._radial = self.bbox.is_circle()
        return self._radial

    @radial.setter
    def radial(self):
        raise RuntimeError('HspIsland.radial read only.')


class HspStorage:

    def __init__(self) -> None:

        self.trims = set()
        self.islands = set()

        self.radial_trims = set()
        self.radial_islands = set()

        self._trims_count = 0
        self._islands_count = 0

        self.radial_islands_idxs_scope = dict()

    @property
    def trims_count(self):
        self._trims_count = len(self.trims)
        return self._trims_count

    @property
    def islands_count(self):
        self._islands_count = len(self.islands) + len(self.radial_islands)
        return self._islands_count

    def collect_radial_idxs(self, obj) -> None:
        self.radial_islands_idxs_scope.update({obj.name: [f.index for island in self.radial_islands for f in island.faces]})

    def get_aspect_suited_trims(self, container, aspect, allow_rotation):
        t_scp = Scope()
        t_scp.name = 'Trims Scope'

        if allow_rotation:
            for trim in container:
                t_scp.append(trim.aspect, trim)
                t_scp.append(trim.aspect_inverted, trim)
        else:
            for trim in container:
                t_scp.append(trim.aspect, trim)

        return t_scp.data[min(t_scp.data.keys(), key=lambda x: abs(aspect - x))]

    def get_area_suited_trim(self, h_trims, h_island, scalar, allow_rotation):
        area_scp = Scope()
        for trim in h_trims:
            area_scp.append(trim.bbox.len_x * trim.bbox.len_y, trim)
        return area_scp.data[min(area_scp.data.keys(), key=lambda x: abs(h_island.bbox.area * scalar - x))]

    def collect_trims(self, trimsheet: list, detect_radial) -> None:
        self.trims.clear()
        for trim in trimsheet:
            trim_bbox = BoundingBox2d(points=(trim.left_bottom, trim.top_right))

            self.trims.add(
                HspTrim(
                    trim,
                    trim_bbox,
                    trim_bbox.aspect,
                    trim_bbox.aspect_inverted,
                )
            )

        if detect_radial:
            self.radial_trims = {trim for trim in self.trims if trim.radial}
            self.trims = self.trims.difference(self.radial_trims)

    def collect_islands(self, context, bm, uv_layer, detect_radial) -> None:
        self.islands.clear()
        for island in island_util.get_island(context, bm, uv_layer):
            i_bbox = BoundingBox2d(islands=[island, ], uv_layer=uv_layer)
            self.islands.add(
                HspIsland(
                    island,
                    i_bbox,
                    i_bbox.aspect,
                    i_bbox.aspect_inverted
                )
            )
        if detect_radial:
            self.radial_islands = {island for island in self.islands if island.radial}
            self.islands = self.islands.difference(self.radial_islands)

    def update_islands(self, uv_layer):
        for island in self.islands:
            self.update_island_data(uv_layer, island)
        for island in self.radial_islands:
            self.update_island_data(uv_layer, island)

    def update_island_data(self, uv_layer, island):
        island.bbox = BoundingBox2d(islands=[island.faces, ], uv_layer=uv_layer)
        island.aspect = island.bbox.aspect
        island.aspect_inverted = island.bbox.aspect_inverted


@dataclass
class HspPropertiesBase:
    """ HotspotFactory Properties Base Class"""

    def __post_init__(self, PROPS) -> None:
        self.get_properties_from(PROPS)

    def get_properties_from(self, PROPS: bpy.types.OperatorProperties) -> None:
        """ Get properties from bpy.types.OperatorProperties class """
        # print('PROPS Transfer')
        for prp in self.__annotations__.keys():
            attr = getattr(PROPS, prp, None)
            if attr is None:
                Log.debug(f'Property "{prp}" not present in the {PROPS} Class')
                continue
            setattr(self, prp, attr)


@dataclass
class HspProperties(HspPropertiesBase):
    """ HotspotFactory Properties """
    orient: str = 'AS_IS'  # in {"NONE", "WORLD", "ORIENT"}
    area_match: str = 'AS_IS'  # in {"AS_IS", "MAX", "MIN", "MANUAL"}
    manual_scale: float = 1.0
    allow_rotation: bool = True
    allow_rotation_variation: bool = False
    keep_proportion: str = 'YES'  # in {"YES", "NO", "FROM_TRIM"}
    fit_axis: str = 'AUTO'  # in {"AUTO", "FROM_TRIM"}
    detect_radial: bool = False
    select_radials: bool = False
    allow_location_variation: bool = False
    loc_var_offset: float = 0.0
    aspect_precision: float = 1.0
    trims_preselection: str = 'ALL'  # in {"ALL", "SELECTED"}
    priority: str = 'ASPECT'  # in {"ASPECT", "AREA"}

    def __post_init__(self, PROPS) -> None:
        super().__post_init__(PROPS)


class HotspotFactory(HspProperties):

    def __init__(self, PROPS: bpy.types.OperatorProperties) -> None:
        super().__post_init__(PROPS)

        self.hTrims = []
        self.hIslands = []

    def do_hotspotting(self, context: bpy.types.Context, objs: list, p_trimsheet: list):

        HST = self.conditional_store_trims(p_trimsheet)
        scalar = self._get_scalar()

        for obj in objs:
            me, bm = get_mesh_data(obj)
            uv_layer = bm.loops.layers.uv.verify()

            HST.collect_islands(context, bm, uv_layer, self.detect_radial)

            if self.orient == 'WORLD':
                self.world_orient_islands(context, obj, bm, HST.islands)
                HST.update_islands(uv_layer)
            elif self.orient == 'ORIENT':
                self.orient_to_near_axis(context, HST.islands, uv_layer)
                HST.update_islands(uv_layer)

            for island in HST.islands:
                if self.priority == 'ASPECT':
                    suited_trims = self.trims_by_aspect_priority(HST, scalar, island)
                elif self.priority == 'AREA':
                    suited_trims = self.trims_by_area_priority(HST, scalar, island)

                if not len(suited_trims):
                    continue
                if self.allow_location_variation:
                    suited_trim = choice(suited_trims)  # type: HspTrim
                else:
                    suited_trim = suited_trims[0]  # type: HspTrim

                if self.allow_rotation and island.bbox.is_vertical != suited_trim.bbox.is_vertical:
                    match_angle = pi / 2
                else:
                    match_angle = 0.0

                if self.allow_rotation_variation:
                    match_angle += choice([0.0, pi])

                if self.fit_axis != 'AUTO':
                    fit_axis = suited_trim.trim.fit_axis
                else:
                    fit_axis = 'AUTO'

                if self.keep_proportion == 'YES':
                    keep_proportion = True
                elif self.keep_proportion == 'NO':
                    keep_proportion = False
                else:
                    keep_proportion = suited_trim.trim.keep_proportion

                if fit_axis == 'MIN':
                    random_offset = uniform(- self.loc_var_offset, self.loc_var_offset)
                    suited_trim_bbox = suited_trim.bbox.moved(
                        Vector.Fill(2, random_offset) * suited_trim.bbox.get_longest_axis_vector())
                else:
                    suited_trim_bbox = suited_trim.bbox

                TransformLoops.fit_loops(
                        loops=island.loops,
                        uv_layer=uv_layer,
                        fit_bbox=suited_trim_bbox,
                        fit_axis_name=fit_axis,
                        keep_proportion=keep_proportion,
                        angle=match_angle,
                        rotate=self._is_rotation_allowed()
                    )
            if self.detect_radial and len(HST.radial_islands):
                container = HST.radial_trims if len(HST.radial_trims) else HST.trims

                for island in HST.radial_islands:

                    suited_trims = HST.get_area_suited_trim(container, island, scalar, self.allow_rotation)

                    if not len(suited_trims):
                        continue
                    if self.allow_location_variation:
                        suited_trim = choice(suited_trims)  # type: HspTrim
                    else:
                        suited_trim = suited_trims[0]  # type: HspTrim

                    if self.allow_rotation and island.bbox.is_vertical != suited_trim.bbox.is_vertical:
                        match_angle = pi / 2
                    else:
                        match_angle = 0.0

                    if self.allow_rotation_variation:
                        match_angle += choice(range(0, 360, 5))

                    TransformLoops.fit_loops(
                            loops=island.loops,
                            uv_layer=uv_layer,
                            fit_bbox=suited_trim.bbox,
                            fit_axis_name=fit_axis,
                            keep_proportion=keep_proportion,
                            angle=match_angle,
                            rotate=self._is_rotation_allowed()
                        )
                HST.collect_radial_idxs(obj)

            bmesh.update_edit_mesh(me)

        if self.select_radials:
            deselect_by_context(context)

            for obj_name, p_f_idxs in HST.radial_islands_idxs_scope.items():
                me, bm = get_mesh_data(context.scene.objects[obj_name])

                p_faces = [bm.faces[i] for i in p_f_idxs]
                select_by_context(context, bm, [p_faces, ], state=True)

                bmesh.update_edit_mesh(me)

        return HST.islands_count

    def conditional_store_trims(self, p_trimsheet):
        HST = HspStorage()

        if self.trims_preselection == 'SELECTED':
            p_presel_trims = [tr for tr in p_trimsheet if tr.selected]
        else:
            p_presel_trims = p_trimsheet
        HST.collect_trims(p_presel_trims, self.detect_radial)
        return HST

    def _is_rotation_allowed(self):
        return self.allow_rotation or self.allow_rotation_variation

    def trims_by_aspect_priority(self, HST, scalar, island):
        presumptive_aspect = island.aspect + self.aspect_precision
        suited_trims = HST.get_aspect_suited_trims(HST.trims, presumptive_aspect, self.allow_rotation)

        return HST.get_area_suited_trim(suited_trims, island, scalar, self.allow_rotation)

    def trims_by_area_priority(self, HST, scalar, island):
        suited_trims = HST.get_area_suited_trim(HST.trims, island, scalar, self.allow_rotation)

        presumptive_aspect = island.aspect + self.aspect_precision
        return HST.get_aspect_suited_trims(suited_trims, presumptive_aspect, self.allow_rotation)

    def get_match_angle(self, i_bbox: BoundingBox2d, image_aspect):
        if self.orient == 'ORIENT':
            return i_bbox.get_orient_angle(image_aspect)
        return 0.0

    def _get_scalar(self):
        if self.area_match == 'AS_IS':
            return 1.0
        elif self.area_match == 'MAX':
            return 50
        elif self.area_match == 'MIN':
            return 0.1
        else:
            return self.manual_scale

    def world_orient_islands(self, context: bpy.types.Context, obj: bpy.types.Object, bm: bmesh.types.BMesh, h_islands: list):
        islands = [h_island.faces for h_island in h_islands]
        for island in islands:
            cluster = oCluster(context, obj, island, bm)
            cluster.f_orient = True
            cluster.type = "HARD"
            cluster.do_orient_to_world()

    def orient_to_near_axis(self, context: bpy.types.Context, h_islands, uv_layer):
        for h_island in h_islands:
            TrOrientProcessor._orient_loops(
                h_island.loops,
                uv_layer,
                h_island.bbox,
                ActiveUvImage(context).aspect,
                'AUTO',
                'CW'
            )


class ZUV_OT_TrHotspot(bpy.types.Operator):
    bl_idname = "uv.zenuv_fit_to_trim_hotspot"
    bl_label = "Hotspot Mapping"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Map Islands by matching Islands to predefined Trims from Trimsheet"

    trims_preselection: bpy.props.EnumProperty(
        name='Mode',
        items=[
            ("ALL", "All Trims", "Use all available Trims"),
            ("SELECTED", "Selected Trims", "Use only the selected Trims"),
        ],
        description='Use all Trims or selected Trims to map Islands',
        default='ALL')
    orient: bpy.props.EnumProperty(
        name='Orient',
        description='Perform some Island rotation before Hotspotting',
        items=[
            ("AS_IS", "As is", "No rotation at all"),
            ("WORLD", "Orient to World", "Orient to World"),
            ("ORIENT", "Orient to axis", "Auto orient island to nearest axis")
            ],
        default='AS_IS')
    priority: bpy.props.EnumProperty(
        name='Priority',
        description='''Prioritizing the similarities between the Trim and the Island.
Determines the criterion that takes effect first''',
        items=[
            ("ASPECT", "Aspect", "Based on the aspect ratio. Height to width."),
            ("AREA", "Area", "Based on the size of the area")
            ],
        default='ASPECT')
    area_match: bpy.props.EnumProperty(
        name='Area Matching',
        description='How to match Trim area with Island area',
        items=[
            ("AS_IS", "As is", "The island will be located in Trim with the closest area"),
            ("MAX", "Max", "The island will be located in Trim with the largest area. The highest possible Texel Density"),
            ("MIN", "Min", "The island will be located in Trim with the lowest area. The lowest possible Texel Density"),
            ("MANUAL", "Manual", "Value 1 equivalent to Area Matching 'As is'"),
            ],
        default='AS_IS')
    manual_scale: bpy.props.FloatProperty(
        name='Matching Scale',
        description='The value for manually adjusting the area matching scale',
        min=0.0,
        max=100,
        default=1.0)
    allow_rotation: bpy.props.BoolProperty(
        name='Allow Rotation',
        description='Allow Islands rotation by 90 degrees to achieve the best match',
        default=True)
    allow_rotation_variation: bpy.props.BoolProperty(
        name='Allow Rotation Variation',
        description='Allow random rotation of Trim by 180 degrees to increase variability',
        default=False)
    allow_location_variation: bpy.props.BoolProperty(
        name='Allow Location Variation',
        description='Allow islands to be placed in other trims with similar parameters',
        default=False)
    loc_var_offset: bpy.props.FloatProperty(
        name='Variation Offset',
        description='The amount by which the shift will be performed, if possible',
        default=0.0)
    fit_axis: bpy.props.EnumProperty(
        name='Fit Axis',
        description='Where to get the Fit Axis parameter',
        items=[
            ('AUTO', 'Automatic', 'Automatically detected axis for full dimensional compliance'),
            ('FROM_TRIM', 'Trim Settings', 'Use particular Trim properties from Trim Advanced Settings panel')
        ],
        default='AUTO')
    seed: bpy.props.IntProperty(
        name='Seed',
        description='Seed of variable island distribution in similar trims',
        default=132)
    keep_proportion: bpy.props.EnumProperty(
        name="Keep proportion",
        description="Keep proportion",
        items=[
            ('YES', 'Yes', 'Keep proportion'),
            ('NO', 'No', 'Do not keep proportion'),
            ('FROM_TRIM', 'Trim Settings', 'Use particular Trim properties from Trim Advanced Settings panel')
        ],
        default='YES')
    detect_radial: bpy.props.BoolProperty(
        name="Detect Radial",
        description="Detect Radial Islands and place them in Trims with Tag 'HOTSPOT Radial'",
        default=False)
    select_radials: bpy.props.BoolProperty(
        name='Select Radials',
        description='Select Radial Islands',
        default=False)
    aspect_precision: bpy.props.FloatProperty(
        name='Aspect Influence',
        description='Aspect influence for calculating the correspondence proportions between Trim and Island',
        default=0.0,
        step=0.1)
    cat: bpy.props.StringProperty(name='Category', default='HOTSPOT', options={'HIDDEN'})
    tag: bpy.props.StringProperty(name='Tag', default='Radial', options={'HIDDEN'})
    allow_extra_options: bpy.props.BoolProperty(default=False, name='Allow Variability:')

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    @classmethod
    def draw_variability(cls, props: bpy.types.OperatorProperties, layout: bpy.types.UILayout):
        # layout.label(text='Variability:')
        box = layout.box()
        box.prop(props, 'allow_rotation_variation')
        box.prop(props, 'allow_location_variation')
        offset_row = box.row()
        offset_row.enabled = props.allow_location_variation
        offset_row.prop(props, 'loc_var_offset')
        box.prop(props, 'detect_radial')

        if props.detect_radial:
            row = box.row()
            row.prop(props, 'cat')
            row.prop(props, 'tag')
            box.prop(props, 'select_radials')

        s_box = box.box()
        s_box.enabled = props.allow_location_variation or props.allow_rotation_variation
        s_box.prop(props, 'seed')

    @classmethod
    def draw_extra_options(cls, props: bpy.types.OperatorProperties, layout: bpy.types.UILayout):
        # layout.label(text='Extra:')
        box = layout.box()
        cls.draw_variability(props, box)

        # Draw Aspect Corrector
        row = box.row()
        row.alert = True if props.aspect_precision != 0.0 else False
        row.label(text='Wider')
        rc = row.row(align=True)
        rc.alignment = 'LEFT'
        rc.prop(props, 'aspect_precision')
        row = row.row()
        row.alignment = 'RIGHT'
        row.label(text='Higher')

    def draw_ex(self, layout: bpy.types.UILayout, context: bpy.types.Context):

        # Preprocess
        layout.label(text='Preprocess:')
        box = layout.box()
        box.prop(self, 'trims_preselection')
        box.prop(self, 'orient')
        box.prop(self, 'priority')

        # Settings
        layout.label(text='Settings:')
        box = layout.box()
        box.prop(self, 'allow_rotation')
        box.prop(self, 'keep_proportion')
        box.prop(self, 'fit_axis')

        # Area Matching
        layout.label(text='Area Matcing:')
        box = layout.box()
        box.prop(self, 'area_match')
        row = box.row()
        row.enabled = self.area_match == 'MANUAL'
        row.prop(self, 'manual_scale')

        # Extra Options
        layout.prop(self, 'allow_extra_options')
        if self.allow_extra_options:
            ZUV_OT_TrHotspot.draw_extra_options(self, layout)

    def draw(self, context):
        self.draw_ex(self.layout, context)

    def execute(self, context):
        self.cat = 'HOTSPOT'
        self.tag = 'Radial'
        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "There are no selected objects.")
            return {'CANCELLED'}

        p_trimsheet = ZuvTrimsheetUtils.getTrimsheet(context)
        if not len(p_trimsheet):
            self.report({'INFO'}, "There are no trims.")
            return {'CANCELLED'}

        if self.trims_preselection == 'SELECTED':
            if True not in [tr.selected for tr in p_trimsheet]:
                self.report({'WARNING'}, "There are no selected trims.")
                return {'FINISHED'}

        if not self.allow_extra_options:
            self.allow_rotation_variation = False
            self.allow_location_variation = False
            self.detect_radial = False
            self.aspect_precision = 0.0

        HSP = HotspotFactory(self.properties)
        i_counter = HSP.do_hotspotting(context, objs, p_trimsheet)

        if not i_counter:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        return {"FINISHED"}


classes = (
    ZUV_OT_TrHotspot,
)


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)
