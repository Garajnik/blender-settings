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

# Copyright 2023, Valeriy Yatsenko

import bpy
from dataclasses import dataclass

from ZenUV.ui.labels import ZuvLabels
from bpy.props import BoolProperty
from ZenUV.utils.generic import fit_uv_view
from ZenUV.prop.zuv_preferences import get_prefs
from ZenUV.ui.pie import ZsPieFactory
from ZenUV.ops.trimsheets.trimsheet_utils import ZuvTrimsheetUtils

from ZenUV.utils.blender_zen_utils import ZenPolls

from ZenUV.utils.vlog import Log

from .pack_utils import ObjsStorage, PackUtils, SoBject


@dataclass
class UnifiedPackerProps:

    result: bool = False
    message: str = ''
    raise_popup_id_name: str = None


class GenericPackerManager(UnifiedPackerProps):

    def __init__(self, context, addon_prefs) -> None:
        self.context: bpy.types.Context = context
        self.addon_prefs: bpy.types.AddonPreferences = addon_prefs
        self.packer_parsed_props = {"generic": "generic"}
        self.packer_name: str = None
        self.stored_props = None
        self.packer_props_pointer = None
        self.show_transfer: bool = False
        self.raise_popup_id_name: str = None

    def pack(self):
        return False

    def get_engine_version(self):
        return False

    # PROTECTED
    # this method must be overrided in all derived classes !!!
    def _is_engine_present(self):
        return False

    def _store_packer_props(self):
        self.stored_props = dict()
        for attr in self.packer_parsed_props.keys():
            try:
                self.stored_props.update({attr: getattr(self.packer_props_pointer, attr)})
            except Exception:
                self.stored_props = None

    def _restore_packer_props(self):
        for attr in self.packer_parsed_props.keys():
            try:
                setattr(self.packer_props_pointer, attr, self.stored_props[attr])
            except Exception:
                return False
        if self.show_transfer:
            print(f"\nRestored Packer Props: {self.stored_props}\n")
        return True

    def _is_attribute_real(self, attrib):
        if isinstance(attrib, str):
            if getattr(self.addon_prefs, attrib, "NOT_PASSED") == "NOT_PASSED":
                return False
            return True
        return False

    def _trans_props_zen_to_packer(self):
        for packer_attr, zuv_attr in self.packer_parsed_props.items():
            try:
                if self._is_attribute_real(zuv_attr):
                    if self.show_transfer:
                        print(f"attr type: {type(zuv_attr)}.\t{self.packer_name}: {packer_attr} -> {getattr(self.packer_props_pointer, packer_attr)}, Zen UV: {zuv_attr} -> {getattr(self.addon_prefs, zuv_attr, False)}")
                    setattr(self.packer_props_pointer, packer_attr, getattr(self.addon_prefs, zuv_attr))

                else:
                    if self.show_transfer:
                        print(f"attr type: {type(zuv_attr)}.\t{self.packer_name}: {packer_attr} -> {getattr(self.packer_props_pointer, packer_attr)}, Zen UV: {zuv_attr} -> {self.packer_parsed_props[packer_attr]}")
                    setattr(self.packer_props_pointer, packer_attr, zuv_attr)

            except Exception:
                if self.show_transfer:
                    print(f"\nError in: {packer_attr}. Value: {getattr(self.packer_props_pointer, packer_attr)}")
                    print(f"\t\t{self.packer_name}: {packer_attr}, Zen UV: {zuv_attr}: {getattr(self.addon_prefs, zuv_attr, 'UNDEFINED')}, Type: {type(zuv_attr)}\n")


class UVPackerManager(GenericPackerManager):

    def __init__(self, context, addon_prefs) -> None:
        GenericPackerManager.__init__(self, context, addon_prefs)
        self.packer_parsed_props = {
            "uvp_width": "TD_TextureSizeX",
            "uvp_height": "TD_TextureSizeY",
            "uvp_rescale": "averageBeforePack",
            "uvp_prerotate": "rotateOnPack",
            "uvp_rotate": None,
            "uvp_padding": None,
            "uvp_selection_only": "packSelectedIslOnly",
        }
        self.packer_name = "UV-Packer"
        self.show_transfer = False

    def pack(self, context: bpy.types.Context, Storage: ObjsStorage, addon_prefs: bpy.types.AddonPreferences):
        print("Zen UV - Pack: UV-Packer Engine activated.")
        self.result, self.message = self._do_pack(context, Storage, addon_prefs)

    def _is_engine_present(self):
        if hasattr(bpy.types, bpy.ops.uvpackeroperator.packbtn.idname()):
            if hasattr(self.context.scene, "UVPackerProps") and hasattr(self.context.scene.UVPackerProps, "uvp_padding"):
                if self.show_transfer:
                    print("Engine present. Props Pointer created.")
                self.packer_props_pointer = self.context.scene.UVPackerProps
                return True
        return False

    def _do_pack(self, context: bpy.types.Context, Storage: ObjsStorage, addon_prefs: bpy.types.AddonPreferences):

        if not self._is_engine_present():
            self.raise_popup_id_name = 'ZUV_MT_ZenPack_Uvpacker_Popup'
            return False, f"Nothing is produced. Seems like {self.packer_name} is not installed on your system."

        self._store_packer_props()

        # Setting additional Packer Properties
        self.packer_parsed_props["uvp_rotate"] = self.context.scene.UVPackerProps.uvp_rotate
        if not addon_prefs.rotateOnPack:
            self.packer_parsed_props["uvp_rotate"] = "0"
        self.packer_parsed_props["uvp_padding"] = self.context.scene.zen_uv.pack_uv_packer_margin

        self._trans_props_zen_to_packer()

        if addon_prefs.packSelectedIslOnly is False and Storage.is_hidden_faces_in_objects():
            PackUtils.resolve_pack_selected_only(context, addon_prefs, Storage, set_sel_only=True)
            context.scene.UVPackerProps.uvp_selection_only = True
        elif addon_prefs.packSelectedIslOnly is True and Storage.is_hidden_faces_in_objects():
            PackUtils.resolve_pack_selected_only(context, addon_prefs, Storage)
            context.scene.UVPackerProps.uvp_selection_only = True
        else:
            PackUtils.resolve_pack_selected_only(context, addon_prefs, Storage)

        res = True
        out_msg = []

        try:
            if not bpy.ops.uvpackeroperator.packbtn.poll():
                raise RuntimeError(f"For some reason, {self.packer_name} cannot be launched. Check out its performance separately from Zen UV.")

            bpy.ops.uvpackeroperator.packbtn('INVOKE_DEFAULT')
            out_msg.append("Finished")
        except Exception as e:
            res = False
            out_msg.append(str(e))

        restored = self._restore_packer_props()

        if not restored:
            res = False
            out_msg.append(f"The properties of the {self.packer_name} are not restored.")

        return res, '.'.join(out_msg)


class UVPMmanager(GenericPackerManager):

    def __init__(self, context, addon_prefs) -> None:
        GenericPackerManager.__init__(self, context, addon_prefs)
        self.uvp_2_parsed_props = {
            "margin": "margin",
            "rot_enable": "rotateOnPack",
            "lock_overlapping_mode": "lock_overlapping_mode",
            "fixed_scale": "packFixedScale",
            "heuristic_enable": False,
            "normalize_islands": "averageBeforePack",
            "pack_to_others": False,
            "use_blender_tile_grid": False
        }

        self.uvp_3_parsed_props = {
            "margin": "margin",
            "rotation_enable": "rotateOnPack",
            "lock_overlapping_enable": "lock_overlapping_enable",
            "lock_overlapping_mode": "lock_overlapping_mode",
            "fixed_scale": "packFixedScale",
            "heuristic_enable": False,
            "normalize_islands": "averageBeforePack",
            # "pack_to_others": False,
            "use_blender_tile_grid": False
        }
        self.uvpm_version = None
        self.packer_name = "UV Packmaster"
        self.show_transfer = False
        self.disable_overlay = False
        self.stored_t_b = None

    def pack(self, context, Storage: ObjsStorage, addon_prefs, disable_overlay):
        print("Zen UV - Pack: UV Packmaster Engine activated.")

        PackUtils.resolve_pack_selected_only(context, addon_prefs, Storage)

        self.is_pack_in_trim(context, addon_prefs)

        # Disable UVP Overlay case HOps display is on.
        if addon_prefs.hops_uv_activate is True:
            self.disable_overlay = True
            self.report({'INFO'}, 'UVP Overlay is temporarily disabled. See the details in the console.')
            print('Zen UV message: UVP Overlay is temporarily disabled. Reason - HOps UV Display is On . Only one overlay info can be activated.')
        else:
            self.disable_overlay = disable_overlay

        self.result, self.message = self._do_pack()
        self.raise_popup_id_name = self.raise_popup_id_name

        # bpy.ops.mesh.select_all(action='DESELECT')
        PackUtils.bpy_select_by_context(context, action='DESELECT')
        self.restore_uvpm3_target_box(context)

    def get_engine_version(self):
        if hasattr(self.context.scene, "uvp2_props"):
            self.packer_parsed_props = self.uvp_2_parsed_props
            self.packer_props_pointer = self.context.scene.uvp2_props
            self.uvpm_version = 2
            return self.uvpm_version

        elif hasattr(self.context.scene, "uvpm3_props"):
            self.packer_parsed_props = self.uvp_3_parsed_props
            self.packer_props_pointer = self.context.scene.uvpm3_props
            self.uvpm_version = 3
            return self.uvpm_version

        else:
            return None

    def is_pack_in_trim(self, context: bpy.types.Context, addon_prefs) -> bool:
        if not addon_prefs.packInTrim:
            Log.debug('Pack in Trim not Activated')
            return
        if self.get_engine_version() != 3:
            Log.debug(self.uvpm_version)
            Log.debug('uvpm_ver_not_3')
            self.raise_message('uvpm_ver_not_3')
            return False
        trim = ZuvTrimsheetUtils.getActiveTrim(context)
        if trim is None:
            self.raise_message('active_trim_is_none')
            return False

        uvpm3_props = context.scene.uvpm3_props
        t_b_props = uvpm3_props.custom_target_box

        self.stored_t_b = [
            t_b_props.p1_x,
            t_b_props.p1_y,
            t_b_props.p2_x,
            t_b_props.p2_y,
            uvpm3_props.custom_target_box_enable
        ]
        rect = trim.rect

        uvpm3_props.custom_target_box_enable = True
        t_b_props.p1_x = rect[0]
        t_b_props.p1_y = rect[3]
        t_b_props.p2_x = rect[2]
        t_b_props.p2_y = rect[1]

        return True

    def restore_uvpm3_target_box(self, context: bpy.types.Context) -> bool:
        if self.stored_t_b is None:
            return False
        uvpm3_props = context.scene.uvpm3_props
        t_b_props = uvpm3_props.custom_target_box
        uvpm3_props.custom_target_box_enable = self.stored_t_b[4]

        t_b_props.p1_x = self.stored_t_b[0]
        t_b_props.p1_y = self.stored_t_b[1]
        t_b_props.p2_x = self.stored_t_b[2]
        t_b_props.p2_y = self.stored_t_b[3]

        return True

    def transfer_attrs_to_uvpm(self):
        self._trans_props_zen_to_packer()

    def _do_pack(self):

        ZsPieFactory.mark_pie_cancelled()

        if not self.get_engine_version():
            self.raise_popup_id_name = 'ZUV_MT_ZenPack_Uvp_Popup'
            return False, self.raise_message("engine_not_present")

        print(f"Zen UV: UVPMmanager: Pack Engine UV Packmaster {self.uvpm_version} detected.")

        if not self.packer_props_pointer:
            return False, self.raise_message("props_error")

        self._store_packer_props()

        if not self.stored_props:
            return False, self.raise_message("props_not_found")

        self._trans_props_zen_to_packer()

        if self.uvpm_version == 2 and bpy.ops.uvpackmaster2.uv_pack.poll():
            if self.disable_overlay:
                bpy.ops.uvpackmaster2.uv_pack()
            else:
                bpy.ops.uvpackmaster2.uv_pack("INVOKE_DEFAULT")

        elif self.uvpm_version == 3 and bpy.ops.uvpackmaster3.pack.poll():
            if self.disable_overlay:
                bpy.ops.uvpackmaster3.pack(mode_id=self.context.scene.zen_uv.uvp3_packing_method, pack_to_others=False)
            else:
                bpy.ops.uvpackmaster3.pack("INVOKE_DEFAULT", mode_id=self.context.scene.zen_uv.uvp3_packing_method, pack_to_others=False)

        else:
            self._restore_packer_props()
            return False, self.raise_message("poll_failed")

        restored = self._restore_packer_props()
        if not restored:
            return False, self.raise_message("restore_props_error")

        return True, self.raise_message("finished")

    def raise_message(self, err_type):
        messages = {
            "detected_engine": f"Zen UV: UVPMmanager: Pack Engine UV Packmaster {self.uvpm_version} detected.",
            "props_error": "Some Properties of UV Packmaster cannot be found. Update UV Packmaster to the latest version.",
            "restore_props_error": "Property restoring error.",
            "engine_not_present": "Nothing is produced. Seems like UV Packmaster is not installed on your system.",
            "props_not_found": "Not found properties of UVPackmaster",
            "finished": "Finished.",
            "err_finished": "Finished with Errors.",
            "poll_failed": "For some reason, UVPackmaster cannot be launched. Check out its performance separately from Zen UV.",
            "uvpm_ver_not_3": "Supported only in UV Packmaster v3",
            "active_trim_is_none": "There are no Active Trim."
        }
        if err_type in messages.keys():
            out_message = f"Zen UV: {messages[err_type]}"
            if self.show_transfer:
                print(out_message)
        else:
            out_message = "Zen UV: UVPMmanager: Message is not classified."
            if self.show_transfer:
                print(out_message)

        return out_message


class BlenderPackManager(UnifiedPackerProps):

    def __init__(self) -> None:
        self.show_transfer = False

    def is_pack_allowed(cls):
        if ZenPolls.version_equal_3_6_0:
            return False
        return True

    def pack(self, context: bpy.types.Context, Storage: ObjsStorage, addon_prefs: bpy.types.AddonPreferences, fast_mode: bool):
        print("Zen UV - Pack: Blender Engine activated.")
        if not self.is_pack_allowed():
            self.result = False
            self.message = 'Blender Pack Engine: In Blender v3.6.0 pack is not allowed becouse Packer is modal. Use Blender v3.6.1 istead'
            self.raise_popup_id_name = 'ZUV_MT_ZenWarningV36Popup'
            return

        PackUtils.resolve_pack_selected_only(context, addon_prefs, Storage)

        if addon_prefs.packInTrim:
            bpy.ops.uv.zenuv_fit_to_trim(
                influence_mode='ISLAND',
                op_order='OVERALL',
                fit_mode='TO_TRIM_T',
                op_fit_axis='AUTO',
                op_keep_proportion=True,
                op_align_to='cen')
            self.create_fake_geometry(context, Storage)

        self.result, self.message = self._do_pack(addon_prefs, fast_mode)
        Storage.remove_marker_faces()
        PackUtils.bpy_select_by_context(context, action='DESELECT')

    def _do_pack(self, addon_prefs: bpy.types.AddonPreferences, fast_mode: bool):
        if addon_prefs.averageBeforePack:
            bpy.ops.uv.average_islands_scale()

        if ZenPolls.version_greater_3_6_0:
            try:
                self._bpy_pack(addon_prefs, fast_mode)
            except Exception:
                _message = "Zen UV: Potential Crash in Blender Pack process. \
                    Try to clean up geometry."
                return False, _message
        else:
            try:
                bpy.ops.uv.pack_islands(
                    'INVOKE_DEFAULT',
                    rotate=addon_prefs.rotateOnPack,
                    margin=addon_prefs.margin * 2.95
                    )
            except Exception:
                _message = "Zen UV: Potential Crash in Blender Pack process. \
                    Try to clean up geometry."
                return False, _message

        return True, "Zen UV: Pack Finished"

    def _bpy_pack(self, addon_prefs, fast_mode: bool):
        if fast_mode:
            bpy.ops.uv.pack_islands(
                udim_source='ORIGINAL_AABB' if addon_prefs.packInTrim else 'CLOSEST_UDIM',
                rotate=True,
                rotate_method='AXIS_ALIGNED',
                scale=True,
                merge_overlap=addon_prefs.lock_overlapping_enable,
                margin_method='ADD',
                margin=addon_prefs.margin,
                pin=False,
                pin_method='LOCKED',
                shape_method='AABB'
                )
        else:
            bpy.ops.uv.pack_islands(
                udim_source='ORIGINAL_AABB' if addon_prefs.packInTrim else 'CLOSEST_UDIM',
                rotate=addon_prefs.rotateOnPack,
                rotate_method='AXIS_ALIGNED',
                scale=True,
                merge_overlap=addon_prefs.lock_overlapping_enable,
                margin_method='ADD',
                margin=addon_prefs.margin,  # * 2.95,
                pin=False,
                pin_method='LOCKED',
                shape_method='CONCAVE'
                )

    def create_fake_geometry(self, context: bpy.types.Context, Storage: ObjsStorage):
        trim = ZuvTrimsheetUtils.getActiveTrim(context)
        if trim is None:
            self.raise_message('active_trim_is_none')
            return False
        self.create_markers(Storage, [trim.left_bottom, trim.top_right])
        return True

    def create_markers(self, Storage: ObjsStorage, trim_corners):
        s_obj: SoBject = Storage.objs[0]
        bm = s_obj.bm
        uv_layer = s_obj.uv_layer
        p_face = bm.faces[0]
        verts_co = (
            (-1.0000, -1.0000, 0.0000),
            (1.0000, -1.0000, 0.0000),
            (1.0000, 1.0000, 0.0000),
            (-1.0000, 1.0000, 0.0000))

        faces = ((0, 1, 2), (0, 2, 3))
        p_verts = []
        p_b_idx = len(bm.verts)

        for c, co in enumerate(verts_co):
            vert = bm.verts.new(co, p_face.verts[0])
            vert.index = p_b_idx + c
            p_verts.append(vert)

        for f_idxs, uv_co in zip(faces, trim_corners):
            verts = [p_verts[i] for i in f_idxs]
            p_f_idx = len(bm.faces) - 1
            face = bm.faces.new(verts, p_face)
            face.index = p_f_idx + 1
            face.select_set(True)
            Storage.marker_face_idxs.append(face.index)
            for lp in face.loops:
                lp[uv_layer].uv = uv_co

    def raise_message(self, err_type):
        messages = {
            "active_trim_is_none": "There are no Active Trim.",
        }
        if err_type in messages.keys():
            out_message = f"Zen UV: {messages[err_type]}"
            if self.show_transfer:
                print(out_message)
        else:
            out_message = "Zen UV: UVPMmanager: Message is not classified."
            if self.show_transfer:
                print(out_message)

        return out_message


class PackerProcessor:

    def __init__(self, PROPS) -> None:

        self.result: bool = False
        self.message: str = ''
        self.raise_popup_id_name: str = None

        self.disable_overlay = PROPS.disable_overlay

        self.fast_mode: bool = PROPS.fast_mode

    def pack(self, context: bpy.types.Context, Storage: ObjsStorage):
        addon_prefs = get_prefs()
        current_engine = addon_prefs.packEngine

        if current_engine == "UVP":

            Packer = UVPMmanager(context, addon_prefs)
            Packer.pack(context, Storage, addon_prefs, self.disable_overlay)

        elif current_engine == "BLDR":

            Packer = BlenderPackManager()
            Packer.pack(context, Storage, addon_prefs, self.fast_mode)

        elif current_engine == "UVPACKER":

            Packer = UVPackerManager(context, addon_prefs)
            Packer.pack(context, Storage, addon_prefs)

        else:
            self.result = False
            self.message = "Zen UV: There is no selected Engine for packing."
            return

        self.result = Packer.result
        self.message = Packer.message
        self.raise_popup_id_name = Packer.raise_popup_id_name


class ZUV_OT_Pack(bpy.types.Operator):
    bl_idname = "uv.zenuv_pack"
    bl_label = ZuvLabels.PACK_LABEL
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = ZuvLabels.PACK_DESC

    def __init__(self) -> None:
        self.Storage: ObjsStorage = ObjsStorage()
        self.invoked: bool = False

    display_uv: BoolProperty(
        name="Display UV",
        default=False,
        options={'HIDDEN'}
    )
    disable_overlay: BoolProperty(
        name="Disable Overlay",
        default=False,
        options={'HIDDEN'}
    )
    fast_mode: BoolProperty(
        name="Fast (simpliest) pack settings",
        default=False,
        options={'HIDDEN'}
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        p_res = self.Storage.collect_objects(context)
        self.invoked = True
        if p_res is False:
            self.report({'WARNING'}, "Zen UV: Select something.")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        if not self.invoked:
            p_res = self.Storage.collect_objects(context)
            if p_res is False:
                self.report({'WARNING'}, "Zen UV: Select something.")
                return {'CANCELLED'}

        ZsPieFactory.mark_pie_cancelled()

        self.Storage.hide_pack_excluded(context)

        PackProcessor = PackerProcessor(self.properties)
        PackProcessor.pack(context, self.Storage)

        if PackProcessor.result is False:
            self.Storage.unhide_pack_excluded()
            self.report({'WARNING'}, PackProcessor.message)
            if PackProcessor.raise_popup_id_name is not None:
                bpy.ops.wm.call_menu(name=PackProcessor.raise_popup_id_name)
            return {'CANCELLED'}

        print(PackProcessor.message)

        self.Storage.unhide_pack_excluded()
        self.Storage.restore_selection_all_objects(context)

        fit_uv_view(context, mode="all")

        if self.display_uv:
            # Display UV Widget from HOPS addon
            from ZenUV.utils.hops_integration import show_uv_in_3dview
            show_uv_in_3dview(context, use_selected_meshes=True, use_selected_faces=False, use_tagged_faces=False)

        return {'FINISHED'}


class ZUV_OT_SyncZenUvToUVP(bpy.types.Operator):
    bl_idname = "uv.zenuv_sync_to_uvp"
    bl_label = ZuvLabels.OT_SYNC_TO_UVP_LABEL
    bl_description = ZuvLabels.OT_SYNC_TO_UVP_DESC
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        addon_prefs = get_prefs()
        current_engine = addon_prefs.packEngine

        if current_engine == "UVP":
            print("Zen UV: UV Packmaster Engine detected")
            packer = UVPMmanager(context, addon_prefs)
            if not packer.get_engine_version():
                return {'CANCELLED'}
            packer.transfer_attrs_to_uvpm()
        else:
            bpy.ops.wm.call_menu(name="ZUV_MT_ZenPack_Uvp_Popup")
            return {'CANCELLED'}
        return {'FINISHED'}


pack_classes = (
    ZUV_OT_Pack,
    ZUV_OT_SyncZenUvToUVP,
)


if __name__ == '__main__':
    pass
