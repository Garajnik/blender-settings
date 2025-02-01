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

""" Zen Checker Files Pocessor """

from struct import unpack
import imghdr
import os
from shutil import copy
from json import dumps

import bpy
from bpy_extras.io_utils import ImportHelper
from .ui import zen_message

from .constants import ADDON_SHORT


def load_checker_image(context, _image):
    from .preferences import get_prefs
    addon_prefs = get_prefs()
    image_file = os.path.join(addon_prefs.assetspath, _image)
    current_image = bpy.data.images.get(_image)
    if current_image and not current_image.has_data:
        bpy.data.images.remove(current_image, do_unlink=True)
    if os.path.exists(image_file):
        bpy.data.images.load(image_file, check_existing=True)
        _image = bpy.data.images.get(_image, None)
        if _image is not None:
            return _image
        bpy.ops.wm.call_menu(name="ZUV_MT_ZenChecker_Popup")
        return None
    else:
        if _image != "None":
            print("Zen Checker: file not exist ", image_file)
            zen_message(context, message="File not exist:" + image_file, title="Zen Checker")
        return None


def get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = unpack('>ii', head[16:24])
        # elif imghdr.what(fname) == 'gif':
        #     width, height = unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0)  # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = unpack('>HH', fhandle.read(4))
            except Exception:  # IGNORE:W0703
                return
        else:
            return
        return width, height


def collect_image_names(path):
    """ Read files from Zen Checker .images directory """
    checker_images = []
    if os.path.exists(path):
        for _file in os.listdir(path=path):
            if _file.endswith(".png") or _file.endswith(".jpg"):
                checker_images.append(_file)
    else:
        print("Zen UV: Folder ../Images not exist")
    return checker_images


def update_files_info(path):
    """ Update info of files from Zen Checker .images directory """
    from .utils import get_checker_previews
    files_dict = dict()
    files = collect_image_names(path)
    if files:
        p_previews = get_checker_previews()
        p_previews.clear()

        for _file in files:
            # print("Update File Info:", _file)
            files_dict[_file] = dict()
            p_path = os.path.join(path, _file)
            files_dict[_file]["res_x"], files_dict[_file]["res_y"] = get_image_size(p_path)

            try:
                p_previews.load(_file, p_path, 'IMAGE')
            except Exception as e:
                print(f'Not_found -> {e}')

    # print(files_dict)
    return files_dict


class ZTCHK_OT_CollectImages(bpy.types.Operator):
    """ Zen UV Checker Collect files data """
    bl_idname = f"view3d.{ADDON_SHORT}_collect_images"
    bl_label = "Refresh Texture Library"
    bl_description = "Refresh Textures from Checker Library Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .preferences import get_prefs
        addon_prefs = get_prefs()
        path = addon_prefs.assetspath
        addon_prefs.files_dict = dumps(update_files_info(path))
        return {'FINISHED'}


class ZTCHK_OT_AppendCheckerFile(bpy.types.Operator, ImportHelper):
    bl_idname = f"view3d.{ADDON_SHORT}_append_checker_file"
    bl_label = "Load Your Texture"
    bl_description = """Open File Browser and add
 selected texture to the Checker Library"""

    filter_glob: bpy.props.StringProperty(
        default='*.jpg;*.png',
        options={'HIDDEN'}
    )

    def execute(self, context):
        from .preferences import get_prefs
        addon_prefs = get_prefs()
        path = addon_prefs.assetspath
        # Copy User Image to
        copy(self.filepath, path)
        print("ZChecker: File ", self.filepath)
        print("          Copied to: ", path)
        addon_prefs.files_dict = dumps(update_files_info(path))
        return {'FINISHED'}


class ZTCHK_OT_ResetPath(bpy.types.Operator):
    bl_idname = f"ops.{ADDON_SHORT}_reset_path"
    bl_label = "Reset Path"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Reset Checker Library path to Default State"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Path to the Checker Library will be changed to Default state")
        layout.separator()

    def execute(self, context):
        from .preferences import get_prefs
        addon_prefs = get_prefs()
        items = addon_prefs.__annotations__.keys()
        for pref in items:
            if pref == "assetspath":
                addon_prefs.property_unset(pref)
        # Update main dict
        addon_prefs.files_dict = dumps(update_files_info(addon_prefs.assetspath))
        addon_prefs["SizesY"] = 0
        addon_prefs["ZenCheckerImages"] = 0
        return {'FINISHED'}


classes = (
    ZTCHK_OT_CollectImages,
    ZTCHK_OT_AppendCheckerFile,
    ZTCHK_OT_ResetPath
)


def register():
    from bpy.utils import register_class
    for cl in classes:
        register_class(cl)


def unregister():
    from bpy.utils import unregister_class
    for cl in classes:
        unregister_class(cl)


if __name__ == '__main__':
    pass
