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

""" Zen UV Addon Preferences Init """

import bpy

from json import dumps

from bpy.props import PointerProperty
from bpy.utils import register_class, unregister_class
from ZenUV.prop.zuv_preferences import ZuvPanelEnableGroup, ZuvComboSettings, ZUV_AddonPreferences, get_prefs
from ZenUV.zen_checker.files import update_files_info
from ZenUV.utils.vlog import Log

from ..ops.texel_density.td_props import register as register_td_props
from ..ops.texel_density.td_props import unregister as unregister_td_props
from ZenUV.prop.properties import ZUV_Properties
from ZenUV.prop.op_relax_props import ZUV_RelaxOpProps
from ZenUV.prop.op_quadrify_props import ZUV_QuadrifyOpProps
from ZenUV.sticky_uv_editor.stk_uv_props import UVEditorSettings
from ZenUV.ops.zen_unwrap.props import (
    ZUV_ZenUnwrapOpAddonProps,
    ZUV_ZenUnwrapOpSceneProps
    )
from ZenUV.prop.scene_ui_props import (
    ZUV_UVToolProps,
    ZUV_3DVToolProps,
    ZUV_SceneUIProps)
from ZenUV.prop.demo_examples import (
    ZuvDemoExample,
    ZUV_DemoExampleProps,
    ZUV_OT_DemoExamplesUpdate,
    ZUV_OT_DemoExamplesDownload,
    ZUV_OT_DemoExamplesDelete,
    ZUV_UL_DemoExampleList,
)
from ZenUV.prop.material_props import ZUV_MaterialProps
from ZenUV.prop.user_script_props import (
    ZUV_UserScriptProps,
    ZUV_OT_UserScriptTemplate,
    ZUV_OT_UserScriptSelect)
from ZenUV.prop.td_draw_props import ZUV_TexelDensityDrawProps
from ZenUV.prop.wm_props import (
    ZuvUVMapWrapper,
    ZuvUVMeshGroup,
    ZuvObjUVGroup,
    ZuvWMDrawGroup,
    ZuvWMTexelDensityGroup,
    ZUV_WMProps)
from ZenUV.prop.adv_maps_props import ZUV_AdvMapsProps, ZUV_AdvMapsSceneProps, ZUV_AdvMapsRenameTemplateGroup
from ZenUV.prop.image_props import ZuvImageProperties
from ZenUV.prop.world_scale_props import ZUV_WorldScaleProps


classes = (
    ZUV_RelaxOpProps,
    ZUV_QuadrifyOpProps,
    UVEditorSettings,
    ZUV_ZenUnwrapOpAddonProps,
    ZUV_ZenUnwrapOpSceneProps,
    ZuvPanelEnableGroup,
    ZuvComboSettings,
    ZUV_MaterialProps,
    ZUV_TexelDensityDrawProps,
    ZUV_AdvMapsRenameTemplateGroup,
    ZUV_AdvMapsProps,
    ZUV_AdvMapsSceneProps,
    ZUV_WorldScaleProps,
    ZuvImageProperties,

    ZUV_UserScriptProps,
    ZUV_OT_UserScriptSelect,
    ZUV_OT_UserScriptTemplate,

    ZuvUVMeshGroup,
    ZuvUVMapWrapper,
    ZuvObjUVGroup,
    ZuvWMDrawGroup,
    ZuvWMTexelDensityGroup,
    ZUV_WMProps,

    ZuvDemoExample,
    ZUV_DemoExampleProps,
    ZUV_OT_DemoExamplesUpdate,
    ZUV_OT_DemoExamplesDownload,
    ZUV_OT_DemoExamplesDelete,
    ZUV_UL_DemoExampleList,

    ZUV_UVToolProps,
    ZUV_3DVToolProps,
    ZUV_SceneUIProps
)


def register():

    # Registering Properties Classes

    for cl in classes:
        register_class(cl)

    register_td_props()

    # Registering Addon Properties. Always after Properties Classes registration.
    register_class(ZUV_AddonPreferences)
    register_class(ZUV_Properties)

    bpy.types.Scene.zen_uv = PointerProperty(type=ZUV_Properties)
    bpy.types.Scene.StkUvEdProps = PointerProperty(type=UVEditorSettings)

    bpy.types.Image.zen_uv = bpy.props.PointerProperty(
        name='Zen UV Image Properties',
        type=ZuvImageProperties)

    bpy.types.WindowManager.zen_uv = bpy.props.PointerProperty(type=ZUV_WMProps)
    bpy.types.Material.zen_uv = bpy.props.PointerProperty(type=ZUV_MaterialProps)

    # WARNING! It may slow down addon loading !!!
    addon_prefs = get_prefs()
    addon_prefs.files_dict = dumps(update_files_info(addon_prefs.assetspath))


def unregister():
    # Unregistering Properties Classes

    for cl in classes:
        unregister_class(cl)

    # Unregistering Addon Properties. Always after Properties Classes unregistration.
    unregister_class(ZUV_AddonPreferences)
    unregister_class(ZUV_Properties)
    unregister_td_props()

    try:
        del bpy.types.Scene.zen_uv
        del bpy.types.Scene.StkUvEdProps
        del bpy.types.Material.zen_uv
        del bpy.types.WindowManager.zen_uv
        del bpy.types.Image.zen_uv
    except Exception as e:
        Log.error('UNREGISTER PROPS:', e)
