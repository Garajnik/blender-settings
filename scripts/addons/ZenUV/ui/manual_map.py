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

import bpy

from ZenUV.utils.blender_zen_utils import ZenPolls


def normalize(string):
    """ Switch to lower case and replaces SPACES by '-' """
    return string.lower().replace(" ", "-")


# Lower Case Only !
zen_uv_manual_map = (

    # Adv UV Maps
    ('bpy.ops.wm.zuv_adv_maps_rename', 'adv_uv-maps/#rename-uv-maps'),
    ('bpy.ops.mesh.zuv_add_uvs*', 'adv_uv-maps/#duplicate-active-uv-map'),
    ('bpy.ops.mesh.zuv_remove_uvs', 'adv_uv-maps/#remove-active-uv-map'),
    ('bpy.ops.mesh.zuv_move_*', 'adv_uv-maps/#advanced-uv-maps-list'),
    ('bpy.ops.wm.zuv_advmaps_sync', 'adv_uv-maps/#sync-uv-maps-ids'),

    # Copy UV / Paste UV Subsection
    ('bpy.ops.uv.zenuv_copy_uv', 'adv_uv-maps/#copy-uv-paste-uv'),
    ('bpy.ops.uv.zenuv_paste_uv', 'adv_uv-maps/#copy-uv-paste-uv'),

    # Unwrap Section
    ('bpy.ops.uv.zenuv_unwrap', 'unwrap/#zen-unwrap'),
    ('bpy.ops.uv.zenuv_unwrap_constraint', 'unwrap/#unwrap-constraint'),
    ('bpy.ops.uv.zenuv_unwrap_inplace', 'unwrap/#unwrap-inplace'),
    # -- Mark Subsection
    ('bpy.ops.uv.zenuv_auto_mark', 'unwrap/#mark-by-angle'),
    ('bpy.ops.uv.zenuv_mark_seams', 'unwrap/#mark'),
    ('bpy.ops.uv.zenuv_unmark_all', normalize('unwrap/#Unmark All')),
    ('bpy.ops.uv.zenuv_unmark_seams', 'unwrap/#unmark'),
    ('bpy.ops.uv.zenuv_unified_mark', 'unwrap/#conversion-system'),
    ('bpy.types.ZUV_Properties.sl_convert'.lower(), 'unwrap/#conversion-system'),
    ('bpy.ops.mesh.zenuv_mirror_seams', 'unwrap/#mirror-seams'),
    ('bpy.ops.view3d.zenuv_set_smooth_by_sharp', 'unwrap/#smooth-by-sharp-toggle'),
    # -- Conversion Subsection
    ('bpy.ops.uv.zenuv_seams_by_open_edges', 'unwrap/#seams-by-open-edges'),
    ('bpy.ops.uv.zenuv_seams_by_sharp', 'unwrap/#seams-by-sharp-edges'),
    ('bpy.ops.uv.zenuv_seams_by_uv_islands', normalize('unwrap/#Seams by UV Borders')),
    ('bpy.ops.uv.zenuv_sharp_by_seams', normalize('unwrap/#Sharp Edges by Seams')),
    ('bpy.ops.uv.zenuv_sharp_by_uv_islands', normalize('unwrap/#Sharp by UV Borders')),
    # -- Finished Subsection
    ('bpy.ops.uv.zenuv_islands_sorting', normalize('unwrap/#Sort Islands by Tags')),
    ('bpy.ops.uv.zenuv_tag_finished', normalize('unwrap/#Tag Finished')),
    ('bpy.ops.uv.zenuv_untag_finished', normalize('unwrap/#Tag Unfinished')),
    ('bpy.ops.uv.zenuv_select_finished', normalize('unwrap/#Select Finished')),
    ('bpy.ops.uv.zenuv_display_finished', normalize('unwrap/#Display Finished Toggle')),

    # Select Section
    ('bpy.ops.uv.zenuv_select_island', normalize('select/#Islands')),
    ('bpy.ops.uv.zenuv_select_loop', normalize('select/#Int Loop')),
    ('bpy.ops.uv.zenuv_select_uv_overlap', normalize('select/#Overlapped')),
    ('bpy.ops.uv.zenuv_select_flipped', normalize('select/#Flipped')),
    ('bpy.ops.mesh.zenuv_select_seams', normalize('select/#Seam')),
    ('bpy.ops.mesh.zenuv_select_sharp', normalize('select/#Sharp')),
    ('bpy.ops.uv.zenuv_select_uv_borders', normalize('select/#Select UV Borders')),
    ('bpy.ops.uv.zenuv_select_similar', normalize('select/#Similar')),
    ('bpy.ops.uv.zenuv_select_by_direction', normalize('select/#Select Edges By Direction')),
    ('bpy.ops.uv.zenuv_isolate_island', normalize('select/#Isolate Islands Toggle')),
    ('bpy.ops.uv.zenuv_select_by_uv_area', normalize('select/#select-by-uv-area')),
    ('bpy.ops.uv.zenuv_grab_sel_area', normalize('select/#operator-get-selected-area')),

    # Pack Section
    ('bpy.ops.uv.zenuv_pack', normalize('pack/#Pack Islands')),
    ('bpy.ops.uv.zenuv_sync_to_uvp', normalize('pack/#TEMP_LINK')),
    ('bpy.ops.uv.zenuv_get_uv_coverage', normalize('pack/#UV Coverage')),

    # Checker Section
    ('bpy.ops.view3d.zenuv_checker_toggle', normalize('checker/#Checker Texture Toggle')),
    ('bpy.ops.view3d.zenuv_checker_remove', normalize('checker/#TEMP_LINK')),
    ('bpy.types.ZUV_Properties.tex_checker_interpolation'.lower(), normalize('checker/#1-interpolation')),
    ('bpy.types.ZUV_Properties.tex_checker_tiling'.lower(), 'checker/#2-checker-textures'),
    ('bpy.types.ZUV_Properties.tex_checker_offset'.lower(), 'checker/#2-checker-textures'),
    ('bpy.types.ZUV_PT_OSL_Display.stretch'.lower(), normalize('checker/#Display Stretch Map')),
    ('bpy.ops.uv.zenuv_select_stretched_islands', normalize('checker/#Display Stretch Map')),
    # -- Checker Props Subsection
    ('bpy.ops.ops.zenuv_checker_reset_path', normalize('checker/#Checker Texture Toggle')),
    ('bpy.ops.view3d.zenuv_check_library', normalize('checker/#Checker Texture Toggle')),
    ('bpy.ops.view3d.zenuv_checker_append_checker_file', normalize('checker/#Checker Texture Toggle')),
    ('bpy.ops.view3d.zenuv_checker_collect_images', normalize('checker/#Checker Texture Toggle')),
    ('bpy.ops.view3d.zenuv_checker_open_editor', normalize('checker/#Checker Texture Toggle')),
    ('bpy.ops.view3d.zenuv_checker_reset', normalize('checker/#Checker Texture Toggle')),

    # Prefs / System Section
    ('bpy.ops.ops.zenuv_show_prefs', normalize('preferences/#Preferences System')),
    ('bpy.ops.uv.zenuv_debug', '/#TEMP_LINK'),
    ('bpy.ops.uv.zenuv_unregister_library', normalize('installation/#Installation')),
    ('bpy.ops.uv.zenuv_update_addon', normalize('installation/#Installation')),
    ('bpy.ops.view3d.zenuv_install_library', normalize('installation/#Installation')),
    ('bpy.ops.zenuv.reset_preferences', normalize('preferences/#Preferences System')),

    # # -- Unused Operators Subsection
    # ('bpy.ops.zenuv.call_pie', '/#TEMP_LINK'),
    # ('bpy.ops.zenuv.call_popup', '/#TEMP_LINK'),
    # ('bpy.ops.zenuv.pie_caller', '/#TEMP_LINK'),
    # ('bpy.ops.uv.zenuv_show_sim_index', normalize('stack/#Stack')),

    # Seam Groups Section
    ('bpy.ops.uv.zenuv_activate_seam_group', normalize('seam_groups/#Seam Groups')),
    ('bpy.ops.uv.zenuv_assign_seam_to_group', normalize('seam_groups/#Seam Groups')),
    ('bpy.ops.zen_sg_list.delete_item', normalize('seam_groups/#Seam Groups')),
    ('bpy.ops.zen_sg_list.move_item', normalize('seam_groups/#Seam Groups')),
    ('bpy.ops.zen_sg_list.new_item', normalize('seam_groups/#Seam Groups')),

    # Texel Density Section
    ('bpy.ops.uv.zenuv_bake_td_to_vc', normalize('texel_density/#TD Checker')),
    # ('bpy.ops.uv.zenuv_get_image_size_uv_layout', 'texel_density/#TEMP_LINK'),
    ('bpy.ops.uv.zenuv_get_texel_density', normalize('texel_density/#Get TD')),
    ('bpy.ops.uv.zenuv_get_texel_density_obj', normalize('texel_density/#Get TD')),
    ('bpy.ops.uv.zenuv_clear_baked_texel_density', normalize('texel_density/#TD Checker')),
    ('bpy.ops.uv.zenuv_set_texel_density', normalize('texel_density/#Set TD')),
    ('bpy.ops.uv.zenuv_set_texel_density_obj', normalize('texel_density/#Set TD')),
    # ('bpy.ops.zenuv.set_current_td_to_checker_td', normalize('texel_density/#TD Checker')),

    # -- Texel Density Presets Subsection
    # ('bpy.ops.uv.zenuv_bake_td_to_vc_preset', normalize('texel_density/#Show Presets')),
    ('bpy.ops.zen_tdpr.clear_presets', normalize('texel_density/#Clear')),
    ('bpy.ops.zen_tdpr.delete_item', normalize('texel_density/#Texel Density Presets')),
    ('bpy.ops.zen_tdpr.generate_presets', normalize('texel_density/#Generate')),
    ('bpy.ops.zen_tdpr.get_td_from_preset', normalize('texel_density/#Get')),
    ('bpy.ops.zen_tdpr.move_item', normalize('texel_density/#Texel Density Presets')),
    ('bpy.ops.zen_tdpr.new_item', normalize('texel_density/#Texel Density Presets')),
    ('bpy.ops.zen_tdpr.select_by_texel_density', normalize('texel_density/#Select by TD')),
    ('bpy.ops.zen_tdpr.set_td_from_preset', normalize('texel_density/#Set From Preset')),

    # Transform Section
    ('bpy.ops.uv.zenuv_relax', normalize('transform/#Relax')),
    ('bpy.ops.uv.zenuv_world_orient', normalize('transform/#World Orient')),
    ('bpy.ops.uv.zenuv_randomize_transform', normalize('transform/#Randomize')),
    ('bpy.ops.uv.zenuv_quadrify', normalize('transform/#Quadrify Islands')),
    ('bpy.ops.uv.zenuv_reshape_island', normalize('operators/reshape_island')),

    ('bpy.ops.uv.zenuv_unified_transform', normalize('transform/#Universal Control Panel')),
    ('bpy.types.ZUV_Properties.tr_pivot_mode'.lower(), normalize('transform/#Pivot')),
    ('bpy.types.ZUV_Properties.tr_type'.lower(), normalize('transform/#Mode')),
    ('bpy.types.ZUV_Properties.tr_mode'.lower(), normalize('transform/#Transform Types')),

    ('bpy.ops.uv.zenuv_arrange_transform', normalize('transform/#Transform type Distribute')),
    ('bpy.ops.uv.zenuv_distribute_islands', normalize('transform/#Transform type Distribute')),
    ('bpy.ops.uv.zenuv_distribute_verts', normalize('transform/#Transform type Distribute')),
    ('bpy.ops.uv.zenuv_fit_grab_region', normalize('transform/#Fit into Region')),
    ('bpy.ops.uv.zenuv_fit_region', normalize('transform/#Fit into Region')),
    ('bpy.ops.uv.zenuv_scale_grab_size', normalize('transform/#Fit into Region')),
    ('bpy.types.ZUV_Properties.tr_fit_region_tr'.lower(), normalize('transform/#Fit into Region')),
    ('bpy.ops.uv.zenuv_tr_scale_tuner', normalize('transformtransform/#mode-axis')),

    # Stack Section
    ('bpy.ops.uv.zenuv_stack_similar', normalize('stack/#Stack')),
    ('bpy.ops.uv.zenuv_unstack', normalize('stack/#Unstack')),
    ('bpy.ops.uv.zenuv_simple_stack', normalize('stack/#Stack Mode')),
    ('bpy.ops.uv.zenuv_simple_unstack', normalize('stack/#Stack Mode')),
    ('bpy.ops.uv.zenuv_select_stack', normalize('stack/#Stack Display Mode')),
    ('bpy.ops.uv.zenuv_select_stacked', normalize('stack/#Stack Display Mode')),

    # -- Copy/Paste Subsection
    ('bpy.ops.uv.zenuv_copy_param', normalize('operators/stack_copy_paste/#Copy')),
    ('bpy.ops.uv.zenuv_paste_param', normalize('operators/stack_copy_paste/#Paste')),

    # -- Manual Stack Subsection
    ('bpy.ops.uv.zenuv_assign_manual_stack', normalize('stack/#Add Islands')),
    ('bpy.ops.uv.zenuv_collect_manual_stacks', normalize('stack/#Stack_2')),
    ('bpy.ops.zen_stack_list.delete_item', normalize('stack/#Delete')),
    ('bpy.ops.zen_stack_list.new_item', normalize('stack/#Add')),
    ('bpy.ops.zen_stack_list.remove_all_m_stacks', normalize('stack/#Remove All')),
    ('bpy.ops.uv.zenuv_analyze_stack', normalize('stack/#Analyze Stack')),
    ('bpy.ops.uv.zenuv_unstack_manual_stack', normalize('stack/#Unstack_1')),
    ('bpy.ops.uv.zenuv_select_m_stack', normalize('select/#manual-stack#Select Islands')),

    # -- Excluded System
    ('bpy.ops.uv.zenuv_offset_pack_excluded', normalize('pack/#offset-excluded')),
    ('bpy.ops.uv.zenuv_tag_pack_excluded', normalize('pack/#tag-excluded')),
    ('bpy.ops.uv.zenuv_untag_pack_excluded', normalize('pack/#untag-excluded')),
    ('bpy.ops.uv.zenuv_hide_pack_excluded', normalize('pack/#hide')),
    ('bpy.ops.uv.zenuv_unhide_pack_excluded', normalize('pack/#unhide')),
    ('bpy.ops.uv.zenuv_select_pack_excluded', normalize('pack/#select-excluded')),
    ('bpy.types.ZUV_PT_OSL_Display.p_excluded'.lower(), normalize('pack/#display-excluded')),

    # -- Trimsheet
    ('bpy.ops.uv.zuv_add_trimsheet_preset', 'trimsheet_creation/#add_1'),
    ('bpy.ops.wm.zenuv_open_presets_folder', 'trimsheet_creation/#open-presets-folder'),
    ('bpy.ops.wm.zuv_trim_preview', 'trimsheet_creation/#select-active-trim-with-preview-panel'),

    ('bpy.ops.uv.zenuv_new_trim', 'trimsheet_creation/#add'),
    ('bpy.ops.uv.zuv_trim_remove_ui', 'trimsheet_creation/#remove'),
    ('bpy.ops.uv.zuv_trim_delete_all', 'trimsheet_creation/#delete-all'),

    ('bpy.ops.*.zenuv_move_in_trim', 'trimsheet_operators/#move-in-trim'),
    ('bpy.ops.*.zenuv_fit_to_trim', 'trimsheet_operators/#fit-to-trim'),
    ('bpy.ops.*.zenuv_rotate_in_trim', 'trimsheet_operators/#rotate-in-trim'),
    ('bpy.ops.*.zenuv_align_to_trim', 'trimsheet_operators/#align-to-trim'),
    ('bpy.ops.*.zenuv_flip_in_trim', 'trimsheet_operators/#flip-in-trim'),
    ('bpy.ops.*.zenuv_scale_in_trim', 'trimsheet_operators/#scale-in-trim'),

    ('bpy.ops.uv.zenuv_fit_to_trim_hotspot', 'trimsheet_operators/#hotspot-mapping'),
    ('bpy.ops.uv.zenuv_trim_select_by_face', 'trimsheet_operators/#select-trim-by-face'),
    ('bpy.ops.uv.zenuv_select_island_by_trim', 'trimsheet_operators/#select-islands-by-trim'),

    ('bpy.ops.uv.zuv_crop_trim', 'trimsheet_creation/#crop-trims'),
    ('bpy.ops.uv.zuv_align_trim', 'trimsheet_creation/#align-trims'),
    ('bpy.ops.uv.zuv_adjust_size_trim', 'trimsheet_creation/#adjust-trims'),
    ('bpy.ops.uv.zuv_distribute_trim', 'trimsheet_creation/#distribute-trims'),

    ('bpy.ops.wm.zenuv_set_props_to_trims', 'trimsheet_creation/#how-to-apply-same-settings-to-multiple-trims'),

    ('bpy.types.ZUV_UVToolProps.display_trims'.lower(), 'trimsheet_creation/#display-trims'),
    ('bpy.types.ZUV_UVToolProps.select_trim'.lower(), 'trimsheet_creation/#select-trim-in-the-viewport'),
    ('bpy.types.ZuvTrimsheetTransformProps.trim_transform_mode'.lower(), 'trimsheet_creation/#transform-trims'),
    ('bpy.types.ZuvTrimsheetGroup.*'.lower(), 'trimsheet_creation/#trim-settings'),
)


def zen_uv_addon_docs():
    return ZenPolls.doc_url, zen_uv_manual_map


def register():
    bpy.utils.register_manual_map(zen_uv_addon_docs)


def unregister():
    bpy.utils.unregister_manual_map(zen_uv_addon_docs)
