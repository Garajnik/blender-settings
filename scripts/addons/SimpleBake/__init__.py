bl_info = {
    "name": "SimpleBake",
    "author": "Lewis <www.toohey.co.uk/SimpleBake/support/>",
    "version": (1, 8, 3),
    "blender": (4, 2, 1),
    "location": "Properties Panel -> Render Settings Tab",
    "description": "Simple baking of PBR and other textures",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object",
}

import bpy
from bpy.utils import register_class, unregister_class

from . import object_preperation
from . import image_management
from . import material_management
from . import external_save
from . import property_group
from . import uv_management
from . import copy_and_apply
from . import starting_checks
from . import utils
from . import background_and_progress
from . import channel_packing
from . import channel_packing_old
from . import cleanup
try:
    from . import auto_update
except:
    auto_update = None
from . import presets
from . import presets_local
from . import sketchfab_upload
from . import messages
from . import auto_cage


from . import ui
from . import bake_operators

import platform
import sys
from pathlib import Path

if auto_update != None:
    from .auto_update import VersionControl
else:
    VersionControl = None

#-----------------------------------------------------------------------------------------------------


# #In case the Blender python packages directory is not writable
# import site
# print(site.getusersitepackages())
# site.addsitedir(site.getusersitepackages())
#
#
# def ensure_pillow():
#     try:
#         import PIL
#     except ImportError:
#         print("PIL is not available")
#
#         # Detect the system platform
#         system = platform.system().lower()
#
#         # Get the current Python version
#         py_version = f"{sys.version_info.major}{sys.version_info.minor}"
#         print(f"Available Python version {py_version}")
#
#         # Map system to directory
#         if system == 'windows':
#             wheel_dir = 'windows'
#         elif system == 'darwin':  # macOS
#             # Determine macOS version
#             mac_ver = platform.mac_ver()[0]
#             major_version = int(mac_ver.split('.')[0])
#
#             # Choose the correct wheel based on macOS version
#             if major_version >= 11:
#                 wheel_dir = 'macos/11_0'
#             else:
#                 wheel_dir = 'macos/10_10'
#         elif system == 'linux':
#             wheel_dir = 'linux'
#         else:
#             raise OSError(f"Unsupported platform: {system}")
#         print(f"System dir will be {wheel_dir}")
#
#         wheel_path = Path(__file__).parent / "libs" / wheel_dir
#
#         #Scan our path for the file with the correct python version
#         for file_path in wheel_path.rglob('*'):
#             if py_version in file_path.name:
#                 wheel_path = wheel_path / file_path.name
#
#         print(f"Going to use {wheel_path}")
#
#         # Construct the path to the wheel
#         #wheel_path = Path(__file__).parent / "libs" / wheel_dir / f"pillow-10.4.0-cp{py_version}-cp{py_version}-{platform}.whl"
#
#         # Check if the wheel exists and install it
#         if wheel_path.exists():
#             try:
#                 import subprocess
#                 subprocess.check_call([sys.executable, "-m", "pip", "install", str(wheel_path)])
#             except subprocess.CalledProcessError as e:
#                 print(f"Failed to install Pillow from wheel: {e}")
#         else:
#             print(f"Pillow wheel file not found for Python {py_version} on {system}.")
#             # Optional: You could add a download mechanism here
#
# ensure_pillow()

#------------------------------------------------------------------------------------------------------------


classes = ([
        ])

def register():
    global classes
    for cls in classes:
        register_class(cls)

    object_preperation.register()
    image_management.register()
    material_management.register()
    external_save.register()
    property_group.register()
    ui.register()
    uv_management.register()
    copy_and_apply.register()
    bake_operators.register()
    starting_checks.register()
    utils.register()
    background_and_progress.register()
    channel_packing.register()
    channel_packing_old.register()
    if auto_update!=None:
        auto_update.register()
    presets.register()
    presets_local.register()
    sketchfab_upload.register()
    messages.register()
    auto_cage.register()
    cleanup.register()

    prefs = bpy.context.preferences.addons[__package__].preferences

    version = bl_info["version"]
    if VersionControl != None:
        VersionControl.installed_version = version
        no_online_check = False
        if prefs.no_update_check:
            no_online_check = True
        VersionControl.check_at_current_version(no_online_check)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
        
    object_preperation.unregister()
    image_management.unregister()
    material_management.unregister()
    external_save.unregister()
    property_group.unregister()
    ui.unregister()
    uv_management.unregister()
    copy_and_apply.unregister()
    bake_operators.unregister()
    starting_checks.unregister()
    utils.unregister()
    background_and_progress.unregister()
    channel_packing.unregister()
    channel_packing_old.unregister()
    if auto_update != None:
        auto_update.unregister()
    presets.unregister()
    presets_local.unregister()
    sketchfab_upload.unregister()
    messages.unregister()
    auto_cage.unregister()
    cleanup.unregister()
    
