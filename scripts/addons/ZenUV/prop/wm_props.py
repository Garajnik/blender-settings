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

# Copyright 2023, Alex Zhornyak, alexander.zhornyak@gmail.com

import bpy

import numpy as np
from dataclasses import dataclass
from timeit import default_timer as timer

from ZenUV.utils.vlog import Log
from ZenUV.ops.event_service import get_blender_event
from ZenUV.ops.texel_density.td_props import TdProps


@dataclass
class TimeDataUVMap:
    time: float = 0.0
    idx: int = -1

    obj = None
    literal_id = 'zenuv_uvmap_time_data'


class ZuvUVMeshGroup(bpy.types.PropertyGroup):
    mesh: bpy.props.PointerProperty(
        type=bpy.types.Mesh
    )

    obj: bpy.props.PointerProperty(
        type=bpy.types.Object
    )


class ZuvUVMapWrapper(bpy.types.PropertyGroup):
    select: bpy.props.BoolProperty(
        name='Select',
        default=False
    )

    def _update_name_ex(self, context):
        bpy.app.driver_namespace[TimeDataUVMap.literal_id] = TimeDataUVMap()

    def _set_name_ex(self, value):
        was_name = self.name

        for me_group in self.mesh_groups:
            p_uv = me_group.mesh.uv_layers.get(was_name, None)
            if p_uv:
                if p_uv.name != value:
                    p_uv.name = value

    name_ex: bpy.props.StringProperty(
        name='Name',
        description='Set UV map name of the selected objects',
        get=lambda self: self.name,
        set=_set_name_ex,
        update=_update_name_ex,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def _set_name_ex_active(self, value):
        was_name = self.name

        p_act_obj = bpy.context.active_object
        if p_act_obj and p_act_obj.type == 'MESH':
            p_uv = p_act_obj.data.uv_layers.get(was_name, None)
            if p_uv:
                if p_uv.name != value:
                    p_uv.name = value

    name_ex_active: bpy.props.StringProperty(
        name='Name',
        description='Set UV map name of the active object',
        get=lambda self: self.name,
        set=_set_name_ex_active,
        update=_update_name_ex,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def _set_name_ex_auto(self, value):
        p_scene_props = bpy.context.scene.zen_uv.adv_maps
        if p_scene_props.sync_adv_maps:
            self._set_name_ex(value)
        else:
            self._set_name_ex_active(value)

    name_ex_auto: bpy.props.StringProperty(
        name='Name',
        description='UV map name',
        get=lambda self: self.name,
        set=_set_name_ex_auto,
        update=_update_name_ex,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def _get_active_render(self):
        if len(self.mesh_groups) > 0:
            p_uv = self.mesh_groups[0].mesh.uv_layers.get(self.name, None)
            if p_uv:
                return p_uv.active_render
        return False

    def _set_active_render(self, value):
        for me_group in self.mesh_groups:
            p_uv = me_group.mesh.uv_layers.get(self.name, None)
            if p_uv:
                if not p_uv.active_render:
                    # Always set to True as in Blender
                    p_uv.active_render = True

    def _set_active_render_active(self, value):
        p_act_obj = bpy.context.active_object
        if p_act_obj and p_act_obj.type == 'MESH':
            p_uv = p_act_obj.data.uv_layers.get(self.name, None)
            if p_uv:
                p_uv.active_render = True

    active_render_ex: bpy.props.BoolProperty(
        name='Active Render',
        description='Set the UV map as active for rendering of the selected objects',
        get=_get_active_render,
        set=_set_active_render,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    active_render_ex_active: bpy.props.BoolProperty(
        name='Active Render',
        description='Set the UV map as active for rendering of the active object',
        get=_get_active_render,
        set=_set_active_render_active,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    mesh_groups: bpy.props.CollectionProperty(
        type=ZuvUVMeshGroup
    )


class ZuvObjUVGroup(bpy.types.PropertyGroup):
    uvmaps: bpy.props.CollectionProperty(
        name='Selected Object UVS',
        type=ZuvUVMapWrapper
    )

    lock_selection_by_index: bpy.props.BoolProperty(
        name='Lock Selection by Index',
        default=False
    )

    selected_meshes: bpy.props.CollectionProperty(
        type=ZuvUVMeshGroup
    )

    active_uv_name: bpy.props.StringProperty(
        name='Active UV Name',
        default=''
    )

    active_mesh_name: bpy.props.StringProperty(
        name='Active Mesh Name',
        default=''
    )

    def _update_uv_object(self, context: bpy.types.Context):
        if self.active_uv_object and self.active_uv_object.type == 'MESH':
            if self.active_uv_object and context.view_layer.objects.active != self.active_uv_object:
                context.view_layer.objects.active = self.active_uv_object
                self.active_uv_object.select_set(True)

    active_uv_object: bpy.props.PointerProperty(
        name='Active UV Object',
        type=bpy.types.Object,
        options={'HIDDEN', 'SKIP_SAVE'},
        update=_update_uv_object
    )

    def _get_selected_index(self):
        return self.get('selected_index', -1)

    def _set_selected_index(self, value):
        p_event = get_blender_event(force=True)

        mode = 'ACTIVE'

        b_ctrl = p_event.get('ctrl', False)
        b_shift = p_event.get('shift', False)

        if b_shift and b_ctrl:
            mode = 'TOGGLE_ALL'
        elif b_ctrl:
            mode = 'TOGGLE'
        elif b_shift:
            mode = 'EXTEND'

        try:
            n_count = len(self.uvmaps)
            if n_count > 0:
                if mode == 'ACTIVE':
                    arr_selected = [False] * n_count
                    arr_selected[value] = True
                    self.uvmaps.foreach_set("select", arr_selected)
                    self['selected_index'] = value
                elif mode == 'EXTEND':
                    start_idx = min(max(0, self.get('selected_index', -1)), max(0, value))
                    end_idx = max(max(0, self.get('selected_index', -1)), max(0, value))
                    for idx in range(start_idx, end_idx + 1):
                        self.uvmaps[idx].select = True
                    self['selected_index'] = value
                elif mode == 'TOGGLE':
                    self.uvmaps[value].select = not self.uvmaps[value].select
                    if self.uvmaps[value].select:
                        self['selected_index'] = value
                elif mode == 'TOGGLE_ALL':
                    arr = np.empty(n_count, 'b')
                    self.uvmaps.foreach_get('select', arr)

                    arr.fill(False if arr.all() else True)

                    self.uvmaps.foreach_set('select', arr)

        except Exception as e:
            Log.error('SET TRIM INDEX:', str(e))

    def _update_selected_index_time_data(self, context: bpy.types.Context):
        p_last_time_data = bpy.app.driver_namespace.get(TimeDataUVMap.literal_id, TimeDataUVMap())  # type: TimeDataUVMap

        if timer() - p_last_time_data.time < 0.3 and self.selected_index == p_last_time_data.idx:
            p_last_time_data.obj = context.active_object
        else:
            p_last_time_data.obj = None
        p_last_time_data.time = timer()
        p_last_time_data.idx = self.selected_index
        bpy.app.driver_namespace[TimeDataUVMap.literal_id] = p_last_time_data

    def _update_selected_index(self, context: bpy.types.Context):
        self._update_selected_index_time_data(context)

        if self.selected_index in range(len(self.uvmaps)):
            p_uv_map = self.uvmaps[self.selected_index]
            for me_group in p_uv_map.mesh_groups:
                me = me_group.mesh
                idx = me.uv_layers.find(p_uv_map.name)
                if idx != -1 and idx != me.uv_layers.active_index:
                    me.uv_layers.active_index = idx

    selected_index: bpy.props.IntProperty(
        name='Selected Object UVS Index',
        default=-1,
        get=_get_selected_index,
        set=_set_selected_index,
        update=_update_selected_index
    )

    def _update_selected_index_active(self, context: bpy.types.Context):
        self._update_selected_index_time_data(context)

        p_act_obj = context.active_object
        if p_act_obj and p_act_obj.type == 'MESH':
            if self.selected_index in range(len(self.uvmaps)):
                p_uv_map = self.uvmaps[self.selected_index]

                me = p_act_obj.data
                idx = me.uv_layers.find(p_uv_map.name)
                if idx != -1 and idx != me.uv_layers.active_index:
                    me.uv_layers.active_index = idx

    selected_index_active: bpy.props.IntProperty(
        name='Selected Object UVS Index',
        default=-1,
        get=_get_selected_index,
        set=_set_selected_index,
        update=_update_selected_index_active
    )

    def _update_selected_index_auto(self, context: bpy.types.Context):
        p_scene_props = context.scene.zen_uv.adv_maps
        if p_scene_props.sync_adv_maps:
            self._update_selected_index(context)
        else:
            self._update_selected_index_active(context)

    selected_index_auto: bpy.props.IntProperty(
        name='Selected Object UVS Index',
        get=_get_selected_index,
        set=_set_selected_index,
        update=_update_selected_index_auto
    )

    def get_active_uvmap(self) -> ZuvUVMapWrapper:
        if self.selected_index in range(len(self.uvmaps)):
            return self.uvmaps[self.selected_index]
        return None

    def get_active_render_uvmap(self) -> ZuvUVMapWrapper:
        for p_uv_map in self.uvmaps:
            if p_uv_map.active_render_ex:
                return p_uv_map
        return None


class ZuvWMDrawGroup(bpy.types.PropertyGroup):
    draw_auto_update: bpy.props.BoolProperty(
        name='Auto Update Draw',
        description='Update draw cache every time when mesh is changed',
        default=True
    )


class ZuvWMTexelDensityGroup(bpy.types.PropertyGroup):
    def get_td_limits(self):
        p_limits = self.get('td_limits', (0.0, 0.0))
        if p_limits[0] > p_limits[1]:
            return p_limits[0], p_limits[0]
        else:
            return p_limits

    def set_td_limits(self, value):
        self['td_limits'] = value

    td_limits: bpy.props.FloatVectorProperty(
        name='Limits',
        description='',
        size=2,
        default=(0.0, 0.0),
        min=0.0,
        soft_min=0.0,
        subtype='COORDINATES',
        get=get_td_limits,
        set=set_td_limits
    )

    td_limits_ui: bpy.props.FloatVectorProperty(
        name='Limits',
        description='',
        size=2,
        default=(0.0, 0.0),
        min=0.0,
        soft_min=0.0,
        subtype='COORDINATES',
        get=get_td_limits,
        set=set_td_limits,
        update=TdProps.update_td_draw_force
    )

    def get_balanced_checker(self):
        return self.get('balanced_checker', 47.59)

    def set_balanced_checker(self, value):
        self['balanced_checker'] = value

    balanced_checker: bpy.props.FloatProperty(
        name='TD Checker',
        description='Texel Density value used for Show TD Balanced method',
        min=0.001,
        get=get_balanced_checker,
        set=set_balanced_checker,
        precision=2
    )

    balanced_checker_ui: bpy.props.FloatProperty(
        name='TD Checker',
        description='Texel Density value used for Show TD Balanced method',
        min=0.001,
        get=get_balanced_checker,
        set=set_balanced_checker,
        precision=2,
        update=TdProps.update_td_draw_force
    )


class ZUV_WMProps(bpy.types.PropertyGroup):
    obj_uvs: bpy.props.PointerProperty(
        type=ZuvObjUVGroup
    )

    draw_props: bpy.props.PointerProperty(
        type=ZuvWMDrawGroup
    )

    td_props: bpy.props.PointerProperty(
        type=ZuvWMTexelDensityGroup
    )
