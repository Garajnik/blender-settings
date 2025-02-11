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

# Copyright 2023, Alex Zhornyak

import bpy

from dataclasses import dataclass, field

from ZenUV.utils.vlog import Log
from ZenUV.utils.blender_zen_utils import update_areas_in_view3d

# Tool Operators
from .tool_ops import (
    ZUV_OT_ToolTrimHandle,
    ZUV_OT_ToolAreaUpdate,
    ZUV_OT_ToolExitCreate,
    ZUV_OT_ToolScreenZoom,
    ZUV_OT_ToolScreenPan,
    ZUV_OT_ToolScreenReset,
    ZUV_OT_ToolScreenSelector,
    ZUV_OT_TrimScrollFit,
    ZUV_OT_TrimActivateTool
)

# Custom Gizmos
from .view3d_texture_gizmo import ZuvTextureGizmo
from .view3d_trim import (
    ZuvTrimCageGizmo,
    ZuvTrimSelectGizmo,
    ZuvTrimAlignGizmo,
    ZuvTrimFitFlipGizmo,
    VIEW2D_GT_zenuv_trim_viewport_select)
from .view3d_transform_line import VIEW2D_GT_zenuv_transform_line
from .view3d_text import VIEW2D_GT_zenuv_tool_text

from .uv.uv_trim import (
    UV_GT_zenuv_trim_select,
    UV_GT_zenuv_trim_box_select,
    UV_GT_zenuv_trim_select_background)
from .uv.uv_create import UV_GT_zenuv_trim_create
from .uv.uv_align import UV_GT_zenuv_trim_align
from .uv.uv_fit_flip import UV_GT_zenuv_trim_fitflip
from .uv.uv_arrow import UV_GT_zenuv_arrow
from .uv.uv_transform_line import UV_GT_zenuv_transform_line

# Gizmo Groups
from .view3d_move import ZUV_GGT_3DVTransformMove
from .view3d_scale import ZUV_GGT_3DVTransformScale, ZUV_GGT_2DVTransformScale, ZuvTrimScaleGizmo
from .view3d_rotate import ZUV_GGT_3DVTransformRot
from .view3d_text import ZUV_GGT_2DVToolText

from .uv.uv_move import ZUV_GGT_UVTransformMove
from .uv.uv_scale import ZUV_GGT_UVTransformScale
from .uv.uv_rotate import ZUV_GGT_UVTransformRot
from .uv.uv_create import ZUV_GGT_UVTrimCreate
from .uv.uv_generic import ZUV_GGT_UVTrimGeneric, ZUV_GGT_UVTrimDisplay

# Tools
from .view3d_tool import Zuv3DVWorkSpaceTool
from .uv.uv_tool import ZuvUVWorkSpaceTool

classes = (
    # Operators
    ZUV_OT_ToolTrimHandle,
    ZUV_OT_ToolAreaUpdate,
    ZUV_OT_ToolExitCreate,
    ZUV_OT_ToolScreenZoom,
    ZUV_OT_ToolScreenPan,
    ZUV_OT_ToolScreenReset,
    ZUV_OT_ToolScreenSelector,
    ZUV_OT_TrimScrollFit,
    # Call from UI Operator
    ZUV_OT_TrimActivateTool,

    # 3D
    ZuvTextureGizmo,
    ZuvTrimAlignGizmo,
    ZuvTrimSelectGizmo,
    ZuvTrimFitFlipGizmo,
    ZuvTrimCageGizmo,
    ZuvTrimScaleGizmo,

    # 3D GizmoGroups
    ZUV_GGT_3DVTransformMove,
    ZUV_GGT_3DVTransformScale,
    ZUV_GGT_3DVTransformRot,

    # 2D View3D Gizmos
    VIEW2D_GT_zenuv_transform_line,
    ZUV_GGT_2DVTransformScale,

    VIEW2D_GT_zenuv_tool_text,
    ZUV_GGT_2DVToolText,

    VIEW2D_GT_zenuv_trim_viewport_select,

    # UV
    UV_GT_zenuv_trim_select,
    UV_GT_zenuv_trim_create,
    UV_GT_zenuv_trim_align,
    UV_GT_zenuv_trim_fitflip,
    UV_GT_zenuv_transform_line,
    UV_GT_zenuv_arrow,
    UV_GT_zenuv_trim_box_select,
    UV_GT_zenuv_trim_select_background,

    # UV GizmoGroups
    ZUV_GGT_UVTransformMove,
    ZUV_GGT_UVTrimCreate,
    ZUV_GGT_UVTrimGeneric,
    ZUV_GGT_UVTransformScale,
    ZUV_GGT_UVTransformRot,
    ZUV_GGT_UVTrimDisplay
)


@dataclass
class NotifyToolCache:
    UV: str = ''
    VIEW_3D: str = ''

    PREV_UV: str = ''
    PREV_VIEW_3D: str = ''


@dataclass
class NotifyToolCacheModes:
    OBJECT: NotifyToolCache = field(default_factory=NotifyToolCache)
    EDIT_MESH: NotifyToolCache = field(default_factory=NotifyToolCache)


_notify_tool_cache = NotifyToolCacheModes()


zenuv_handle_subcribe_to = None


@bpy.app.handlers.persistent
def zenuv_notify_tool_changed(handle):
    try:
        ctx = bpy.context
        s_mode = ctx.mode

        if s_mode in {'EDIT_MESH', 'OBJECT'}:

            from ZenUV.prop.zuv_preferences import get_prefs

            global _notify_tool_cache

            p_mode_cache = getattr(_notify_tool_cache, s_mode)  # type: NotifyToolCache

            _id_UV = getattr(ctx.workspace.tools.from_space_image_mode('UV', create=False), 'idname', None)
            _id_3D = getattr(ctx.workspace.tools.from_space_view3d_mode(s_mode, create=False), 'idname', None)

            b_UV_tool = None
            b_3D_tool = None

            if _id_UV and isinstance(_id_UV, str):
                if p_mode_cache.UV != _id_UV:
                    p_mode_cache.PREV_UV = p_mode_cache.UV
                    p_mode_cache.UV = _id_UV
                    b_UV_tool = p_mode_cache.UV == ZuvUVWorkSpaceTool.bl_idname

            if _id_3D and isinstance(_id_3D, str):
                if p_mode_cache.VIEW_3D != _id_3D:
                    p_mode_cache.PREV_VIEW_3D = p_mode_cache.VIEW_3D
                    p_mode_cache.VIEW_3D = _id_3D
                    b_3D_tool = p_mode_cache.VIEW_3D == Zuv3DVWorkSpaceTool.bl_idname

            addon_prefs = get_prefs()
            if addon_prefs.trimsheet.auto_highlight == 'DEFAULT':
                p_scene = ctx.scene

                if b_UV_tool is not None and p_scene.zen_uv.ui.uv_tool.display_trims != b_UV_tool:
                    p_scene.zen_uv.ui.uv_tool.display_trims = b_UV_tool
                if b_3D_tool is not None and p_scene.zen_uv.ui.view3d_tool.display_trims != b_3D_tool:
                    p_scene.zen_uv.ui.view3d_tool.display_trims = b_3D_tool
    except Exception as e:
        Log.error('TOOL CHANGED:', e)


@bpy.app.handlers.persistent
def zenuv_notify_object_mode_changed(handle):
    from ZenUV.prop.zuv_preferences import get_prefs
    addon_prefs = get_prefs()
    if addon_prefs.draw_auto_disable:
        p_scene = bpy.context.scene
        if p_scene:
            if p_scene.zen_uv.ui.draw_mode_UV != 'NONE':
                p_scene.zen_uv.ui.draw_mode_UV = 'NONE'
            if p_scene.zen_uv.ui.draw_mode_3D != 'NONE':
                p_scene.zen_uv.ui.draw_mode_3D = 'NONE'


@bpy.app.handlers.persistent
def zenuv_notify_tool_settings_uv_sync_changed(handle):
    # Blender does not inform about UV Sync Select is changed,
    # but there may be possible draw operations in View3D that requires update
    update_areas_in_view3d(bpy.context)


@bpy.app.handlers.persistent
def zenuv_tool_load_scene_handler(dummy):

    p_scene = bpy.context.scene
    if p_scene:
        if p_scene.zen_uv.ui.draw_mode_UV != 'NONE':
            p_scene.zen_uv.ui.draw_mode_UV = 'NONE'
        if p_scene.zen_uv.ui.draw_mode_3D != 'NONE':
            p_scene.zen_uv.ui.draw_mode_3D = 'NONE'

    global _notify_tool_cache
    _notify_tool_cache = NotifyToolCacheModes()

    _subscribe_rna_common_types()


def _subscribe_rna_common_types():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.WorkSpace, 'tools'),
        owner=zenuv_handle_subcribe_to,
        args=(zenuv_handle_subcribe_to,),
        notify=zenuv_notify_tool_changed,
        options={"PERSISTENT", }
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, 'mode'),
        owner=zenuv_handle_subcribe_to,
        args=(zenuv_handle_subcribe_to,),
        notify=zenuv_notify_object_mode_changed,
        options={"PERSISTENT", }
    )

    bpy.msgbus.subscribe_rna(
        key=(bpy.types.ToolSettings, 'use_uv_select_sync'),
        owner=zenuv_handle_subcribe_to,
        args=(zenuv_handle_subcribe_to,),
        notify=zenuv_notify_tool_settings_uv_sync_changed,
        options={"PERSISTENT", }
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    try:
        bpy.utils.register_tool(Zuv3DVWorkSpaceTool)
        bpy.utils.register_tool(ZuvUVWorkSpaceTool)
    except Exception as e:
        Log.error('Register tool:', e)

    global zenuv_handle_subcribe_to
    if zenuv_handle_subcribe_to is None:
        zenuv_handle_subcribe_to = object()
        _subscribe_rna_common_types()

    if zenuv_tool_load_scene_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(zenuv_tool_load_scene_handler)


def unregister():

    if zenuv_tool_load_scene_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(zenuv_tool_load_scene_handler)

    global zenuv_handle_subcribe_to
    if zenuv_handle_subcribe_to is not None:
        bpy.msgbus.clear_by_owner(zenuv_handle_subcribe_to)
        zenuv_handle_subcribe_to = None

    try:
        bpy.utils.unregister_tool(ZuvUVWorkSpaceTool)
        bpy.utils.unregister_tool(Zuv3DVWorkSpaceTool)
    except Exception as e:
        Log.error('Unregister tool:', e)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
