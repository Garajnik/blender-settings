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

import sys
import os
from json import loads, dumps
import bpy

from .files import update_files_info, load_checker_image

from .checker import (
    zen_checker_image_update,
    get_materials_with_overrider,
)
from .constants import (
    ZEN_GLOBAL_OVERRIDER_NAME,
    ZEN_IMAGE_NODE_NAME,
    ZEN_TILER_NODE_NAME,
    ZEN_OFFSETTER_NODE_NAME,
    ADDON_NAME
)


resolutions_x = []
resolutions_y = []
values_x = []
values_y = []


class ZTCHK_AddonPreferences(bpy.types.AddonPreferences):
    """ Zen Checker Addon Preferences """
    bl_idname = ADDON_NAME


    def get_files_dict(self, context):
        try:
            if self.files_dict == "":
                self.files_dict = dumps(update_files_info(self.assetspath))
            files_dict = loads(self.files_dict)
            return files_dict
        except Exception:
            print("Warning!", sys.exc_info()[0], "occurred.")
            self.files_dict = dumps(update_files_info(self.assetspath))
            return None

    def get_x_res_list(self, context):
        """ Get resolutions list for files from files_dict """
        files_dict = self.get_files_dict(context)
        if files_dict:
            # Update info in resolutions_x list
            values_x.clear()
            for image in files_dict:
                value = files_dict[image]["res_x"]
                if value not in values_x:
                    values_x.append(value)
            values_x.sort()
            identifier = 0
            resolutions_x.clear()
            for value in values_x:
                resolutions_x.append((str(value), str(value), "", identifier))
                identifier += 1
            return resolutions_x
        return [('None', 'None', '', 0), ]

    def get_y_res_list(self, context):
        """ Fills resolutions_y depend on current value of SizeX """
        files_dict = self.get_files_dict(context)
        if files_dict:
            res_x = self.SizesX
            if res_x and res_x.isdigit():
                res_x = int(res_x)
                # If axes locked - return same value as Resolution X
                if self.lock_axes:
                    return [(str(res_x), str(res_x), "", 0)]
                identifier = 0
                values_y.clear()
                resolutions_y.clear()
                for image in files_dict:
                    value = files_dict[image]["res_y"]
                    if files_dict[image]["res_x"] == res_x and value not in values_y:
                        values_y.append(value)
                        resolutions_y.append((str(value), str(value), "", identifier))
                        identifier += 1
            if resolutions_y:
                return resolutions_y
        return [('None', 'None', '', 0), ]

    def zen_tex_chkrecker_image_items(self, context):
        from .utils import get_checker_previews
        files_dict = self.get_files_dict(context)
        if files_dict:
            files = []
            identifier = 0
            # If filter disabled - return all images from dict
            if not self.chk_rez_filter:
                for image in files_dict:
                    icon_id = 'BLANK1'
                    try:
                        icon_id = get_checker_previews()[image].icon_id
                    except Exception as e:
                        print(str(e))
                    files.append((image, image, "", icon_id, identifier))
                    identifier += 1
                return files

            res_x = self.SizesX
            res_y = self.SizesY
            if res_x and res_y and res_x.isdigit() and res_y.isdigit():
                res_x = int(res_x)
                res_y = int(res_y)
                values = []
                for image in files_dict:
                    if files_dict[image]["res_x"] == res_x \
                            and files_dict[image]["res_y"] == res_y \
                            and image not in values:
                        values.append(image)

                        icon_id = 'BLANK1'
                        try:
                            icon_id = get_checker_previews()[image].icon_id
                        except Exception as e:
                            print(str(e))

                        if self.chk_orient_filter:
                            if "orient" in image:
                                files.append((image, image, "", icon_id, identifier))
                                identifier += 1
                        else:
                            files.append((image, image, "", icon_id, identifier))
                            identifier += 1
            if files:
                return files
        return [('None', 'None', '', 0), ]

    def dynamic_update_function(self, context):
        if self.dynamic_update and get_materials_with_overrider(bpy.data.materials):
            self.checker_presets_update_function(context)

    def update_x_res(self, context):
        addon_prefs = get_prefs()
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def update_y_res(self, context):
        addon_prefs = get_prefs()
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def update_orient_switch(self, context):
        addon_prefs = get_prefs()
        if self.chk_orient_filter:
            addon_prefs["SizesX"] = 1
            addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        self.dynamic_update_function(context)

    def dynamic_update_function_overall(self, context):
        addon_prefs = get_prefs()
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        if self.dynamic_update:
            materials_with_overrider = get_materials_with_overrider(bpy.data.materials)
            # print("Mats with overrider in bpy.data: ", materials_with_overrider)
            if materials_with_overrider:
                self.checker_presets_update_function(context)

    # def show_checker_in_uv_layout(self, context):
    #     materials_with_overrider = get_materials_with_overrider(get_materials_from_objects(context, context.selected_objects))
    #     if materials_with_overrider:
    #         image = bpy.data.images.get(self.ZenCheckerPresets)
    #         # update_image_in_uv_layout(context, image)

    def checker_presets_update_function(self, context):
        image = bpy.data.images.get(self.ZenCheckerImages)
        if image:
            zen_checker_image_update(context, image)
        else:
            # print("Image not Loaded. Load image ", self.ZenCheckerPresets)
            image = load_checker_image(context, self.ZenCheckerImages)
            if image:
                zen_checker_image_update(context, image)
        # self.show_checker_in_uv_layout(context)

    def update_assetspath(self, context):
        self.files_dict = dumps(update_files_info(self.assetspath))

    assetspath: bpy.props.StringProperty(
        name="Checker Library",
        subtype='DIR_PATH',
        default=os.path.join(os.path.dirname(__file__), "images"),
        update=update_assetspath
    )

    files_dict: bpy.props.StringProperty(
        name="Zen Checker Files Dict",
        default=""
    )

    dynamic_update: bpy.props.BoolProperty(
        name="Auto Sync Checker",
        description="""Automatically sync selected Checker Texture
 with Viewport""",
        default=True
    )

    ZenCheckerPresets: bpy.props.EnumProperty(
        name="Zen Texture Checker Presets",
        description="Presets of Zen UV Default Checker",
        items=[
            ('Zen-UV-512-colour.png', 'Zen Color 512x512', '', 1),
            ('Zen-UV-1K-colour.png', 'Zen Color 1024x1024', '', 2),
            ('Zen-UV-2K-colour.png', 'Zen Color 2048x2048', '', 3),
            ('Zen-UV-4K-colour.png', 'Zen Color 4096x4096', '', 4),
            ('Zen-UV-512-mono.png', 'Zen Mono 512x512', '', 5),
            ('Zen-UV-1K-mono.png', 'Zen Mono 1024x1024', '', 6),
            ('Zen-UV-2K-mono.png', 'Zen Mono 2048x2048', '', 7),
            ('Zen-UV-4K-mono.png', 'Zen Mono 4096x4096', '', 8)],
        default="Zen-UV-1K-colour.png",
        update=checker_presets_update_function
    )

    # ShowCheckerInUVLayout: bpy.props.BoolProperty(
    #     name="Show Image In UV Editor",
    #     description="Show Image In UV Editor Toggle",
    #     default=True,
    #     update=show_checker_in_uv_layout
    # )

    lock_axes: bpy.props.BoolProperty(
        name="Lock",
        description="Lock resolution fields",
        default=True,
        update=update_x_res
    )

    chk_rez_filter: bpy.props.BoolProperty(
        name="Filter",
        description="Resolution variables filtration",
        default=False,
        update=update_x_res
    )

    chk_orient_filter: bpy.props.BoolProperty(
        name="Orient Filter",
        description="Orient Checker Filter",
        default=False,
        update=update_orient_switch
    )

    SizesX: bpy.props.EnumProperty(
        name="X Res",
        description="X resolution",
        items=get_x_res_list,
        update=update_x_res
    )

    SizesY: bpy.props.EnumProperty(
        name="Y Res",
        description="Y resolution",
        items=get_y_res_list,
        update=update_y_res
    )

    ZenCheckerImages: bpy.props.EnumProperty(
        name="",
        items=zen_tex_chkrecker_image_items,
        update=checker_presets_update_function
    )


class ZTCHK_SceneLevelProperties(bpy.types.PropertyGroup):

    def update_interpolation(self, context):
        interpolation = {True: 'Linear', False: 'Closest'}
        _overrider = None
        if bpy.data.node_groups.items():
            _overrider = bpy.data.node_groups.get(ZEN_GLOBAL_OVERRIDER_NAME, None)
        if _overrider:
            if hasattr(_overrider, "nodes"):
                image_node = _overrider.nodes.get(ZEN_IMAGE_NODE_NAME)
                if image_node:
                    # image_node.image = _image
                    image_node.interpolation = interpolation[get_scene_props(context).tex_checker_interpolation]

    tex_checker_interpolation: bpy.props.BoolProperty(
        name='Interpolation',
        default=True,
        description='Texture checker interpolation',
        update=update_interpolation,
        options=set()
    )

    def update_checker_tiling(self, context):
        _overrider = None
        if bpy.data.node_groups.items():
            _overrider = bpy.data.node_groups.get(ZEN_GLOBAL_OVERRIDER_NAME, None)
        if _overrider:
            if hasattr(_overrider, "nodes"):
                tiler_node = _overrider.nodes.get(ZEN_TILER_NODE_NAME)
                if tiler_node:

                    tiler_node.inputs['Scale'].default_value = get_scene_props(context).tex_checker_tiling.to_3d()

    tex_checker_tiling: bpy.props.FloatVectorProperty(
        name="Tiling",
        size=2,
        default=(1.0, 1.0),
        subtype='XYZ',
        update=update_checker_tiling,
        options=set()
    )

    def update_checker_offset(self, context):
        _overrider = None
        if bpy.data.node_groups.items():
            _overrider = bpy.data.node_groups.get(ZEN_GLOBAL_OVERRIDER_NAME, None)
        if _overrider:
            if hasattr(_overrider, "nodes"):
                offsetter_node = _overrider.nodes.get(ZEN_OFFSETTER_NODE_NAME)
                if offsetter_node:
                    offsetter_node.outputs[0].default_value = get_scene_props(context).tex_checker_offset

    tex_checker_offset: bpy.props.FloatProperty(
        name="Offset",
        default=0.0,
        step=1,
        update=update_checker_offset,
        options=set()
    )
    prev_color_type: bpy.props.StringProperty(name="Color Type", default='MATERIAL')


def get_prefs() -> ZTCHK_AddonPreferences:
    """ Return Zen Texture Checker Addon Properties obj """
    return bpy.context.preferences.addons[ADDON_NAME].preferences


def get_scene_props(context: bpy.types.Context) -> ZTCHK_SceneLevelProperties:
    """ Return Zen Texture Checker Scene level Properties obj """
    return context.scene.zen_tex_chkr_props


def register_addon_preferences():
    from bpy.utils import register_class

    register_class(ZTCHK_AddonPreferences)
    register_class(ZTCHK_SceneLevelProperties)

    bpy.types.Scene.zen_tex_chkr_props = bpy.props.PointerProperty(type=ZTCHK_SceneLevelProperties)


def unregister_addon_preferences():
    from bpy.utils import unregister_class

    unregister_class(ZTCHK_AddonPreferences)
    unregister_class(ZTCHK_SceneLevelProperties)

    try:
        del bpy.types.Scene.zen_tex_chkr_props
    except Exception as e:
        ('UNREGISTER PROPS:', e)


if __name__ == '__main__':
    pass
