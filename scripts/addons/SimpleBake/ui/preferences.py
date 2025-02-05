import bpy
import os
from pathlib import Path
from bpy.utils import register_class, unregister_class
from bpy.types import Panel, AddonPreferences, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from .. import __package__ as base_package
from .panel import SIMPLEBAKE_PT_main_panel
from .panel import read_settings

import webbrowser

try:
    from ..auto_update import VersionControl
except:
    VersionControl = None
from ..utils import SBConstants, clean_file_name, get_cs_list

panel_loc_just_changed = False

class SimpleBake_Preferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = base_package
    

    apikey: StringProperty(name="Sketchfab API Key: ")
    img_name_format: StringProperty(name="Image format string",
        default="%OBJ%_%BATCH%_%BAKEMODE%_%BAKETYPE%")
    des = "Abbreviate the resolution in the image name where appropriate (e.g. \"2K\" instead of \"2048x2048\")"
    abbr_res: BoolProperty(description = des, default = True)
    
    
    #Aliases
    diffuse_alias: StringProperty(name=SBConstants.PBR_DIFFUSE, default=SBConstants.PBR_DIFFUSE)
    diffuse_cs: EnumProperty(name="", items=get_cs_list, default=19)
    metal_alias: StringProperty(name=SBConstants.PBR_METAL, default=SBConstants.PBR_METAL)
    metal_cs: EnumProperty(name="", items=get_cs_list, default=16)
    roughness_alias: StringProperty(name=SBConstants.PBR_ROUGHNESS, default=SBConstants.PBR_ROUGHNESS)
    roughness_cs: EnumProperty(name="", items=get_cs_list, default=16)
    glossy_alias: StringProperty(name=SBConstants.PBR_GLOSSY, default=SBConstants.PBR_GLOSSY)
    glossy_cs: EnumProperty(name="", items=get_cs_list, default=16)
    normal_alias: StringProperty(name=SBConstants.PBR_NORMAL, default=SBConstants.PBR_NORMAL)
    normal_cs: EnumProperty(name="", items=get_cs_list, default=16)
    transmission_alias: StringProperty(name=SBConstants.PBR_TRANSMISSION, default=SBConstants.PBR_TRANSMISSION)
    transmission_cs: EnumProperty(name="", items=get_cs_list, default=16)
    #transmissionrough_alias: StringProperty(name=SBConstants.PBR_TRANSMISSION_ROUGH, default=SBConstants.PBR_TRANSMISSION_ROUGH)
    #transmissionrough_cs: EnumProperty(name="", items=get_cs_list, default=16)
    clearcoat_alias: StringProperty(name=SBConstants.PBR_CLEARCOAT, default=SBConstants.PBR_CLEARCOAT)
    clearcoat_cs: EnumProperty(name="", items=get_cs_list, default=16)
    clearcoatrough_alias: StringProperty(name=SBConstants.PBR_CLEARCOAT_ROUGH, default=SBConstants.PBR_CLEARCOAT_ROUGH)
    clearcoatrough_cs: EnumProperty(name="", items=get_cs_list, default=16)
    emission_alias: StringProperty(name=SBConstants.PBR_EMISSION, default=SBConstants.PBR_EMISSION)
    emission_cs: EnumProperty(name="", items=get_cs_list, default=19)
    emission_strength_alias: StringProperty(name=SBConstants.PBR_EMISSION_STRENGTH, default=SBConstants.PBR_EMISSION_STRENGTH)
    emission_strength_cs: EnumProperty(name="", items=get_cs_list, default=16)
    specular_alias: StringProperty(name=SBConstants.PBR_SPECULAR, default=SBConstants.PBR_SPECULAR)
    specular_cs: EnumProperty(name="", items=get_cs_list, default=16)
    alpha_alias: StringProperty(name=SBConstants.PBR_ALPHA, default=SBConstants.PBR_ALPHA)    
    alpha_cs: EnumProperty(name="", items=get_cs_list, default=16)
    sss_alias: StringProperty(name=SBConstants.PBR_SSS, default=SBConstants.PBR_SSS)
    sss_cs: EnumProperty(name="", items=get_cs_list, default=16)
    #ssscol_alias: StringProperty(name=SBConstants.PBR_SSSCOL, default=SBConstants.PBR_SSSCOL)
    #ssscol_cs: EnumProperty(name="", items=get_cs_list, default=16)
    bump_alias: StringProperty(name=SBConstants.PBR_BUMP, default=SBConstants.PBR_BUMP)
    bump_cs: EnumProperty(name="", items=get_cs_list, default=16)
    displacement_alias: StringProperty(name=SBConstants.PBR_DISPLACEMENT, default=SBConstants.PBR_DISPLACEMENT)
    displacement_cs: EnumProperty(name="", items=get_cs_list, default=16)
    
    ao_alias: StringProperty(name=SBConstants.AO, default=SBConstants.AO)
    ao_cs: EnumProperty(name="", items=get_cs_list, default=16)
    curvature_alias: StringProperty(name=SBConstants.CURVATURE, default=SBConstants.CURVATURE)
    curvature_cs: EnumProperty(name="", items=get_cs_list, default=16)
    thickness_alias: StringProperty(name=SBConstants.THICKNESS, default=SBConstants.THICKNESS)
    thickness_cs: EnumProperty(name="", items=get_cs_list, default=16)
    vertexcol_alias: StringProperty(name=SBConstants.VERTEXCOL, default=SBConstants.VERTEXCOL)
    vertexcol_cs: EnumProperty(name="", items=get_cs_list, default=16)
    colid_alias: StringProperty(name=SBConstants.COLOURID, default=SBConstants.COLOURID)
    colid_cs: EnumProperty(name="", items=get_cs_list, default=16)
    lightmap_alias: StringProperty(name=SBConstants.LIGHTMAP, default=SBConstants.LIGHTMAP)
    lightmap_cs: EnumProperty(name="", items=get_cs_list, default=16)
    
    #Misc tweaks and options
    no_update_check: BoolProperty(
        default=False,
        description="Don't automatically check for updates to SimpleBake. Keep at current installed version"
        )
    ungroup_all_node_groups: BoolProperty(
        default=False,
        description="Unpack all node groups. Used if you have very unusual node setups in your materials. (e.g. Material Output nodes hidden inside node groups). This will hurt performance, but can avoid crashes with some materials that have lots and lots of nested node groups"
        )
    skip_pbr_nodes_check: BoolProperty(
        default=False,
        description="Skip the check for invalid PBR nodes when baking PBR (Diffuse BSDF, Glossy BSDF etc.) NOT RECOMMENDED."
        )
    use_old_channel_packing: BoolProperty(
        default=False,
        description="Use the old compositor method of channel packing"
        )
    disable_auto_smooth_for_split_normals: BoolProperty(
        default=True,
        description="The auto-smooth option causes issues when baking normal maps for objects with custom split normals. This option will cause SimpleBake to disable auto-smooth for the bake to stop weird artifacts in the normal map"
        )
    pbr_sample_count: IntProperty(
        default=2,
        description="Override the sample count used for PBR bakes. The default is 2, and this is usually fine for all PBR bakes as they are baked as emission (i.e. no noise is possible)"
        )
    panel_location: EnumProperty(name="Panel location", default=0, items=[\
        ("renderpanel", "Render Panel", "Display SimpleBake on the Render Properties Panel (the camera icon)"),\
        ("npanel", "N-Panel", "Display SimpleBake on the N-Panel (also called the properties panel) in the 3D viewport")\
        ])

    togglesorboxes: EnumProperty(name="Toggles or tickboxes", default=0, items=[\
        ("toggles", "Use toggles", "Changes the appearance of the options on the SimpleBake panel (toggles)"),\
        ("tickboxes", "Use tickboxes", "Changes the appearance of the options on the SimpleBake panel (tickboxes)")\
        ])

    solidshadingonbake: BoolProperty(
        default=True,
        description="It is recommended to only use solid shaing during baking to\
        increase performance and reduce the chance of crashes"
        )
    saveonbake: BoolProperty(
        default=True,
        description="Save blend file prior to any baking operation"
        )
    disable_other_addons2: BoolProperty(
        default=False,
        description="Disable other addons when baking to prevent conflicts"
        )
    check_for_conflicting_addons: BoolProperty(
        default=True,
        description="Check for addons known to conflict with SimpleBake and prevent bake"
        )

    
    @classmethod
    def reset_img_string(cls, context):
        prefs = context.preferences.addons[base_package].preferences
        prefs.property_unset("img_name_format")
        bpy.ops.wm.save_userpref()
        
    @classmethod
    def reset_aliases(cls, context):
        prefs = context.preferences.addons[base_package].preferences
        
        prefs.property_unset("diffuse_alias")
        prefs.property_unset("metal_alias")  
        prefs.property_unset("roughness_alias")  
        prefs.property_unset("normal_alias")  
        prefs.property_unset("transmission_alias")  
        #prefs.property_unset("transmissionrough_alias")
        prefs.property_unset("clearcoat_alias")  
        prefs.property_unset("clearcoatrough_alias")  
        prefs.property_unset("emission_alias")
        prefs.property_unset("emission_strength_alias")
        prefs.property_unset("specular_alias")  
        prefs.property_unset("alpha_alias")
        prefs.property_unset("bump_alias")
        prefs.property_unset("displacement_alias")
        prefs.property_unset("sss_alias")
        #prefs.property_unset("ssscol_alias")
        prefs.property_unset("ao_alias") 
        prefs.property_unset("curvature_alias") 
        prefs.property_unset("thickness_alias") 
        prefs.property_unset("vertexcol_alias") 
        prefs.property_unset("colid_alias") 
        prefs.property_unset("lightmap_alias")
        
        prefs.property_unset("diffuse_cs")
        prefs.property_unset("metal_cs")  
        prefs.property_unset("roughness_cs")  
        prefs.property_unset("normal_cs")  
        prefs.property_unset("transmission_cs")  
        #prefs.property_unset("transmissionrough_cs")
        prefs.property_unset("clearcoat_cs")  
        prefs.property_unset("clearcoatrough_cs")  
        prefs.property_unset("emission_cs")
        prefs.property_unset("emission_strength_cs")
        prefs.property_unset("specular_cs")  
        prefs.property_unset("alpha_cs")
        prefs.property_unset("bump_cs")
        prefs.property_unset("displacement_cs")
        prefs.property_unset("sss_cs")
        #prefs.property_unset("ssscol_cs")
        prefs.property_unset("ao_cs") 
        prefs.property_unset("curvature_cs") 
        prefs.property_unset("thickness_cs") 
        prefs.property_unset("vertexcol_cs") 
        prefs.property_unset("colid_cs") 
        prefs.property_unset("lightmap_cs") 

        bpy.ops.wm.save_userpref() 
        
    def get_alias_dict(self):
        alias_dict = {}
        alias_dict[SBConstants.PBR_DIFFUSE] = clean_file_name(self.diffuse_alias)
        alias_dict[SBConstants.PBR_METAL] = clean_file_name(self.metal_alias)
        alias_dict[SBConstants.PBR_ROUGHNESS] = clean_file_name(self.roughness_alias)
        alias_dict[SBConstants.PBR_GLOSSY] = clean_file_name(self.glossy_alias)
        alias_dict[SBConstants.PBR_NORMAL] = clean_file_name(self.normal_alias)
        alias_dict[SBConstants.PBR_TRANSMISSION] = clean_file_name(self.transmission_alias)
        #alias_dict[SBConstants.PBR_TRANSMISSION_ROUGH] = clean_file_name(self.transmissionrough_alias)
        alias_dict[SBConstants.PBR_CLEARCOAT] = clean_file_name(self.clearcoat_alias)
        alias_dict[SBConstants.PBR_CLEARCOAT_ROUGH] = clean_file_name(self.clearcoatrough_alias)
        alias_dict[SBConstants.PBR_EMISSION] = clean_file_name(self.emission_alias)
        alias_dict[SBConstants.PBR_EMISSION_STRENGTH] = clean_file_name(self.emission_strength_alias)
        alias_dict[SBConstants.PBR_SPECULAR] = clean_file_name(self.specular_alias)
        alias_dict[SBConstants.PBR_ALPHA] = clean_file_name(self.alpha_alias)
        alias_dict[SBConstants.PBR_SSS] = clean_file_name(self.sss_alias)
        #alias_dict[SBConstants.PBR_SSSCOL] = clean_file_name(self.ssscol_alias)
        alias_dict[SBConstants.PBR_BUMP] = clean_file_name(self.bump_alias)
        alias_dict[SBConstants.PBR_DISPLACEMENT] = clean_file_name(self.displacement_alias)
        alias_dict[SBConstants.AO] = clean_file_name(self.ao_alias)
        alias_dict[SBConstants.CURVATURE] = clean_file_name(self.curvature_alias)
        alias_dict[SBConstants.THICKNESS] = clean_file_name(self.thickness_alias)
        alias_dict[SBConstants.VERTEXCOL] = clean_file_name(self.vertexcol_alias)
        alias_dict[SBConstants.COLOURID] = clean_file_name(self.colid_alias)
        alias_dict[SBConstants.LIGHTMAP] = clean_file_name(self.lightmap_alias)
        
        return alias_dict
    
    def get_cs_dict(self):
        cs_dict = {}
        cs_dict[SBConstants.PBR_DIFFUSE] = self.diffuse_cs
        cs_dict[SBConstants.PBR_METAL] = self.metal_cs
        cs_dict[SBConstants.PBR_ROUGHNESS] = self.roughness_cs
        cs_dict[SBConstants.PBR_GLOSSY] = self.glossy_cs
        cs_dict[SBConstants.PBR_NORMAL] = self.normal_cs
        cs_dict[SBConstants.PBR_TRANSMISSION] = self.transmission_cs
        #cs_dict[SBConstants.PBR_TRANSMISSION_ROUGH] = self.transmissionrough_cs
        cs_dict[SBConstants.PBR_CLEARCOAT] = self.clearcoat_cs
        cs_dict[SBConstants.PBR_CLEARCOAT_ROUGH] = self.clearcoatrough_cs
        cs_dict[SBConstants.PBR_EMISSION] = self.emission_cs
        cs_dict[SBConstants.PBR_EMISSION_STRENGTH] = self.emission_strength_cs
        cs_dict[SBConstants.PBR_SPECULAR] = self.specular_cs
        cs_dict[SBConstants.PBR_ALPHA] = self.alpha_cs
        cs_dict[SBConstants.PBR_SSS] = self.sss_cs
        #cs_dict[SBConstants.PBR_SSSCOL] = self.ssscol_cs
        cs_dict[SBConstants.PBR_BUMP] = self.bump_cs
        cs_dict[SBConstants.PBR_DISPLACEMENT] = self.displacement_cs
        cs_dict[SBConstants.AO] = self.ao_cs
        cs_dict[SBConstants.CURVATURE] = self.curvature_cs
        cs_dict[SBConstants.THICKNESS] = self.thickness_cs
        cs_dict[SBConstants.VERTEXCOL] = self.vertexcol_cs
        cs_dict[SBConstants.COLOURID] = self.colid_cs
        cs_dict[SBConstants.LIGHTMAP] = self.lightmap_cs
        
        return cs_dict
    
    def draw(self, context):
        sbp = context.scene.SimpleBake_Props
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.scale_y = 2
        row.operator("simplebake.release_notes", icon="MOD_WAVE")
        if VersionControl != None:
            if not VersionControl.at_current:
                row = box.row()
                row.scale_y = 2
                row.alert = True
                if VersionControl.just_updated:
                    row.label(text=f"Please restart Blender")
                else:
                    row.label(text=f"Version {VersionControl.current_version_str} of SimpleBake is available!")
                    row.operator("simplebake.auto_update", icon="MOD_WAVE")

            #Always allow rollback
            row = box.row()
            row.scale_y = 2
            row.operator("simplebake.rollback_update", icon="FILE_REFRESH", text="Rollback to previous version of SimpleBake")

            #Support
            box = layout.box()
            row = box.row()
            row.scale_y = 2
            row.operator("simplebake.support", icon="HELP")

            #Discord
            box = layout.box()
            row = box.row()
            row.scale_y = 2
            row.operator("simplebake.discord", icon="OUTLINER_OB_LIGHT")

        
        #Sketchfab
        box = layout.box()
        row = box.row()
        row.label(text="Enter your Sketchfab API key below. Don't forget to click \"Save Preferences\" after.")
        row = box.row()
        row.prop(self, "apikey")
        
        box = layout.box()
        row = box.row()
        row.label(text="Format for baked image names. Valid variables are:")

        row = box.row()
        row.label(text="%OBJ% (object name or 'MergedBake')")
        row.scale_y = 0.5
        row = box.row()
        row.label(text="%BATCH% (batch name)")
        row.scale_y = 0.5
        row = box.row()
        row.label(text="%BAKEMODE% (pbr or cycles bake)")
        row.scale_y = 0.5
        row = box.row()
        row.label(text="%BAKETYPE% (diffuse, emission etc.)")
        row.scale_y = 0.5
        row = box.row()
        row.label(text="%RESOLUTION% (e.g. 1024x1024)")
        row.scale_y = 0.5
        row = box.row()
        row.label(text="%FRAME% (Current frame number e.g. 0002 when baking an Image Sequence)")
        row.scale_y = 0.5

        
        row = box.row()
        row.prop(self, "img_name_format")
        row = box.row()
        row.prop(self, "abbr_res", text="Abbreviate resolution")
        row = box.row()
        row.operator("simplebake.default_imgname_string")
        
        #PBR Aliases
        box = layout.box()
        
        row = box.row()
        row.label(text="Aliases and colour space settings for PBR bake types")
        
        row = box.row()
        row.label(text="WARNING: Sketchfab looks for certain values. Changing these may break SF Upload")
        
        row = box.row()
        col = row.column()
        col.prop(self, "diffuse_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "diffuse_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "metal_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "metal_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "sss_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "sss_cs")
        
        row = box.row()
        col = row.column()
        col.prop(self, "roughness_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "roughness_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "glossy_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "glossy_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "transmission_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "transmission_cs")


        row = box.row()
        col = row.column()
        col.prop(self, "clearcoat_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "clearcoat_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "clearcoatrough_alias")  
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "clearcoatrough_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "emission_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "emission_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "emission_strength_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "emission_strength_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "specular_alias") 
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "specular_cs")
        
        row = box.row()
        col = row.column()
        col.prop(self, "alpha_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "alpha_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "normal_alias") 
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "normal_cs")
        
        row = box.row()
        col = row.column()
        col.prop(self, "bump_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "bump_cs")
        
        row = box.row()
        col = row.column()
        col.prop(self, "displacement_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "displacement_cs")

        #Specials Aliases
        box = layout.box()
        
        row = box.row()
        row.label(text="Aliases for special bake types")
        
        row = box.row()
        col = row.column()
        col.prop(self, "ao_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "ao_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "curvature_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "curvature_cs")
        
        row = box.row()
        col = row.column()
        col.prop(self, "thickness_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "thickness_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "vertexcol_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "vertexcol_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "colid_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "colid_cs")

        row = box.row()
        col = row.column()
        col.prop(self, "lightmap_alias")
        col = row.column()
        col.alignment = 'RIGHT'
        col.prop(self, "lightmap_cs")
        
        #Reset button
        box = layout.box()
        row = box.row()
        row.operator("simplebake.restore_default_aliases")
        
        box = layout.box()
        row = box.row()
        row.label(text="Tweaks and Misc Options")
        row = box.row()
        row.prop(self, "solidshadingonbake", text="Solid shading on bake")
        row = box.row()
        row.prop(self, "saveonbake", text="Save blend file prior to bake")
        row = box.row()
        row.prop(self, "no_update_check", text="Don't check for SimpleBake updates on Blender start")
        row = box.row()
        row.prop(self, "ungroup_all_node_groups", text="Unpack ALL node groups in materials")
        row = box.row()
        row.prop(self, "skip_pbr_nodes_check", text="Skip check for invalid nodes for PBR bake (NOT RECOMMENDED)")
        row = box.row()
        row.prop(self, "use_old_channel_packing", text="Use the old method for channel packing")
        row = box.row()
        row.prop(self, "disable_auto_smooth_for_split_normals", text="Disable auto-smooth for custom split normals")
        row = box.row()
        row.prop(self, "pbr_sample_count", text="Override PBR sample count")
        row = box.row()
        row.prop(self, "disable_other_addons2", text="DEBUG: Disable other addons on bake")
        row = box.row()
        row.prop(self, "check_for_conflicting_addons", text="Check for conflicting addons")

        row = box.row()
        row = box.row()
        row.alert = True
        row.scale_y = 0.5
        row.label(text="WARNING: Based on my testing, Blender crashes WAY more when SimpleBake")

        row = box.row()
        row.alert = True
        row.scale_y = 0.5
        row.label(text="is displayed in the N-Panel. I haven't been able to find out why")

        row = box.row()
        row.alert = True
        row.scale_y = 0.5
        row.label(text="Use with extreme caution!")

        row = box.row()
        row.scale_y = 1.4
        split = row.split(factor=0.2)
        col = split.column()
        col.label(text="Panel location")
        col = split.column()
        col.prop(self, "panel_location", text="")
        col = split.column()
        col.operator("simplebake.change_panel_location")
        global panel_loc_just_changed
        if panel_loc_just_changed:
            row = box.row()
            row.alert = True
            row.label(text="Restart Blender for changes to take effect")

        row = box.row()
        row.scale_y = 1.4
        split = row.split(factor=0.2)
        col = split.column()
        col.label(text="Toggles or tickboxes")
        col = split.column()
        col.prop(self, "togglesorboxes", text="")
        col = split.column()
        col.operator("simplebake.change_panel_toggles")


class SimpleBake_OT_change_panel_location(Operator):
    """Change the location of the SimpleBake panel"""
    bl_idname = "simplebake.change_panel_location"
    bl_label = "Change"

    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences
        p = Path(bpy.utils.script_path_user())
        p = p.parents[1]
        p = p / "data" / "SimpleBake" / "settings"
        savename = "panel_location.txt"

        if not os.path.isdir(str(p)):
            os.makedirs(str(p))

        content = prefs.panel_location

        with open(str(p / savename), 'w') as file:
            file.write(content)

        global panel_loc_just_changed
        panel_loc_just_changed = True


        return {'FINISHED'}

class SimpleBake_OT_change_panel_toggles(Operator):
    """Change the location of the SimpleBake panel"""
    bl_idname = "simplebake.change_panel_toggles"
    bl_label = "Change"

    def execute(self, context):
        prefs = context.preferences.addons[base_package].preferences
        p = Path(bpy.utils.script_path_user())
        p = p.parents[1]
        p = p / "data" / "SimpleBake" / "settings"
        savename = "toggles.txt"

        if not os.path.isdir(str(p)):
            os.makedirs(str(p))

        content = prefs.togglesorboxes

        with open(str(p / savename), 'w') as file:
            file.write(content)

        read_settings()
        unregister_class(SIMPLEBAKE_PT_main_panel)
        register_class(SIMPLEBAKE_PT_main_panel)

        self.report({'INFO'}, "Change made")

        return {'FINISHED'}

        
        
class SimpleBake_OT_restore_default_aliases(Operator):
    """Reset the image name aliases"""
    bl_idname = "simplebake.restore_default_aliases"
    bl_label = "Restore all aliases and colour space settings to default"
    
    def execute(self, context):
        SimpleBake_Preferences.reset_aliases(context)
        return {'FINISHED'} 

class SimpleBake_OT_default_imgname_string(Operator):
    """Reset the image name string to default (Sketchfab compatible)"""
    bl_idname = "simplebake.default_imgname_string"
    bl_label = "Restore image string to default"
    
    def execute(self, context):
        SimpleBake_Preferences.reset_img_string(context)
        
        return {'FINISHED'} 

class SimpleBake_OT_Release_Notes(Operator):
    """View the SimpleBake Release Notes"""
    bl_idname = "simplebake.release_notes"
    bl_label = "View the SimpleBake Release Notes"
    
    def execute(self, context):
        webbrowser.open('http://www.toohey.co.uk/SimpleBake/releasenotes4.html', new=2)
        return {'FINISHED'}  

class SimpleBake_OT_Support(Operator):
    """Open the SimpleBake Support Page"""
    bl_idname = "simplebake.support"
    bl_label = "Open the SimpleBake Support Page"
    
    def execute(self, context):
        webbrowser.open('http://www.toohey.co.uk/SimpleBake/support', new=2)
        return {'FINISHED'}

class SimpleBake_OT_Discord(Operator):
    """Open the SimpleBake Discord"""
    bl_idname = "simplebake.discord"
    bl_label = "Open the SimpleBake Discord"

    def execute(self, context):
        webbrowser.open('https://discord.gg/ux9adAM2ZZ', new=2)
        return {'FINISHED'}

classes = ([
        SimpleBake_Preferences,
        SimpleBake_OT_Release_Notes,
        SimpleBake_OT_Support,
        SimpleBake_OT_restore_default_aliases,
        SimpleBake_OT_default_imgname_string,
        SimpleBake_OT_Discord,
        SimpleBake_OT_change_panel_location,
        SimpleBake_OT_change_panel_toggles
        ])

def register():
    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
