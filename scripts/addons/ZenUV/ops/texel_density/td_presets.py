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

""" Zen Texel Density Presets System """

import bpy
import bmesh
from mathutils import Color

from ZenUV.ui.labels import ZuvLabels
from ZenUV.utils.generic import (
    ZUV_PANEL_CATEGORY,
    ZUV_REGION_TYPE,
    ZUV_CONTEXT,
    ZUV_SPACE_TYPE,
    resort_objects_by_selection,
    get_mesh_data,
    remap_ranges
)

from ZenUV.ops.texel_density.td_utils import (
    TdContext,
    TexelDensityFactory,
    TexelDensityProcessor
)
from pathlib import Path
from ZenUV.ui.ui_call import popup_areas

from ZenUV.utils.blender_zen_utils import ZuvPresets
from bl_operators.presets import AddPresetBase, ExecutePreset
from bpy.app.translations import (
    pgettext_tip as tip_,
)
from ZenUV.utils.tests.system_operators import ZUV_OT_OpenPresetsFolder
from .td_props import TdProps

from ZenUV.utils.vlog import Log


PRESET_NEW = {"name": "new", "value": 10.24, "color": [0.03, 0.3, 0.4]}
TD_PRESET_SUBDIR = 'texel_density_presets'
LITERAL_DRIVER_PRESETS_LIST = 'zen_uv_tdpr_list'


class ZUV_OT_TdExecutePreset(bpy.types.Operator):
    bl_idname = "uv.zuv_execute_td_preset"

    bl_label = 'Load Texel Density Preset'
    bl_description = "Load Texel Density preset from file"

    # Do not use 'UNDO' here!
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE', 'HIDDEN'},
    )

    # we need this to prevent 'getattr()' is None
    menu_idname: bpy.props.StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE', 'HIDDEN'},
        default='ZUV_MT_StoreTdPresets'
    )

    load_units: bpy.props.BoolProperty(
        name='Load TD Units and Texture Size',
        description='Load and apply texel density calculation units and texture size',
        default=False
    )

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.prop(self, 'load_units')

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        from .td_display_utils import TdSysUtils

        p_scene = context.scene

        t_were_scene_props = {
            'td_im_size_presets': None,
            'TD_TextureSizeX': None,
            'TD_TextureSizeY': None,
            'td_unit': None
        }

        for s_prop in t_were_scene_props.keys():
            p_scene_prop = getattr(p_scene.zen_uv.td_props, s_prop)
            t_were_scene_props[s_prop] = p_scene_prop

        # Use this method because if it is inherited, can not change Blender theme !
        res = ExecutePreset.execute(self, context)

        TdSysUtils.update_display_presets(context)

        if not self.load_units:
            for s_prop, val in t_were_scene_props.items():
                setattr(p_scene.zen_uv.td_props, s_prop, val)

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        bpy.ops.ed.undo_push(message='Load TD Preset')

        return res


class ZUV_MT_StoreTdPresets(bpy.types.Menu):
    bl_label = 'TD Presets'

    default_label = 'Texel Density Presets'

    preset_subdir = ZuvPresets.get_preset_path(TD_PRESET_SUBDIR)
    preset_operator = 'uv.zuv_execute_td_preset'

    draw = bpy.types.Menu.draw_preset


class ZUV_OT_TdAddPreset(AddPresetBase, bpy.types.Operator):
    bl_idname = 'uv.zuv_add_td_preset'
    bl_label = 'Add|Remove Preset'
    preset_menu = 'ZUV_MT_StoreTdPresets'

    @classmethod
    def description(cls, context, properties):
        return ('Remove' if properties.remove_active else 'Add') + ' trimsheet preset'

    # Common variable used for all preset values
    preset_defines = [
        'prefs = bpy.context.scene'
    ]

    # Properties to store in the preset
    preset_values = [
        'prefs.zen_tdpr_list',
        'prefs.zen_tdpr_list_index',

        'prefs.zen_uv.td_props.td_unit',
        'prefs.zen_uv.td_props.td_im_size_presets',
        'prefs.zen_uv.td_props.TD_TextureSizeX',
        'prefs.zen_uv.td_props.TD_TextureSizeY',
    ]

    # Directory to store the presets
    preset_subdir = ZuvPresets.get_preset_path(TD_PRESET_SUBDIR)

    def execute(self, context):
        import os
        from bpy.utils import is_path_builtin

        if hasattr(self, "pre_cb"):
            self.pre_cb(context)

        preset_menu_class = getattr(bpy.types, self.preset_menu)

        is_xml = getattr(preset_menu_class, "preset_type", None) == 'XML'
        is_preset_add = not (self.remove_name or self.remove_active)

        if is_xml:
            ext = ".xml"
        else:
            ext = ".py"

        name = self.name.strip() if is_preset_add else self.name

        if is_preset_add:
            if not name:
                self.report({'WARNING'}, 'Preset name is empty!')
                return {'FINISHED'}

            # Reset preset name
            wm = bpy.data.window_managers[0]
            if name == wm.preset_name:
                wm.preset_name = 'New Preset'

            filename = self.as_filename(name)

            target_path = os.path.join("presets", self.preset_subdir)
            target_path = bpy.utils.user_resource('SCRIPTS', path=target_path, create=True)

            if not target_path:
                self.report({'WARNING'}, "Failed to create presets path")
                return {'CANCELLED'}

            filepath = os.path.join(target_path, filename) + ext

            if hasattr(self, "add"):
                self.add(context, filepath)
            else:
                print("Writing Preset: %r" % filepath)

                if is_xml:
                    import rna_xml
                    rna_xml.xml_file_write(context,
                                           filepath,
                                           preset_menu_class.preset_xml_map)
                else:

                    def rna_recursive_attr_expand(value, rna_path_step, level):
                        if isinstance(value, bpy.types.PropertyGroup):
                            for sub_value_attr, sub_value_prop in value.bl_rna.properties.items():
                                if sub_value_attr == "rna_type":
                                    continue
                                if sub_value_prop.is_skip_save:
                                    continue
                                sub_value = getattr(value, sub_value_attr)
                                rna_recursive_attr_expand(sub_value, "%s.%s" % (rna_path_step, sub_value_attr), level)
                        elif type(value).__name__ == "bpy_prop_collection_idprop":  # could use nicer method
                            file_preset.write("%s.clear()\n" % rna_path_step)
                            for sub_value in value:
                                file_preset.write("item_sub_%d = %s.add()\n" % (level, rna_path_step))
                                rna_recursive_attr_expand(sub_value, "item_sub_%d" % level, level + 1)
                        else:
                            # convert thin wrapped sequences
                            # to simple lists to repr()
                            try:
                                value = value[:]
                            except Exception:
                                pass

                            file_preset.write("%s = %r\n" % (rna_path_step, value))

                    file_preset = open(filepath, 'w', encoding="utf-8")
                    file_preset.write("import bpy\n")

                    if hasattr(self, "preset_defines"):
                        for rna_path in self.preset_defines:
                            exec(rna_path)
                            file_preset.write("%s\n" % rna_path)
                        file_preset.write("\n")

                    for rna_path in self.preset_values:
                        value = eval(rna_path)
                        rna_recursive_attr_expand(value, rna_path, 1)

                    file_preset.close()

            preset_menu_class.bl_label = Path(filename).stem

        else:
            if self.remove_active:
                name = preset_menu_class.bl_label

            # fairly sloppy but convenient.
            filepath = bpy.utils.preset_find(name,
                                             self.preset_subdir,
                                             ext=ext)

            if not filepath:
                filepath = bpy.utils.preset_find(name,
                                                 self.preset_subdir,
                                                 display_name=True,
                                                 ext=ext)

            if not filepath:
                self.report({'WARNING'}, f'Preset: {name} - not found!')
                return {'CANCELLED'}

            # Do not remove bundled presets
            if is_path_builtin(filepath):
                self.report({'WARNING'}, "Unable to remove default presets")
                return {'CANCELLED'}

            try:
                if hasattr(self, "remove"):
                    self.remove(context, filepath)
                else:
                    os.remove(filepath)
            except Exception as e:
                self.report({'ERROR'}, tip_("Unable to remove preset: %r") % e)
                import traceback
                traceback.print_exc()
                return {'CANCELLED'}

            preset_menu_class.bl_label = preset_menu_class.default_label

        if hasattr(self, "post_cb"):
            self.post_cb(context)

        context.area.tag_redraw()

        return {'FINISHED'}


def do_draw_preset(layout: bpy.types.UILayout):
    row = layout.row(align=True)

    preset_menu_class = getattr(bpy.types, 'ZUV_MT_StoreTdPresets')
    row.menu("ZUV_MT_StoreTdPresets", text=preset_menu_class.bl_label)

    s_preset_name = preset_menu_class.bl_label

    op = row.operator("uv.zuv_add_td_preset", text="", icon="ADD")
    if s_preset_name and s_preset_name != preset_menu_class.default_label:
        op.name = s_preset_name
    op = row.operator("uv.zuv_add_td_preset", text="", icon="REMOVE")
    op.remove_active = True
    row.operator(
        ZUV_OT_OpenPresetsFolder.bl_idname,
        icon=ZUV_OT_OpenPresetsFolder.get_icon_name(),
        text='').preset_folder = TD_PRESET_SUBDIR


def draw_presets(self: bpy.types.Panel, context: bpy.types.Context):
    layout = self.layout
    scene = context.scene
    do_draw_preset(layout)

    from .td_ui import draw_td_global_preset

    row = layout.row(align=True)
    row.operator(
        TDPR_OT_Get.bl_idname,
        # icon='IMPORT',
        text='Get TD')
    row.operator(
        TDPR_OT_Set.bl_idname,
        # icon='EXPORT',
        text='Set TD')
    row.separator()
    row.operator(TDPR_OT_Clear.bl_idname, icon='TRASH', text="")

    row = layout.row()
    col = row.column()
    col.template_list(
        "TDPR_UL_List",
        "name",
        scene,
        "zen_tdpr_list",
        scene,
        "zen_tdpr_list_index",
        rows=6
    )

    col = row.column(align=True)
    col.operator(TDPR_OT_NewItem.bl_idname, text="", icon='ADD')
    col.operator(TDPR_OT_DeleteItem.bl_idname, text="", icon='REMOVE')
    col.separator()

    col.menu(menu='ZUV_MT_TdPresetsMenu', text='', icon='DOWNARROW_HLT')
    col.separator()

    p_td_uilist = None
    b_use_order_value = False

    try:
        t_td_presets_lists = bpy.app.driver_namespace.get(LITERAL_DRIVER_PRESETS_LIST, {})
        p_td_uilist = t_td_presets_lists.get(context.area.as_pointer(), None)
        b_use_order_value = p_td_uilist.use_order_value
    except Exception as e:
        # This may happen and is normal
        Log.error('TD PRESETS:', e)
        p_td_uilist = None

    col_arrows = col.column(align=True)
    col_arrows.active = not b_use_order_value
    col_arrows.operator(TDPR_OT_MoveItem.bl_idname, text="", icon='TRIA_UP').direction = 'UP'
    col_arrows.operator(TDPR_OT_MoveItem.bl_idname, text="", icon='TRIA_DOWN').direction = 'DOWN'
    col.separator()

    try:
        if p_td_uilist:
            col.prop(p_td_uilist, 'use_order_value', text='', toggle=True, icon='LINENUMBERS_ON')
    except Exception as e:
        # This may happen and is normal
        Log.error('TD PRESETS:', e)

    col = layout.column(align=True)
    # col.operator(TDPR_OT_Set.bl_idname, icon='EXPORT')
    row = col.row(align=True)
    row.prop(scene.zen_uv.td_props, "td_select_type", text="")
    row.separator()
    # op_sel_by_td = row.operator("zen_tdpr.select_by_texel_density", text="", icon="RESTRICT_SELECT_OFF")
    row.operator(TDPR_OT_SelectByTd.bl_idname, icon="RESTRICT_SELECT_OFF", text='')

    draw_td_global_preset(context, layout)


def remap_ranges_to_color(value, base_range, begin_color, finish_color):
    # print(begin_color)
    # print(finish_color)
    output = []
    for i in range(3):
        output.append(remap_ranges(value, base_range, (begin_color[i], finish_color[i])))
    return Color(output)


def new_list_item(context):
    from .td_display_utils import TdSysUtils

    scene = context.scene
    scene.zen_tdpr_list.add()
    name = PRESET_NEW["name"]
    value = PRESET_NEW["value"]
    color = PRESET_NEW["color"]
    i = 1

    while name in scene.zen_tdpr_list:
        name = f"{PRESET_NEW['name']}_{str(i)}"
        i = i + 1

    scene.zen_tdpr_list[-1].name = name
    scene.zen_tdpr_list[-1].value = value
    scene.zen_tdpr_list[-1].display_color = color
    scene.zen_tdpr_list_index = len(scene.zen_tdpr_list) - 1

    TdSysUtils.update_display_presets(context)


def select_by_td(context, td_set, texel_density, treshold):
    for c_td, data in td_set.items():
        if texel_density - treshold < c_td < texel_density + treshold:
            for obj_name in data["objs"]:
                obj = context.scene.objects[obj_name]
                me, bm = get_mesh_data(obj)
                bm.faces.ensure_lookup_table()
                for island in data["objs"][obj_name]:
                    for f in island:
                        bm.faces[f].select = True
                bmesh.update_edit_mesh(me)


class TDPRListGroup(bpy.types.PropertyGroup):
    """
    Group of properties representing
    an item in the zen TD Presets groups.
    """

    name: bpy.props.StringProperty(
        name="Name",
        description="A name for this item",
        default="new"
    )
    value: bpy.props.FloatProperty(
        name="Value",
        description="Texel Density Value",
        default=10.24,
        update=TdProps.update_td_draw_force
    )
    display_color: bpy.props.FloatVectorProperty(
        name="Color",
        description="Color to display the density of texels",
        subtype='COLOR',
        default=[0.316, 0.521, 0.8],
        size=3,
        min=0,
        max=1
    )


class TDPR_UL_List(bpy.types.UIList):
    ''' Zen TD Presets UIList '''

    # This allows us to have mutually exclusive options, which are also all disable-able!
    def _gen_order_update(name1, name2):
        def _u(self, ctxt):
            if (getattr(self, name1)):
                setattr(self, name2, False)
        return _u
    use_order_name: bpy.props.BoolProperty(
        name="Name", default=False, options=set(),
        description="Sort items by their name (case-insensitive)",
        update=_gen_order_update("use_order_name", "use_order_value"),
    )
    use_order_value: bpy.props.BoolProperty(
        name="Value",
        default=True,
        options=set(),
        description="Sort items by their value",
        update=_gen_order_update("use_order_value", "use_order_name"),
    )

    use_filter_show: bpy.props.BoolProperty(
        name='Show Filter',
        default=True
    )

    def filter_items(self, context: bpy.types.Context, data, propname):
        p_list = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        t_td_presets_lists = bpy.app.driver_namespace.get(LITERAL_DRIVER_PRESETS_LIST, {})
        t_td_presets_lists[context.area.as_pointer()] = self
        bpy.app.driver_namespace[LITERAL_DRIVER_PRESETS_LIST] = t_td_presets_lists

        # Default return values.
        flt_flags = []
        flt_neworder = []

        if self.use_filter_show:
            # Filtering by name
            if self.filter_name:
                flt_flags = helper_funcs.filter_items_by_name(
                    self.filter_name, self.bitflag_filter_item, p_list, "name",
                    reverse=False)
            if not flt_flags:
                flt_flags = [self.bitflag_filter_item] * len(p_list)

            # Reorder by name or value
            if self.use_order_name:
                _sort = [(idx, item.name) for idx, item in enumerate(p_list)]
                flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1])
            elif self.use_order_value:
                _sort = [(idx, item.value) for idx, item in enumerate(p_list)]
                flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1])

        return flt_flags, flt_neworder

    def draw_filter(self, context: bpy.types.Context, layout: bpy.types.UILayout):
        # Nothing much to say here, it's usual UI code...
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")
        subrow.prop(self, "use_filter_invert", text="", icon='ARROW_LEFTRIGHT')

        subrow = row.row(align=True)
        subrow.prop(self, "use_order_name", text='', toggle=True, icon='SORTALPHA')
        subrow.prop(self, "use_order_value", text='', toggle=True, icon='LINENUMBERS_ON')

        icon_id = 'SORT_DESC' if self.use_filter_sort_reverse else 'SORT_ASC'
        row.prop(self, "use_filter_sort_reverse", text='', toggle=True, icon=icon_id)

    def draw_item(self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index):
        ''' @Draw TD Presets UIList '''
        custom_icon = 'OBJECT_DATAMODE'

        act_idx = getattr(active_data, active_propname)
        b_active = index == act_idx

        b_emboss = (context.area.as_pointer() in popup_areas) and b_active

        # Make sure code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            row.separator(factor=1)

            subrow = row.row(align=True)
            subrow.alignment = 'LEFT'

            col = subrow.column()
            col.ui_units_x = 0.7
            col.separator(factor=0.8)

            col.scale_y = 0.6
            col.prop(item, 'display_color', text='')

            r = row.row(align=True)
            r1 = r.row(align=True)
            r1.prop(item, 'name', text='', emboss=b_emboss, icon='NONE')

            r2 = r.row(align=True)
            r2.alignment = 'EXPAND'  # NOTE: Optional 'RIGHT', 'LEFT'
            r2.prop(item, "value", text="", emboss=True)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, 'name', text="", emboss=False, icon=custom_icon)


class ZUV_PT_ZenTDPresets(bpy.types.Panel):
    """  Zen TD Presets Panel """
    bl_label = "Presets"
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Texel_Density"
    bl_idname = "ZUV_PT_ZenTDPresets"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        return 'Available in Edit Mode'

    def draw(self, context):
        draw_presets(self, context)


class ZUV_PT_UVL_ZenTDPresets(bpy.types.Panel):
    bl_parent_id = "ZUV_PT_UVL_Texel_Density"
    bl_space_type = "IMAGE_EDITOR"
    bl_idname = "ZUV_PT_ZenTDPresetsUV"
    bl_label = ZuvLabels.PANEL_TDPR_LABEL
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY

    poll = ZUV_PT_ZenTDPresets.poll

    poll_reason = ZUV_PT_ZenTDPresets.poll_reason

    def draw(self, context):
        draw_presets(self, context)


class TDPR_OT_NewItem(bpy.types.Operator):
    """Add a new item to the list."""
    bl_description = ZuvLabels.OT_SGL_NEW_ITEM_DESC
    bl_idname = "zen_tdpr.new_item"
    bl_label = ZuvLabels.OT_SGL_NEW_ITEM_LABEL
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        new_list_item(context)

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        return {'FINISHED'}


class TDPR_OT_DeleteItem(bpy.types.Operator):
    """Delete the selected item from the list."""
    bl_description = ZuvLabels.OT_SGL_DEL_ITEM_DESC
    bl_idname = "zen_tdpr.delete_item"
    bl_label = ZuvLabels.OT_SGL_DEL_ITEM_LABEL
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.zen_tdpr_list

    def execute(self, context):
        from .td_display_utils import TdSysUtils

        scene = context.scene
        list_index = scene.zen_tdpr_list_index
        if list_index in range(len(scene.zen_tdpr_list)):
            zen_tdpr_list = scene.zen_tdpr_list
            index = scene.zen_tdpr_list_index
            if index in range(len(scene.zen_tdpr_list)):
                zen_tdpr_list.remove(index)
                scene.zen_tdpr_list_index = min(max(0, index - 1), len(zen_tdpr_list) - 1)

        TdSysUtils.update_display_presets(context)

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        return {'FINISHED'}


class TDPR_OT_MoveItem(bpy.types.Operator):
    """Move an item in the list."""
    bl_idname = "zen_tdpr.move_item"
    bl_label = ZuvLabels.OT_SGL_MOVE_ITEM_LABEL
    bl_description = ZuvLabels.OT_SGL_MOVE_ITEM_DESC
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=(
            ('UP', 'Up', ""),
            ('DOWN', 'Down', ""),
        )
    )

    @classmethod
    def poll(cls, context):
        return context.scene.zen_tdpr_list

    def move_index(self, context):
        """ Move index of an item render queue while clamping it. """
        index = context.scene.zen_tdpr_list_index
        list_length = len(context.scene.zen_tdpr_list) - 1
        # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        context.scene.zen_tdpr_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        zen_tdpr_list = context.scene.zen_tdpr_list
        index = context.scene.zen_tdpr_list_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        zen_tdpr_list.move(neighbor, index)
        self.move_index(context)

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        return {'FINISHED'}


class TDPR_OT_Set(bpy.types.Operator):
    """ Set TD from active preset to selected Islands """
    bl_idname = "zen_tdpr.set_td_from_preset"
    bl_label = ZuvLabels.OT_TDPR_SET_LABEL
    bl_description = ZuvLabels.OT_TDPR_SET_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = resort_objects_by_selection(context, context.objects_in_mode)
        if not objs:
            return {'CANCELLED'}
        scene = context.scene
        list_index = scene.zen_tdpr_list_index
        if list_index in range(len(scene.zen_tdpr_list)):
            td_inputs = TdContext(context)
            td_inputs.td = scene.zen_tdpr_list[list_index].value
            TexelDensityProcessor.set_td(context, objs, td_inputs)

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        return {'FINISHED'}


class TDPR_OT_Get(bpy.types.Operator):
    """ Get TD from selected Islands to active preset """
    bl_idname = "zen_tdpr.get_td_from_preset"
    bl_label = ZuvLabels.OT_TDPR_GET_LABEL
    bl_description = ZuvLabels.OT_TDPR_GET_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .td_display_utils import TdSysUtils

        objs = resort_objects_by_selection(context, context.objects_in_mode)
        if not objs:
            self.report({'INFO'}, 'Nothing selected!')
            return {'CANCELLED'}

        scene = context.scene
        list_index = scene.zen_tdpr_list_index
        if list_index not in range(len(scene.zen_tdpr_list)):
            new_list_item(context)
        td_inputs = TdContext(context)
        scene.zen_tdpr_list[list_index].value, tmp = TexelDensityFactory.get_texel_density(context, objs, td_inputs)

        TdSysUtils.update_display_presets(context)

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        return {'FINISHED'}


class TDPR_OT_Clear(bpy.types.Operator):
    """ Clear Presets List """
    bl_idname = "zen_tdpr.clear_presets"
    # bl_label = ZuvLabels.OT_TDPR_CLEAR_DESC
    bl_description = ZuvLabels.OT_TDPR_CLEAR_LABEL

    bl_label = 'You are about to Clear preset list'

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        from .td_display_utils import TdSysUtils

        scene = context.scene
        scene.zen_tdpr_list.clear()
        scene.zen_tdpr_list_index = -1

        TdSysUtils.update_display_presets(context)

        return {'FINISHED'}


class TDPR_OT_SelectByTd(bpy.types.Operator):
    """ Select Islands By Texel Density Presets"""
    bl_idname = "zen_tdpr.select_by_td_presets"
    bl_label = 'Select by TD'
    bl_description = 'Select Islands By Texel Density Presets'
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context: bpy.types.Context):
        props = context.scene.zen_uv.td_props

        if len(context.scene.zen_tdpr_list) == 0:
            self.report({'WARNING'}, 'Zen UV: Preset list is Empty')
            return {'CANCELLED'}

        if props.td_select_type == 'UNDERRATED':
            bpy.ops.uv.zenuv_select_by_texel_density(
                'INVOKE_DEFAULT',
                influence='ISLAND',
                selection_mode='SKIP',
                sel_underrated=True,
                sel_overrated=False,
                clear_selection=True)
        elif props.td_select_type == 'OVERRATED':
            bpy.ops.uv.zenuv_select_by_texel_density(
                'INVOKE_DEFAULT',
                influence='ISLAND',
                selection_mode='SKIP',
                sel_underrated=False,
                sel_overrated=True,
                clear_selection=True)
        elif props.td_select_type == 'BY_VALUE':
            list_index = context.scene.zen_tdpr_list_index
            if list_index not in range(len(context.scene.zen_tdpr_list)):
                return {'FINISHED'}
            bpy.ops.uv.zenuv_select_by_texel_density(
                'INVOKE_DEFAULT',
                influence='ISLAND',
                selection_mode='TRESHOLD',
                texel_density=context.scene.zen_tdpr_list[list_index].value,
                treshold=0.01,
                sel_underrated=False,
                sel_overrated=False,
                clear_selection=True)

        return {'FINISHED'}


class ZUV_MT_TdPresetsMenu(bpy.types.Menu):
    bl_label = "ZenUV TD Presets Menu"

    def draw(self, context):
        from .td_tools import TDPR_OT_CreatePresets, TDPR_OT_ColorizePresets
        layout = self.layout
        layout.operator(TDPR_OT_CreatePresets.bl_idname)
        layout.operator(TDPR_OT_ColorizePresets.bl_idname)


TDPR_classes = (
    ZUV_MT_StoreTdPresets,
    ZUV_OT_TdAddPreset,
    ZUV_OT_TdExecutePreset,
    TDPR_UL_List,
    TDPR_OT_NewItem,
    TDPR_OT_DeleteItem,
    TDPR_OT_Set,
    TDPR_OT_Get,
    TDPR_OT_MoveItem,
    TDPR_OT_SelectByTd,
    TDPR_OT_Clear,
    ZUV_MT_TdPresetsMenu,
)


if __name__ == "__main__":
    pass
