import bpy
from .. icons import get_icon_id
from .. utils.addons import addon_exists
from .. utils.objects import get_current_selected_status
from .. utility import addon
from .. import bl_info


class HOPS_MT_MainMenu(bpy.types.Menu):
    bl_idname = "HOPS_MT_MainMenu"
    #bl_label = "Hard Ops 0098"
    bl_label = f"HOps: {bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}.{bl_info['version'][3]}"

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object
        wm = context.window_manager

        if active_object is None:
            self.draw_without_active_object(layout)
            layout.separator()
            self.draw_always(layout)

        elif len(bpy.context.selected_objects) == 0 and active_object.mode == "OBJECT":
            self.draw_without_active_object(layout)
            layout.separator()
            #layout.label(text='No Selection', icon='ERROR')
            self.draw_always(layout)

        elif active_object.mode == "OBJECT":
            if active_object.hops.status == "BOOLSHAPE":
                self.draw_boolshape_menu(layout)
                #self.draw_always(layout)
            elif active_object.hops.status == "BOOLSHAPE2":
                self.draw_boolshape_menu(layout)
                #self.draw_always(layout)
            #elif active_tool().idname == "Hops":
            #    self.draw_curve_menu(layout)
            else:
                if active_object.type == "LATTICE":
                    self.draw_lattice_menu(layout)
                    self.draw_always(layout)
                elif active_object.type == "CURVE":
                    self.draw_curve_menu(layout)
                    self.draw_always(layout)
                elif active_object.type == "FONT":
                    self.draw_font_menu(layout)
                    self.draw_always(layout)
                elif active_object.type == "LIGHT":
                    self.draw_lamp_menu(layout)
                    self.draw_always(layout)
                elif active_object.type == "CAMERA":
                    self.draw_camera_menu(context, layout)
                    self.draw_always(layout)
                elif active_object.type in {"GPENCIL", "GREASEPENCIL"}:
                    self.draw_gpencil_menu(layout)
                    self.draw_always(layout)
                elif active_object.type == "EMPTY":
                    #col = layout.column()
                    self.draw_only_with_active_object_is_empty(layout)
                    self.draw_always(layout)
                elif active_object.type in {'SPEAKER', 'VOLUME', 'ARMATURE', 'LIGHT_PROBE', 'SURFACE', 'META'}:
                    layout.label(text='Not yet', icon='ERROR')
                    self.draw_always(layout)
                else:
                    self.draw_object_mode_menu(layout)
        elif active_object.mode == "EDIT":
            if bpy.context.object.type == 'MESH':
                self.draw_edit_mode_menu(layout, active_object)
            if bpy.context.object.type == 'CURVE':
                #self.draw_edit_mode_curve_menu(layout, active_object)
                layout.label(text='Not yet', icon='ERROR')
            #else:
                #layout.label(text='Not yet', icon='ERROR')
        elif active_object.mode == "POSE":
            self.draw_rigging_menu(layout)
        elif active_object.mode == "SCULPT":
            self.draw_sculpt_menu(layout)
            layout.menu("HOPS_MT_ViewportSubmenu", text="ViewPort", icon_value=get_icon_id("Viewport"))
            #self.draw_always(layout)
        elif active_object.mode == "PAINT_GPENCIL":
            self.draw_pencil_menu(layout)
            self.draw_always(layout)
        #if bpy.context.object.type == 'MESH' and active_object.mode == "OBJECT":
        if asset_loader_unlock():
            layout.separator()
            layout.operator("view3d.insertpopup", text ="(Z) Asset Loader" if addon.preference().property.add_prefix else "Asset Loader", icon_value=get_icon_id("QGui"))
            layout.separator()
                #layout.operator("hops.kit_ops_window", text = "KitOps_ST3", icon_value=get_icon_id("kit_ops"))
        layout.separator()
        layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon_value=get_icon_id("QuickFav"))

        # if addon.preference().needs_update:
        #     layout.separator()
        #     #layout.label(text=addon.preference().needs_update, icon='ERROR')
        #     layout.operator("wm.url_open", text=addon.preference().needs_update, icon="ERROR").url = "https://hardops-manual.readthedocs.io/en/latest/faq/#how-do-i-update-hard-ops-boxcutter"

        # self.draw_always(layout)

    # Without Selection
    ############################################################################

    def draw_without_active_object(self, layout):
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.camera_rig", text="Add Camera", icon='OUTLINER_OB_CAMERA')
        layout.operator("hops.blank_light", text="Add Lights", icon='LIGHT')
        layout.operator("hops.timer", text="hTimer", icon="TIME")
        #layout.operator("hops.sculpt_primitives", text="Add Primitive", icon_value=get_icon_id("QGui"))
        layout.separator()
        if addon.preference().property.accushape_type == 'V2':
            layout.operator("hops.accu_shape_v2", text="AccuShape V2", icon_value=get_icon_id("grey"))
        else:
            layout.operator("hops.accu_shape", text="AccuShape", icon_value=get_icon_id("grey"))
        layout.separator()
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))
        #layout.menu('HOPS_MT_ViewportSubmenu', text="ViewPort", icon_value=get_icon_id("WireMode"))
#        wm = bpy.context.window_manager
#        layout.template_icon_view(wm, "Hard_Ops_previews")
#        layout.template_icon_view(wm, "sup_preview")
#        if addon_exists("MESHmachine"):
#            # layout.template_icon_view(wm, "pluglib_")
#            layout.separator()
#            layout.menu("machin3.mesh_machine_plug_libraries", text="Machin3")
#            layout.menu("machin3.mesh_machine_plug_utils_menu", text="Plug Utils")

    # Always
    ############################################################################

    def draw_always(self, layout):
        layout.separator()
        #layout.menu("HOPS_MT_RenderSetSubmenu", text="RenderSets", icon_value=get_icon_id("StatusOveride"))
        layout.menu("HOPS_MT_ViewportSubmenu", text="ViewPort", icon_value=get_icon_id("WireMode"))
        layout.menu("HOPS_MT_SettingsSubmenu", text="Settings", icon_value=get_icon_id("Settings"))
        #if asset_loader_unlock():
            #layout.operator("view3d.insertpopup", text = "Asset Loader", icon_value=get_icon_id("QGui"))

    # Object Mode
    ############################################################################

    def draw_object_mode_menu(self, layout):
        active_object, other_objects, other_object = get_current_selected_status()
        only_meshes_selected = all(object.type == "MESH" for object in bpy.context.selected_objects)

        object = bpy.context.active_object

        if len(bpy.context.selected_objects) == 1:
            if object.hops.status in ("CSHARP", "CSTEP"):
                if active_object is not None and other_object is None and only_meshes_selected:
                        self.draw_only_with_active_object_is_csharpen(layout, active_object)
            if object.hops.status == "UNDEFINED":
                if active_object is not None and other_object is None and only_meshes_selected:
                    if active_object.name.startswith("AP_"):
                        self.draw_only_with_AP_as_active_object(layout, active_object)
                    #Thin Objects Addition for 2d Bevel
                    elif active_object.dimensions[2] == 0 or active_object.dimensions[1] == 0 or active_object.dimensions[0] == 0:
                        self.draw_thin_object(layout)
                    else:
                        self.draw_only_with_active_object(layout, active_object)
            self.draw_options(layout)

        elif len(bpy.context.selected_objects) >= 2:
            self.draw_with_active_object_and_other_mesh(layout, active_object, other_object)
            self.draw_options(layout)

        else:
            self.draw_without_active_object(layout)
            layout.separator()
            layout.menu("HOPS_MT_SettingsSubmenu", text="Settings", icon_value=get_icon_id("Settings"))

    def draw_only_with_AP_as_active_object(self, layout, object):
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.copy_merge", text="Copy Merge", icon_value=get_icon_id("Merge"))
        layout.operator("hops.remove_merge", text="coming soon", icon_value=get_icon_id("Merge"))
        layout.operator("hops.remove_merge", text="Remove Merge", icon_value=get_icon_id("Merge"))
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        layout.operator("hops.array_gizmo", text="Array", icon_value=get_icon_id("Array"))

    def draw_only_with_active_object(self, layout, object):
        object = bpy.context.active_object

        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.sharpen", text="Sharpen", icon_value=get_icon_id("SSharpen"))
        layout.operator("hops.adjust_bevel", text="(W) Bevel" if addon.preference().property.add_prefix else "Bevel", icon_value=get_icon_id("AdjustBevel"))
        if object.hops.is_pending_boolean:
            layout.operator_context = "INVOKE_DEFAULT"
            #layout.operator("hops.adjust_bevel", text="Bevel", icon_value=get_icon_id("AdjustBevel"))

            #layout.operator("hops.scroll_multi", text="Mod Scroll/Toggle", icon_value=get_icon_id("StatusReset"))
            layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))

            #layout.operator("hops.bool_scroll_objects", text="Object Scroll", icon_value=get_icon_id("StatusReset"))
            #layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
        else:
            #layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
            #layout.operator("hops.adjust_tthick", text="(T) Thick", icon_value=get_icon_id("Tthick"))
            layout.operator_context = "INVOKE_DEFAULT"
            #layout.operator("hops.sharpen", text="Sharpen", icon_value=get_icon_id("SSharpen"))
            #layout.operator("hops.adjust_bevel", text="Bevel", icon_value=get_icon_id("AdjustBevel"))
            layout.operator("hops.st3_array", text="(E) Array V2" if addon.preference().property.add_prefix else "Array V2", icon_value=get_icon_id("GreyArrayX"))
            if object.hops.is_pending_boolean:
                layout.operator_context = "INVOKE_DEFAULT"
                #layout.operator("hops.adjust_bevel", text="Bevel", icon_value=get_icon_id("AdjustBevel"))

                # layout.operator("hops.scroll_multi", text="Mod Scroll/Toggle", icon_value=get_icon_id("StatusReset"))
                layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))

                #layout.operator("hops.bool_scroll_objects", text="Object Scroll", icon_value=get_icon_id("StatusReset"))
                #layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
            else:
                #layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
                #layout.operator("hops.adjust_tthick", text="(T) Thick", icon_value=get_icon_id("Tthick"))
                layout.operator_context = "INVOKE_DEFAULT"
                #layout.operator("hops.adjust_bevel", text="Bevel", icon_value=get_icon_id("AdjustBevel"))
                #layout.operator("hops.mirror_array", text="(R) Mirror / Array" if addon.preference().property.add_prefix else "Mirror / Array", icon_value=get_icon_id("Mirror"))
                layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        #layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        #layout.operator("hops.array_gizmo", text="Array", icon_value=get_icon_id("Array"))

    def draw_only_with_active_object_is_csharpen(self, layout, object):
        object = bpy.context.active_object
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.sharpen", text="Sharpen", icon_value=get_icon_id("SSharpen"))
        layout.operator("hops.adjust_bevel", text="Bevel", icon_value=get_icon_id("AdjustBevel"))
        #layout.operator("hops.mirror_array", text="Mirror / Array", icon_value=get_icon_id("Mirror"))
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))

        #layout.operator("hops.scroll_multi", text="Mod Scroll/Toggle", icon_value=get_icon_id("StatusReset"))
        layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))

    def draw_with_active_object_and_other_mesh(self, layout, active_object, other_object):
        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("hops.bool_difference", text="Difference", icon_value=get_icon_id("red"))
        object = bpy.context.active_object
        layout.operator("hops.adjust_bevel", text="Bevel", icon_value=get_icon_id("AdjustBevel"))
        #layout.operator("hops.mirror_array", text="Mirror / Array", icon_value=get_icon_id("Mirror"))
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        layout.separator()
        layout.menu("HOPS_MT_BoolSumbenu", text="(W) Booleans" if addon.preference().property.add_prefix else "Booleans", icon="MOD_BOOLEAN")
        layout.separator()
        layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))

    def draw_with_active_object_and_other_mesh_for_merge(self, layout, active_object, other_object):
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.parent_merge", text="(C) merge", icon_value=get_icon_id("Merge"))
        layout.operator("hops.simple_parent_merge", text="(S) merge", icon_value=get_icon_id("Merge"))
        layout.operator("hops.remove_merge", text="Remove Merge", icon_value=get_icon_id("Merge"))

    def draw_with_active_object_and_other_mesh_for_softmerge(self, layout, active_object, other_object):
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("hops.parent_merge_soft", text="(C) merge(soft)", icon_value=get_icon_id("CSharpen"))
        layout.operator("hops.slash", text="(C) Slash", icon_value=get_icon_id("Csplit"))
        layout.operator("hops.remove_merge", text="Remove Merge", icon_value=get_icon_id("CSharpen"))

    def draw_options(self, layout):
        layout.separator()
        layout.menu("HOPS_MT_ObjectsOperatorsSubmenu", text="Operations", icon="OBJECT_DATAMODE") #icon_value=get_icon_id("Diagonal"))
        layout.separator()
        if len(bpy.context.selected_objects) == 1:
            layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
            layout.separator()
        layout.menu("HOPS_MT_ObjectToolsSubmenu", text="MeshTools", icon_value=get_icon_id("WireMode"))
        layout.menu("HOPS_MT_SettingsSubmenu", text="Settings", icon_value=get_icon_id("Settings"))

        if False in [dim > 0 for dim in bpy.context.object.dimensions]:
            layout.separator()
            layout.operator_menu_enum("object.convert", "target")


    # Edit Mode
    ############################################################################

    def draw_edit_mode_menu(self, layout, object):
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("hops.edit_multi_tool", text="(s) Mark", icon_value=get_icon_id("MakeSharpE"))
        #layout.operator("hops.set_edit_sharpen", text="Set SSharp", icon_value=get_icon_id("MakeSharpE"))
        #layout.operator("hops.bevel_weight", text="Bweight", icon_value=get_icon_id("AdjustBevel"))
        #layout.menu("HOPS_MT_ModSubmenu", text = 'Add Modifier',  icon_value=get_icon_id("Tris"))
        #layout.operator("hops.array_gizmo", text="Array", icon_value=get_icon_id("Array"))
        layout.separator()
        #layout.operator("hops.clean1_objects", text="Demote", icon_value=get_icon_id("Demote")).clearsharps = False
        layout.menu("HOPS_MT_ModSubmenu", text = 'Add Modifier',  icon_value=get_icon_id("Tris"))
        layout.separator()
        layout.operator("hops.edge2curve", text="Curve/Extract", icon_value=get_icon_id("Curve"))
        layout.operator("view3d.vertcircle", text="Circle" if addon_exists("mesh_looptools") else "Circle (E)", icon_value=get_icon_id("NthCircle"))
        layout.operator("hops.bool_dice_v2", text="Dice V2", icon_value=get_icon_id("Dice"))
        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            layout.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))
        layout.separator()

        #if addon.preference().property.st3_meshtools:
        layout.operator("hops.edit_mesh_macro", text="EM_Macro", icon_value=get_icon_id("FaceGrate"))
        layout.menu("HOPS_MT_ST3MeshToolsSubmenu", text="(M) Mesh Tools" if addon.preference().property.add_prefix else ("Mesh Tools"), icon="MESH_ICOSPHERE")
        layout.separator()

        layout.menu("HOPS_MT_MeshOperatorsSubmenu", text="Operations", icon_value=get_icon_id("StatusOveride"))

        if object.mode == "OBJECT" or object.mode == "EDIT":
            if addon_exists("MESHmachine"):
                #layout.label(text = "MeshMachine")
                layout.separator()
                layout.menu("MACHIN3_MT_mesh_machine", text="MESHmachine", icon_value=get_icon_id("Machine"))
                layout.separator()

        layout.operator("hops.flatten_align", text="Flatten/Align/Select", icon_value=get_icon_id("Xslap"))
        layout.menu("HOPS_MT_BoolSumbenu", text="Booleans", icon_value=get_icon_id("Booleans"))
        if addon_exists('bezier_mesh_shaper') or addon_exists('MESHmachine') or addon_exists('mira_tools'):
            layout.menu("HOPS_MT_PluginSubmenu", text="Plugin", icon="PLUGIN")
        layout.separator()

        """if object.data.show_edge_crease == False:
            layout.operator("object.showoverlays", text="Show Overlays", icon = "RESTRICT_VIEW_ON")
        else :
            layout.operator("object.hide_overlays", text="Hide Overlays", icon = "RESTRICT_VIEW_OFF")"""

        if bpy.context.object and bpy.context.object.type == 'MESH':
            layout.menu("HOPS_MT_MaterialListMenu", text="Material", icon_value=get_icon_id("StatusOveride"))

        if addon_exists("DECALmachine"):
            layout.separator()
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.operator("hops.dm2_window", text = "Asset Loader (DM2)", icon_value=get_icon_id("QGui"))
            layout.separator()

    def draw_edit_mode_curve_menu(self, layout, object):
        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            layout.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))
        layout.operator("hops.to_rope", text="To Rope", icon="STROKE")
        #layout.operator("view3d.view_align", text= "Align View", icon_value=get_icon_id("HardOps"))
        #layout.separator()
        #layout.menu("HOPS_MT_InsertsObjectsSubmenu", text="Insert", icon_value=get_icon_id("Noicon"))

    # Sculpt Menu
    ############################################################################
    def draw_sculpt_menu(self, layout):
        wm = bpy.context.window_manager
        context = bpy.context
        layout.menu("HOPS_MT_SculptSubmenu", text="Sculpt")

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("hops.sculpt_primitives", text = "Add Primitive", icon_value=get_icon_id("QGui"))
        layout.operator("hops.sculpt_arms", text = "Arms", icon="BONE_DATA")
        #layout.template_icon_view(wm, "brush_previews", show_labels=True)
        layout.separator()
        if context.space_data.show_region_header == False:
            layout.operator("hops.show_topbar", text = "Toggle Toolbar")
        layout.operator("sculpt.toggle_brush", text="Toggle Brush")
        #layout.prop(bpy.context.object.data, "use_dynamic_topology_sculpting", text = "Enable Dyntopo")
        layout.separator()
        layout.label(text='Mesh Adjustments', icon='MESH_GRID')
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("sculpt.decimate_mesh", text="(W) Decimate" if addon.preference().property.add_prefix else "Decimate")
        #if context.sculpt_object.use_dynamic_topology_sculpting == False:
            #layout.prop(context.active_object.data, 'remesh_voxel_size', text='Voxel Size')
        layout.operator("view3d.voxelizer", text = "(E) Voxelize" if addon.preference().property.add_prefix else "Voxelize")
        #layout.operator_context = "EXEC_DEFAULT"
        layout.operator("object.quadriflow_remesh", text = "(R) Quadriflow" if addon.preference().property.add_prefix else "Quadriflow")

        layout.separator()
        layout.operator_context = "INVOKE_DEFAULT"
        layout.operator("view3d.sculpt_ops_window", text="(Q) Brush" if addon.preference().property.add_prefix else "Brush", icon="BRUSH_DATA")
        layout.separator()

    # Lamp Menu
    ############################################################################

    def draw_lamp_menu(self, layout):
        c = bpy.context.scene
        if 'EEVEE' in c.render.engine:
            layout.prop(bpy.context.object.data, "energy", text="Energy")
            layout.prop(bpy.context.object.data, "use_contact_shadow", text="Contact Shadow")
            if bpy.context.object.data.type == 'AREA':
                layout.prop(bpy.context.object.data, "shape", text = '')
            layout.separator()
            layout.prop(bpy.context.scene.eevee,"use_soft_shadows", text = "SCN_Soft Shadows")
            layout.prop(bpy.context.scene.eevee, "use_gtao", text = "SCN_Global AO")
        else:
            layout.label(text="No Lamp Options Yet")

    # Camera Menu
    ############################################################################

    def draw_camera_menu(self, context, layout):
        # cam = bpy.context.space_data
        #obj = bpy.context.object

        obj = bpy.context.object.data
        layout.prop(obj, "lens", text="Lens")
        layout.prop(obj, "passepartout_alpha", text="PP")
        #layout.prop(obj, "dof.focus_object", text="")

        if hasattr(obj, 'cycles_visibility'):
            obj = bpy.context.object.data.cycles
            layout.prop(obj, "aperture_size", text="DOF Size")

        layout.separator()

        layout.prop(context.object.data, "sensor_fit", text="")
        if context.object.data.sensor_fit == 'AUTO':
            layout.prop(context.object.data, "sensor_width")
        else:
            layout.prop(context.object.data, "sensor_width")
            layout.prop(context.object.data, "sensor_height")

        layout.separator()
        layout.operator("hops.set_camera", text="Set Active Cam", icon_value=get_icon_id("StarConnect"))

        layout.separator()
        layout.menu("HOPS_MT_SettingsSubmenu", text="Settings", icon_value=get_icon_id("Settings"))

    # Lattice Mode
    ############################################################################

    def draw_lattice_menu(self, layout):
        # layout.prop(bpy.context.object.data, "points_u", text="X")
        # layout.prop(bpy.context.object.data, "points_v", text="Y")
        # layout.prop(bpy.context.object.data, "points_w", text="Z")

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text=f'X - {bpy.context.object.data.points_u}', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.points_u'
        op.header_text = 'Points U: %.0f'
        op.input_scale = 0.05

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text=f'Y - {bpy.context.object.data.points_v}', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.points_v'
        op.header_text = 'Points V: %.0f'
        op.input_scale = 0.05

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text=f'Z - {bpy.context.object.data.points_w}', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.points_w'
        op.header_text = 'Points W: %.0f'
        op.input_scale = 0.05

        layout.prop(bpy.context.object.data, "use_outside")
        layout.operator("hops.simplify_lattice", text="Simplify", icon_value=get_icon_id("StarConnect"))
        layout.separator()
        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            layout.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))

    # BoolShape Menu
    ############################################################################

    def draw_boolshape_menu(self, layout):
        layout.operator_context = "INVOKE_DEFAULT"
        # layout.operator("hops.sharpen", text="Sharpen", icon_value=get_icon_id("SSharpen"))
        # layout.separator()
        layout.operator("hops.adjust_bevel", text="(E) Bevel" if addon.preference().property.add_prefix else "Bevel", icon_value=get_icon_id("AdjustBevel"))
        layout.operator("hops.adjust_tthick", text="(T) Solidify ", icon_value=get_icon_id("Tthick"))
        layout.operator("hops.st3_array", text="(W) Array V2" if addon.preference().property.add_prefix else "Array V2", icon_value=get_icon_id("GreyArrayX"))
        layout.separator()
        is_displace = len([mod for mod in bpy.context.active_object.modifiers if mod.type == 'DISPLACE'])
        is_boolean = len([mod for mod in bpy.context.active_object.modifiers if mod.type == 'BOOLEAN'])

        if len(bpy.context.selected_objects) == 1:
            if bpy.context.active_object.modifiers[:]:
                #layout.operator("hops.scroll_multi", text="Mod Scroll/Toggle", icon_value=get_icon_id("StatusReset"))
                layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))

            elif is_displace:
                layout.operator("hops.mod_displace", text="Displace", icon="MOD_DISPLACE")
            elif is_boolean:
                #layout.operator("hops.scroll_multi", text="Mod Scroll/Toggle", icon_value=get_icon_id("StatusReset"))
                layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))
            else:
                layout.separator()
                #layout.operator("hops.st3_array", text="(W) Array V2" if addon.preference().property.add_prefix else "Array V2", icon_value=get_icon_id("GreyArrayX"))
                #layout.operator("hops.clean1_objects", text="Demote", icon_value=get_icon_id("Demote")).clearsharps = False
            #layout.operator("hops.boolshape_status_swap", text="Red", icon_value=get_icon_id("Red")).red = True
            #layout.operator("hops.boolshape_status_swap", text="Green", icon_value=get_icon_id("Green")).red = False
            layout.operator("hops.bool_shift", text="Shift Bool", icon_value=get_icon_id("CleansharpsE"))
            layout.separator()
        if len(bpy.context.selected_objects) == 2:
            layout.menu("HOPS_MT_BoolSumbenu", text="Booleans", icon="MOD_BOOLEAN")
            layout.separator()
        layout.menu("HOPS_MT_ObjectsOperatorsSubmenu", text="Operations", icon_value=get_icon_id("StatusOveride"))
        layout.separator()
        layout.menu("HOPS_MT_ModSubmenu", text="Add Modifier", icon_value=get_icon_id("Diagonal"))
        layout.separator()
        layout.menu("HOPS_MT_ObjectToolsSubmenu", text="MeshTools", icon_value=get_icon_id("WireMode"))
        layout.menu("HOPS_MT_SettingsSubmenu", text="Settings", icon_value=get_icon_id("Settings"))

        if False in [dim > 0 for dim in bpy.context.object.dimensions]:
            layout.separator()
            layout.operator_menu_enum("object.convert", "target")


    def draw_curve_menu(self, layout):
        if len(bpy.context.selected_objects) == 1:
            layout.operator_context = "INVOKE_DEFAULT"
            layout.operator("hops.adjust_curve", text="Adjust Curve", icon_value=get_icon_id("Curve"))
            layout.operator("hops.to_rope", text="To Rope", icon="STROKE")
            #if False in [dim > 0 for dim in bpy.context.object.dimensions]:
                #layout.operator("hops.adjust_bevel", text="(B) Bevel ", icon_value=get_icon_id("AdjustBevel"))
            layout.separator()
            layout.prop(bpy.context.object.data, 'resolution_u')
            layout.operator_context = "INVOKE_DEFAULT"
            op = layout.operator('wm.context_modal_mouse', text=f'Resolution U {bpy.context.object.data.resolution_u}', icon_value=get_icon_id('gettin id'))
            op.data_path_iter = 'selected_editable_objects'
            op.data_path_item = 'data.resolution_u'
            op.header_text = 'Resolution U: %.0f'
            op.input_scale = 0.01

            layout.separator()
            layout.operator_menu_enum("object.convert", "target")
        else:
            layout.operator("hops.curve_bevel", text="Curve Bevel", icon_value=get_icon_id("Curve"))
            layout.operator_context = "INVOKE_DEFAULT"
            layout.operator("hops.adjust_curve", text="Adjust Curve", icon_value=get_icon_id("Curve"))
            layout.separator()
            layout.operator("hops.add_mod_curve", text="Curve Modifier", icon='MOD_CURVE')

        layout.operator("hops.to_gpstroke", text="To_Stroke", icon="GREASEPENCIL")

        if addon.preference().property.radial_array_type != 'CLASSIC':
            layout.separator()
            layout.operator("hops.radial_array_nodes", text="Radial Array V2", icon_value=get_icon_id("ArrayCircle"))
        layout.separator()

        if addon.preference().property.accushape_type == 'V2':
            layout.operator("hops.accu_shape_v2", text="AccuShape V2", icon_value=get_icon_id("grey"))
        else:
            layout.operator("hops.accu_shape", text="AccuShape", icon_value=get_icon_id("grey"))

        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))
        else:
            layout.operator("hops.to_shape_v2", text="To_Shape V2", icon_value=get_icon_id("Frame"))

    def draw_rigging_menu(self, layout):
        layout.operator("object.create_driver_constraint", text="Driver Constraint")

    # DECAL MENU
    ############################################################################

    def draw_decalA_menu(self, layout):
        # if "decal" not in activemat.name and "paneling" not in activemat.name and "info" not in activemat.name:
        if "decal" or "info" or "panel" in bpy.context.active_object.name:
            if addon_exists("DECALmachine"):
                layout.operator_context = "INVOKE_DEFAULT"
                layout.operator("machin3.modal_decal_height", text="Adjust Decal Height")
                layout.operator("machin3.decal_source", text="Extract Source")
                # layout.separator()

    # Empty Menu
    ############################################################################

    def draw_only_with_active_object_is_empty(self, layout):

        obj = bpy.context.object
        wm = bpy.context.window_manager

        # if obj.empty_display_type == 'IMAGE':
        #     layout.template_icon_view(wm, "img_selection_previews")

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text='Empty Scale', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'empty_display_size'
        op.header_text = 'Empty Scale: %.3f'
        op.input_scale = 0.01

        #layout.menu("SCREEN_MT_user_menu", text="Quick Favorites", icon_value=get_icon_id("QuickFav"))

        # button = layout.operator("hops.set_empty_image", text="Set Image")
        # button.img = wm.img_selection_previews

        if obj.empty_display_type == 'IMAGE':
            layout.separator()
            layout.operator("hops.center_empty", text="Center Image")
            layout.operator_context = "INVOKE_DEFAULT"
            layout.operator("hops.empty_transparency_modal", text="Change Transparency")
            layout.operator("hops.empty_position_modal", text="Change Offset")
        layout.separator()
        layout.operator("hops.set_origin", text="Set Origin", icon_value=get_icon_id("CircleSetup"))
        if addon.preference().property.radial_array_type == 'CLASSIC':
            layout.operator("hops.radial_array", text="Radial Array", icon_value=get_icon_id("ArrayCircle")).from_empty = True
        else:
            layout.operator("hops.radial_array_nodes", text="Radial Array V2", icon_value=get_icon_id("ArrayCircle")).from_empty = True
        layout.separator()
        layout.operator("view3d.view_align", text="Align View", icon_value=get_icon_id("Xslap"))
        layout.operator("hops.blank_light", text="Add Lights", icon='LIGHT')


    # Thin Object Test
    ############################################################################

    def draw_thin_object(self, layout):

        obj = bpy.context.object

        layout.operator_context = "INVOKE_DEFAULT"
        #layout.operator('hops.2d_bevel', text = '2d Bevel', icon_value=get_icon_id("AdjustBevel"))
        layout.operator("hops.adjust_bevel", text="Bevel ", icon_value=get_icon_id("AdjustBevel"))
        layout.operator("hops.adjust_tthick", text="Solidify ", icon_value=get_icon_id("Tthick"))
        layout.operator("hops.st3_array", text="(W) Array V2" if addon.preference().property.add_prefix else "Array V2", icon_value=get_icon_id("GreyArrayX"))
        if bpy.context.active_object.modifiers[:]:
            layout.separator()
            layout.operator("hops.ever_scroll_v2", text="Ever Scroll", icon_value=get_icon_id("StatusReset"))

    # Grease Pencil Tiem
    ############################################################################

    def draw_pencil_menu(self, layout):

        obj = bpy.context.object
        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator("hops.copy_move", text="Copy / Move", icon_value=get_icon_id("Display_dots"))
        layout.operator("hops.surfaceoffset", text="Surface OffSet", icon_value=get_icon_id("dots"))
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        layout.operator("hops.mod_lattice", text="Lattice", icon="MOD_LATTICE")
        if bpy.context.space_data.show_region_tool_header == False:
            layout.operator("hops.show_topbar", text = "Show Toolbar")

    def draw_gpencil_menu(self, layout):

        obj = bpy.context.object
        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator("hops.st3_array", text="(W) Array V2" if addon.preference().property.add_prefix else "Array V2", icon_value=get_icon_id("GreyArrayX"))
        layout.operator("hops.mirror_gizmo", text="Mirror", icon_value=get_icon_id("Mirror"))
        layout.operator("hops.mod_lattice", text="Lattice", icon="MOD_LATTICE")
        if bpy.context.space_data.show_region_tool_header == False:
            layout.operator("hops.show_topbar", text = "Show Toolbar")


    # Font Tiem
    ############################################################################

    def draw_font_menu(self, layout):

        obj = bpy.context.object

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text='Extrude', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.extrude'
        op.header_text = 'Extrude Size: %.3f'
        op.input_scale = 0.001

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text='Offset', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.offset'
        op.header_text = 'Width Size: %.3f'
        op.input_scale = 0.001

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text='Bevel', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.bevel_depth'
        op.header_text = 'Bevel Depth: %.3f'
        op.input_scale = 0.0001

        layout.operator_context = "INVOKE_DEFAULT"
        op = layout.operator('wm.context_modal_mouse', text='Spacing', icon_value=get_icon_id('gettin id'))
        op.data_path_iter = 'selected_editable_objects'
        op.data_path_item = 'data.space_character'
        op.header_text = 'Character Spacing: %.3f'
        op.input_scale = 0.001

        layout.separator()

        if addon.preference().property.accushape_type == 'V2':
            layout.operator("hops.accu_shape_v2", text="AccuShape V2", icon_value=get_icon_id("grey"))
        else:
            layout.operator("hops.accu_shape", text="AccuShape", icon_value=get_icon_id("grey"))

        layout.operator("hops.font_scroll", text="Font Scroll", icon='FILE_FONT')

        if addon.preference().property.to_shape_type == 'CLASSIC':
            layout.operator("hops.to_shape", text="To_Shape", icon_value=get_icon_id("Display_boolshapes"))
        elif addon.preference().property.to_shape_type == 'CLASSIC+':
            layout.operator("hops.to_shape_1_5", text="To_Shape v1.5", icon_value=get_icon_id("Display_boolshapes"))

def asset_loader_unlock():
    wm = bpy.context.window_manager
    active_object = bpy.context.active_object
    if addon_exists("DECALmachine") or hasattr(wm, 'kitops') or hasattr(wm, 'powerlink'):
        if active_object is None or len(bpy.context.selected_objects) == 0:
            return True
        elif len(bpy.context.selected_objects):
            if active_object.mode not in {'EDIT', 'SCULPT', 'POSE', 'WEIGHT_PAINT', 'TEXTURE_PAINT'}:
                return True
    else:
        return False
        # if len(bpy.context.selected_objects):
        #     if active_object.mode == "OBJECT":
        #         return True
    #         else:
    #             return False
    #     else:
    #         return False
    # else:
    #     return False