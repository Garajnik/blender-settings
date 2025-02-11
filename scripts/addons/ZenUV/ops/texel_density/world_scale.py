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

# Copyright 2023, Valeriy Yatsenko, Alexander Zhornyak

import bpy

from ZenUV.utils.generic import (
    ZUV_SPACE_TYPE,
    ZUV_REGION_TYPE,
    ZUV_PANEL_CATEGORY,
    ZUV_CONTEXT)

from ..transform_sys.transform_utils.tr_utils import TransformSysOpsProps


class ZUV_PT_WorldScaleMaterial(bpy.types.Panel):
    bl_idname = "ZUV_PT_WorldScaleMaterial"
    bl_label = 'UV World Size Material'
    bl_context = "material"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout

        p_obj = context.active_object
        if p_obj:
            p_act_mat = p_obj.active_material
            if p_act_mat:
                col = layout.column(align=True)
                col.label(text=p_act_mat.zen_uv.bl_rna.properties['world_size_image'].name)
                col.prop(p_act_mat.zen_uv, 'world_size_image', text='')


class ZUV_PT_3DV_SubWorldSize(bpy.types.Panel):
    bl_label = "UV World Size"
    bl_context = ZUV_CONTEXT
    bl_space_type = ZUV_SPACE_TYPE
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_Texel_Density"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.mode == 'EDIT_MESH'

    @classmethod
    def poll_reason(cls, context: bpy.types.Context):
        if context.mode != 'EDIT_MESH':
            return 'Available in Edit Mesh Mode'
        return ''

    def draw(self, context: bpy.types.Context):

        def draw_world_size_operators(context, p_image, layout):
            r_scale = layout.row(align=True)
            r_scale.label(text='Size:')
            r_scale.prop(p_image.zen_uv.world_scale, 'scale', text='')
            r_scale.prop(context.scene.zen_uv, 'world_size_units', text='')

            row = layout.row(align=True)
            row.operator(ZUV_OT_GetWorldSize.bl_idname, text='Get').write_to_current_texture = True
            ot = row.operator(ZUV_OT_SetWorldSize.bl_idname, text='Set')
            ot.size = p_image.zen_uv.world_scale.scale
            ot.units = context.scene.zen_uv.world_size_units
            layout.operator(ZUV_OT_GetWorldSize.bl_idname, text='Calculate World Size').write_to_current_texture = False

        p_mat_image = None
        p_act_mat = None
        p_image = ZuvWorldScaleUtils.getActiveImage(context)
        b_is_UV = self.bl_space_type == 'IMAGE_EDITOR'
        if not b_is_UV:
            p_obj = context.active_object
            if p_obj:
                p_act_mat = p_obj.active_material
                if p_act_mat:
                    p_mat_image = p_act_mat.zen_uv.world_size_image

        layout = self.layout

        if p_image is not None:
            row = layout.row(align=True)
            box = row.box()
            r_line = box.row(align=True)
            r1 = r_line.row(align=True)
            r1.alert = p_mat_image is not None
            r1.label(text=p_image.name, icon='FILE_IMAGE')

            draw_world_size_operators(context, p_image, layout)

            if p_act_mat is not None:
                r2 = r_line.row(align=True)
                r2.alignment = 'RIGHT'
                r2.popover(panel='ZUV_PT_WorldScaleMaterial', text='', icon='PREFERENCES')

        else:
            layout.separator(factor=0.5)
            box = layout.box()
            if p_act_mat is not None:
                box.prop(p_act_mat.zen_uv, 'world_size_image', text='')

            row = box.row(align=True)
            row.alignment = 'CENTER'
            row.label(text='No active image', icon='ERROR')


class ZUV_PT_UVL_SubWorldSize(bpy.types.Panel):
    bl_label = ZUV_PT_3DV_SubWorldSize.bl_label
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = ZUV_REGION_TYPE
    bl_category = ZUV_PANEL_CATEGORY
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "ZUV_PT_UVL_Texel_Density"

    poll = ZUV_PT_3DV_SubWorldSize.poll

    poll_reason = ZUV_PT_3DV_SubWorldSize.poll_reason

    draw = ZUV_PT_3DV_SubWorldSize.draw


class ZuvWorldScaleUtils:

    @classmethod
    def getActiveImage(cls, context):
        from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils
        p_image = ZuvTrimsheetUtils.getSpaceDataImage(context)
        if p_image is not None:
            return p_image

        if hasattr(context, 'area') and context.area is not None and context.area.type != 'IMAGE_EDITOR':
            if context.active_object is not None:
                p_act_mat = context.active_object.active_material
                if p_act_mat is not None:
                    if p_act_mat.zen_uv.world_size_image is not None:
                        return p_act_mat.zen_uv.world_size_image

                    if p_act_mat.use_nodes:
                        # Priority for Base Color Texture
                        try:
                            principled = next(n for n in p_act_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
                            base_color = principled.inputs['Base Color']
                            link = base_color.links[0]
                            link_node = link.from_node
                            return link_node.image
                        except Exception:
                            pass

        return None


class ZUV_OT_SetWorldSize(bpy.types.Operator):
    bl_idname = "uv.zenuv_set_world_size"
    bl_label = "Set World Size"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Sets the size of the island so that the texture of this island in the scene fills the size specified in the Size field"

    size: bpy.props.FloatProperty(
        name='Size',
        description='Size value',
        min=0.001,
        default=1.0
    )
    units: TransformSysOpsProps.get_units_enum(description='World size units', default=1)
    island_pivot: bpy.props.EnumProperty(
            name='Island Pivot',
            description='The pivot point of the transformation',
            items=[
                ("br", 'Bottom-Right', '', 0),
                ("bl", 'Bottom-Left', '', 1),
                ("tr", 'Top-Right', '', 2),
                ("tl", 'Top-Left', '', 3),
                ("cen", 'Center', '', 4),
                ("rc", 'Right', '', 5),
                ("lc", 'Left', '', 6),
                ("bc", 'Bottom', '', 7),
                ("tc", 'Top', '', 8),
            ],
            default='cen'
        )
    align: bpy.props.BoolProperty(
        name='Align to UV Area',
        description='Align islands to the UV Area',
        default=False
    )
    align_direction: TransformSysOpsProps.get_align_direction(default=1)

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.label(text='Size: ')

        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(self, 'size', text='')
        row.prop(self, 'units', text='')

        row = layout.row(align=True)
        row.label(text='Island Pivot: ')
        row = row.row(align=True)
        row.prop(self, 'island_pivot', text='')

        box = layout.box()
        box.label(text='Postprocess:')
        m_row = box.row(align=True)
        m_row.prop(self, 'align')
        row = m_row.row(align=True)
        row.enabled = self.align
        row.prop(self, 'align_direction', text='')

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel, resort_objects_by_selection
        from ZenUV.ops.texel_density.td_utils import TdContext, TexelDensityProcessor, TexelDensityFactory
        from mathutils import Matrix, Vector

        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "Zen UV: There are no selected objects.")
            return {'CANCELLED'}

        objs = resort_objects_by_selection(context, objs)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        td_inputs = TdContext(context)

        p_image = ZuvWorldScaleUtils.getActiveImage(context)

        if p_image is not None:
            p_ref_size = p_image.zen_uv.world_scale.scale

            from ZenUV.utils.generic import UnitsConverter

            p_ref_image_size = p_image.size[:]

            p_ref_td = round(TexelDensityFactory._calc_referenced_td_world_size(p_ref_image_size, td_inputs)[0], 2) * UnitsConverter.rev_con[self.units]

            p_ma = Matrix.Diagonal(Vector.Fill(3, p_ref_size)).to_3x3()
            scalar = p_ma.inverted().median_scale

        else:
            self.report({'INFO'}, "No active image detected.")
            return {'CANCELLED'}

        td_inputs.td = p_ref_td * scalar
        td_inputs.td_set_pivot_name = self.island_pivot
        td_inputs.set_mode = 'ISLAND'
        td_inputs.image_size = p_ref_image_size

        TexelDensityProcessor.set_td(context, objs, td_inputs)

        if self.align:
            bpy.ops.uv.zenuv_align(
                influence_mode='ISLAND',
                op_order='ONE_BY_ONE',
                align_to='TO_UV_AREA',
                align_direction=self.align_direction,
                i_pivot_as_direction=True)

        return {'FINISHED'}


class ZUV_OT_GetWorldSize(bpy.types.Operator):
    bl_idname = "uv.zenuv_get_world_size"
    bl_label = "Get World Size"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Get the texture size in real units"

    size: bpy.props.FloatProperty(
        name='Size',
        description='Size value',
        min=0.001,
        default=1.0
    )
    units: TransformSysOpsProps.get_units_enum(description='World size units', default=1)
    write_to_current_texture: bpy.props.BoolProperty(
        name='Write to Texture',
        description='Write world size value to the active texture',
        default=False)

    def draw(self, context):
        layout = self.layout

        box = layout.box()

        row = box.row(align=True)
        row.label(text='Size: ')

        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(self, 'size', text='')
        row.prop(self, 'units', text='')
        layout.prop(self, 'write_to_current_texture')

    @classmethod
    def poll(cls, context):
        """ Validate context """
        active_object = context.active_object
        return active_object is not None and active_object.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        from ZenUV.utils.generic import resort_by_type_mesh_in_edit_mode_and_sel, resort_objects_by_selection
        from ZenUV.ops.texel_density.td_utils import TdContext, TexelDensityFactory
        from mathutils import Matrix, Vector

        objs = resort_by_type_mesh_in_edit_mode_and_sel(context)
        if not objs:
            self.report({'INFO'}, "Zen UV: There are no selected objects.")
            return {'CANCELLED'}

        objs = resort_objects_by_selection(context, objs)
        if not objs:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}

        td_inputs = TdContext(context)

        p_image = ZuvWorldScaleUtils.getActiveImage(context)

        if p_image is not None:

            if p_image.size[0] == 0 or p_image.size[1] == 0:
                self.report({'WARNING'}, "Zen UV: It looks like selected texture isn't loaded into the scene.")
                return {'CANCELLED'}

            from ZenUV.utils.generic import UnitsConverter

            p_ref_image_size = p_image.size[:]
            td_inputs.image_size = p_ref_image_size

            td_inputs.units = UnitsConverter.converter[self.units]
            p_input_td = TexelDensityFactory.get_texel_density(context, objs, td_inputs, precision=td_inputs.td_calc_precision)[0]

            p_ref_td = round(TexelDensityFactory._calc_referenced_td_world_size(p_ref_image_size, td_inputs)[0], 2)

        else:
            self.report({'INFO'}, "No active image detected.")
            return {'CANCELLED'}

        p_ma = Matrix.Diagonal(Vector.Fill(3, p_input_td / p_ref_td)).to_3x3()

        self.size = p_ma.inverted().median_scale * UnitsConverter.rev_con[self.units]

        if self.write_to_current_texture:
            p_image.zen_uv.world_scale
            if hasattr(p_image, 'zen_uv'):
                if hasattr(p_image.zen_uv, 'world_scale'):
                    p_image.zen_uv.world_scale.scale = self.size

        from ZenUV.ops.trimsheets.trimsheet import ZuvTrimsheetUtils
        ZuvTrimsheetUtils.fix_undo()

        self.report({'INFO'}, f"Image: {p_image.name} - Size: {round(self.size, 2)} {self.units}")

        return {'FINISHED'}


classes = (
    ZUV_PT_WorldScaleMaterial,
    ZUV_OT_SetWorldSize,
    ZUV_OT_GetWorldSize
)


def register_world_scale():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_world_scale():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
