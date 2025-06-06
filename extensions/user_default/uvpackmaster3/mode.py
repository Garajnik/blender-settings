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


from .grouping import GroupingConfig
from .app_iface import *

import sys
from collections import defaultdict



class ModeType:
    HIDDEN = 0
    MAIN = 1
    UTIL = 2


class OperatorMetadata:

    def __init__(self, idname, label=None, properties=None, scale_y=1.0):
        self.idname = idname
        self.label = bpy_internal.ops.get_rna_type(idname).name if label is None else label
        self.properties = properties
        self.scale_y = scale_y

    def set_properties(self, op):
        if self.properties is None:
            return

        for prop, prop_value in self.properties:
            setattr(op, prop, prop_value)


class OperatorMetadataSeparator:
    pass



class UVPM3_Mode_Generic:

    MODE_PRIORITY = sys.maxsize
    MODE_TYPE = ModeType.HIDDEN
    MODE_HELP_URL_SUFFIX = None

    def subpanels_base(self):

        output = self.subpanels()
        return output

    def subpanels(self):

        return []

    def __init__(self, context):

        self.context = context
        self.scene_props = get_scene_props(context)
        self.prefs = get_prefs()
        self.op = None
        self.grouping_config = self.get_grouping_config()

    def get_grouping_config(self):
        return GroupingConfig(self.context)

    def pre_operation(self):
        pass

    def init_op(self, op):

        self.op = op
        self.pre_operation()

    def append_mode_name_to_op_label(self):
        return False
    
    def draw_operator(self, layout, op_metadata):

        row = layout.row(align=True)
        row.scale_y = op_metadata.scale_y
        label = op_metadata.label
        if self.append_mode_name_to_op_label() and self.prefs.append_mode_name_to_op_label:
            label = "{} ({})".format(label, self.MODE_NAME)

        from .panel import UVPM3_PT_Generic

        op = UVPM3_PT_Generic.operator_attach_mode(op_metadata.idname, self.MODE_ID, row, text=label)
        op_metadata.set_properties(op)

    def operators(self):

        output = []
        if hasattr(self, 'OPERATOR_IDNAME'):
            output.append(OperatorMetadata(self.OPERATOR_IDNAME))

        return output

    def draw(self, layout):

        operators = self.operators()

        if len(operators) == 0:
            return

        for op_metadata in operators:
            if isinstance(op_metadata, OperatorMetadataSeparator):
                layout.separator()
            else:
                self.draw_operator(layout, op_metadata)


class UVPM3_Mode_Main(UVPM3_Mode_Generic):

    MODE_TYPE = ModeType.MAIN

    @classmethod
    def enum_name(cls):
        return cls.MODE_NAME
    


class UVPM3_ModeCategory_Packing:

    PRIORITY = 1000
    NAME = 'Packing'

    
class UVPM3_ModeCategory_Miscellaneous:

    PRIORITY = 2000
    NAME = 'Miscellaneous'



class UVPM3_OT_SelectMode(Operator):

    bl_options = {'INTERNAL'}
    bl_idname = 'uvpackmaster3.select_mode'
    bl_label = 'Select Mode'
    bl_description = "Select active mode"

    mode_id : StringProperty(name='', description='', default='')

    def execute(self, context):
        get_prefs().set_active_main_mode(context, self.mode_id)
        return {'FINISHED'}


class UVPM3_MT_BrowseModes(Menu):
    bl_idname = "UVPM3_MT_BrowseModes"
    bl_label = "Modes"

    def draw(self, context):
        
        prefs = get_prefs()
        mode_list = prefs.get_modes(ModeType.MAIN)
        layout = self.layout

        modes_by_categories = defaultdict(list)
    
        for mode_id, mode_class in mode_list:
            modes_by_categories[mode_class.MODE_CATEGORY].append(mode_class)

        sorted_categories = sorted(modes_by_categories.keys(), key= lambda cat: cat.PRIORITY)

        for category in sorted_categories:
            layout.separator()
            layout.label(text=category.NAME)
            layout.separator()

            for mode_class in modes_by_categories[category]:
                operator = layout.operator(UVPM3_OT_SelectMode.bl_idname, text=mode_class.MODE_NAME)
                operator.mode_id = mode_class.MODE_ID
