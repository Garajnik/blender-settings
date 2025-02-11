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
from dataclasses import dataclass, field

from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel
from ZenUV.utils.blender_zen_utils import ZenPolls
from ZenUV.utils import get_uv_islands as island_util
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.utils.vlog import Log


@dataclass
class SelectedItems:

    selected_verts: list = field(default_factory=list)
    selected_edges: list = field(default_factory=list)
    selected_faces: list = field(default_factory=list)
    selected_loops: list = field(default_factory=list)

    def get_elements(self):
        return self.selected_verts, self.selected_edges, self.selected_faces


@dataclass
class ObjSelectionStorage:

    obj: bpy.types.Object
    bm: bmesh.types.BMesh
    uv_layer: bmesh.types.BMLayerItem
    selected_items: SelectedItems


class PackSelectionStorage:
    @classmethod
    def is_not_sync(cls, context: bpy.types.Context):
        return not (context.area.type == "VIEW_3D" or context.area.type == "IMAGE_EDITOR" and context.scene.tool_settings.use_uv_select_sync)

    @classmethod
    def store_selection(cls, p_unique_mesh_objects, b_is_not_sync, b_is_store_loops: bool = False):
        was_selection = list()
        for p_obj in p_unique_mesh_objects:
            me: bpy.types.Mesh = p_obj.data
            bm = bmesh.from_edit_mesh(me)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.active
            SI = SelectedItems()
            if uv_layer:
                if b_is_not_sync:
                    SI.selected_loops = cls._get_loops_selection(bm, uv_layer)
                else:
                    SI.selected_verts = [
                        item
                        for item in bm.verts
                        if not item.hide and item.select
                    ] if me.total_vert_sel else []

                    SI.selected_edges = [
                        item
                        for item in bm.edges
                        if not item.hide and item.select
                    ] if me.total_edge_sel else []

                    SI.selected_faces = [
                        item
                        for item in bm.faces
                        if not item.hide and item.select
                    ] if me.total_face_sel else []

                    if b_is_store_loops:
                        SI.selected_loops = cls._get_loops_selection(bm, uv_layer)

            was_selection.append(ObjSelectionStorage(obj=p_obj, bm=bm, uv_layer=uv_layer, selected_items=SI))

        return was_selection

    @classmethod
    def _get_loops_selection(cls, bm: bmesh.types.BMesh, uv_layer: bmesh.types.BMLayerItem):
        return [
                    (loop, loop[uv_layer].select_edge if ZenPolls.version_since_3_2_0 else None)
                    for face in bm.faces for loop in face.loops
                    if not face.hide and loop[uv_layer].select
                ]

    @classmethod
    def restore_selection(cls, context: bpy.types.Context, b_is_not_sync, was_selection: list, b_is_restore_loops: bool = False):
        if b_is_not_sync:
            for v in was_selection:
                if v.uv_layer:
                    cls._restore_loops_selection(v)
            v.bm.select_flush_mode()

        else:
            for v in was_selection:
                for elem in v.selected_items.get_elements():
                    for item in elem:
                        item.select = True
                v.bm.select_flush_mode()

            if b_is_restore_loops:
                if v.uv_layer:
                    for v in was_selection:
                        cls._restore_loops_selection(v)
                    v.bm.select_flush_mode()

    @classmethod
    def _restore_loops_selection(cls, v: ObjSelectionStorage):
        for loop, select_edge in v.selected_items.selected_loops:
            loop[v.uv_layer].select = True
            if ZenPolls.version_since_3_2_0:
                loop[v.uv_layer].select_edge = select_edge


@dataclass
class SoBject:


    obj_name: str = ''
    bm: bmesh.types.BMesh = None
    uv_layer: bmesh.types.BMLayerItem = None
    was_selection: list = field(default_factory=list)
    is_hidden_faces: bool = False
    f_pack_excluded_idxs: list = field(default_factory=list)

    def store_selection(self, context: bpy.types.Context) -> None:

        me = self._get_obj_data(context)
        bm = bmesh.from_edit_mesh(me)
        self.bm = bm
        self.uv_layer = bm.loops.layers.uv.verify()

        b_is_not_sync = not context.scene.tool_settings.use_uv_select_sync

        self.was_selection = PackSelectionStorage.store_selection([context.scene.objects[self.obj_name], ], b_is_not_sync=False, b_is_store_loops=b_is_not_sync)

    def _get_obj_data(self, context: bpy.types.Context):
        return context.scene.objects[self.obj_name].data

    def restore_selection(self, context: bpy.types.Context) -> None:
        """ Restore selected elements depending of Blender selection Mode """

        b_is_not_sync = not context.scene.tool_settings.use_uv_select_sync
        PackSelectionStorage.restore_selection(context, False, self.was_selection, b_is_not_sync)

    def hide_p_excluded(self, context: bpy.types.Context):
        p_facemap = self.get_p_excl_facemap()
        if p_facemap is None:
            return
        islands = [island for island in island_util.get_islands(context, self.bm) if True in [f[p_facemap] for f in island]]

        self.f_pack_excluded_idxs.extend([f.index for island in islands for f in island])
        self.bm.faces.ensure_lookup_table()
        for i in self.f_pack_excluded_idxs:
            self.bm.faces[i].hide_set(True)

    def unhide_p_excluded(self):
        if self.get_p_excl_facemap() is None:
            return
        self.bm.faces.ensure_lookup_table()
        for i in self.f_pack_excluded_idxs:
            self.bm.faces[i].hide_set(False)

    def get_p_excl_facemap(self):
        from ZenUV.utils.constants import PACK_EXCLUDED_FACEMAP_NAME
        return self.bm.faces.layers.int.get(PACK_EXCLUDED_FACEMAP_NAME, None)

    def is_pack_excluded_present(self):
        p_facemap = self.get_p_excl_facemap()
        if p_facemap is None:
            return False
        else:
            self.bm.faces.ensure_lookup_table()
            return True in [f[p_facemap] for f in self.bm.faces]

    def check_is_hidden_faces(self):
        if get_prefs().packEngine == "UVPACKER":
            self.is_hidden_faces = True in [f.hide for f in self.bm.faces] or self.is_pack_excluded_present()
            print(f'{self.is_hidden_faces = }')


class ObjsStorage:


    def __init__(self) -> None:
        self.objs: list = []
        self.is_sync_mode: bool = None
        self.selection_mode: str = None  # in ['EDGE', 'FACE', 'VERTEX']
        self.marker_face_idxs: list = []

    def clear(self) -> None:
        self.objs.clear()
        self.is_sync_mode = None
        self.selection_mode = None
        self.marker_face_idxs.clear()

    def is_hidden_faces_in_objects(self) -> bool:
        return True in [o.is_hidden_faces for o in self.objs]

    def hide_pack_excluded(self, context: bpy.types.Context):
        for s_obj in self.objs:
            s_obj.hide_p_excluded(context)

    def unhide_pack_excluded(self) -> None:
        if self.is_unhide_allowed():
            for s_obj in self.objs:
                s_obj.unhide_p_excluded()

    def is_unhide_allowed(self):
        return not get_prefs().packEngine == "UVPACKER"

    def remove_marker_faces(self):
        if len(self.marker_face_idxs):
            bmesh.ops.delete(self.objs[0].bm, geom=[self.objs[0].bm.faces[i] for i in self.marker_face_idxs], context='FACES')

    def collect_objects(self, context: bpy.types.Context) -> bool:

        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)

        if not objs:
            return False
        else:
            self.selection_mode = self.check_selection_mode(context)
            self.is_sync_mode = context.space_data.type == 'VIEW_3D' \
                or context.space_data.type == 'IMAGE_EDITOR' \
                and context.scene.tool_settings.use_uv_select_sync is True

            for obj in objs:
                s_obj = SoBject(obj.name)
                s_obj.store_selection(context)
                s_obj.check_is_hidden_faces()
                self.objs.append(s_obj)
        return True

    def restore_selection_all_objects(self, context: bpy.types.Context) -> None:
        if not get_prefs().packEngine == "UVPACKER":
            for s_obj in self.objs:  # type: SoBject
                s_obj.restore_selection(context)

    def check_selection_mode(self, context: bpy.types.Context) -> str:
        if context.tool_settings.mesh_select_mode[:] == (False, True, False):
            return 'EDGE'
        elif context.tool_settings.mesh_select_mode[:] == (False, False, True):
            return 'FACE'
        return 'VERTEX'

    def select_islands(self, context) -> None:
        from ZenUV.utils.generic import select_loops
        if context.area.type == "IMAGE_EDITOR" and not context.scene.tool_settings.use_uv_select_sync:
            for obj in self.objs:
                bm = obj.bm
                uv_layer = bm.loops.layers.uv.verify()
                select_loops(island_util.get_island(context, bm, uv_layer), uv_layer, state=True)
                bm.select_flush_mode()
        else:
            for obj in self.objs:
                bm = obj.bm
                uv_layer = bm.loops.layers.uv.verify()
                islands = island_util.get_island(context, bm, uv_layer)
                for island in islands:
                    for f in island:
                        f.select_set(True)
                if not context.scene.tool_settings.use_uv_select_sync:
                    select_loops(islands, uv_layer, state=True)

                bm.select_flush_mode()


class PackUtils:

    @classmethod
    def resolve_pack_selected_only(
            cls,
            context: bpy.types.Context,
            addon_prefs: bpy.types.AddonPreferences,
            Storage: ObjsStorage,
            set_sel_only: bool = False) -> None:

        if set_sel_only:
            cls.bpy_select_by_context(context, action='SELECT')
        else:
            if not addon_prefs.packSelectedIslOnly:
                cls.bpy_select_by_context(context, action='SELECT')
            else:
                Storage.select_islands(context)

    @classmethod
    def bpy_select_by_context(cls, context: bpy.types.Context, action: str = 'DESELECT'):
        if not context.scene.tool_settings.use_uv_select_sync:
            if action == 'SELECT':
                bpy.ops.mesh.select_all(action=action)
                bpy.ops.uv.select_all(action=action)
            else:
                bpy.ops.uv.select_all(action=action)
                bpy.ops.mesh.select_all(action=action)
        else:
            bpy.ops.mesh.select_all(action=action)