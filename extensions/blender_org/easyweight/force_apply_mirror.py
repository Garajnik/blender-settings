import bpy
from bpy.props import BoolProperty
from bpy.utils import flip_name

# TODO: 
# Should find a way to select the X axis verts before doing Remove Doubles, or don't Remove Doubles at all. Also need to select the Basis shape before doing Remove Doubles.
# Implement our own Remove Doubles algo with kdtree, which would average the vertex weights of the merged verts rather than just picking the weights of one of them at random.


def flip_driver_targets(obj):
    # We just need to flip the bone targets on every driver.
    shape_keys = obj.data.shape_keys
    if not shape_keys:
        return
    if not hasattr(shape_keys.animation_data, "drivers"):
        return
    drivers = shape_keys.animation_data.drivers

    for sk in shape_keys.key_blocks:
        # Capital D signifies that this is a driver container (known as a driver) rather than a driver(also known as driver) - Yes, the naming convention for drivers in python API is BAD. D=driver, d=driver.driver.
        for D in drivers:
            if sk.name in D.data_path:
                sk.vertex_group = flip_name(sk.vertex_group)
                for var in D.driver.variables:
                    for t in var.targets:
                        if not t.bone_target:
                            continue
                        t.bone_target = flip_name(t.bone_target)


class EASYWEIGHT_OT_force_apply_mirror(bpy.types.Operator):
    """Force apply mirror modifier by duplicating the object, flipping it on the X axis, merging into the original, and welding it at the middle"""

    bl_idname = "object.force_apply_mirror_modifier"
    bl_label = "Force Apply Mirror Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    remove_doubles: BoolProperty(name="Remove Doubles", default=False)
    weighted_normals: BoolProperty(name="Weighted Normals", default=True)
    split_shape_keys: BoolProperty(
        name="Split Shape Keys",
        default=True,
        description="If shape keys end in either .L or .R, duplicate them and flip their mask vertex group name",
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH' and obj.data and obj.data.shape_keys:
            cls.poll_message_set("There must be an active mesh object with shape keys.")
            return False
        for mod in obj.modifiers:
            if mod.type == 'MIRROR':
                if mod.use_axis[:] != (True, False, False):
                    cls.poll_message_set("Only X axis mirror modifier is supported.")
                    return False

                return True
        else:
            cls.poll_message_set("This mesh has no Mirror modifier.")

        return False

    def execute(self, context):
        # Remove Mirror Modifier
        # Copy mesh
        # Scale it -1 on X
        # Flip vgroup names
        # Join into original mesh
        # Remove doubles
        # Recalc Normals
        # Weight Normals

        obj = context.active_object

        # Find Mirror modifier.
        mirror = None
        for mod in obj.modifiers:
            if mod.type == 'MIRROR':
                mirror = mod
                break
        if not mirror:
            return {'CANCELLED'}

        if mirror.use_axis[:] != (True, False, False):
            self.report({'ERROR'}, "Only X axis mirroring is supported for now.")
            return {'CANCELLED'}

        # Remove mirror modifier.
        obj.modifiers.remove(mirror)

        # Set mode and selection.
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Remove Doubles - This should print out removed 0, otherwise we're gonna remove some important verts.
        if self.remove_doubles:
            print(
                "Checking for doubles pre-mirror. If it doesn't say Removed 0 vertices, you should undo."
            )
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.remove_doubles(use_unselected=True)
            bpy.ops.object.mode_set(mode='OBJECT')

        # Reset scale
        org_scale = obj.scale[:]
        obj.scale = (1, 1, 1)

        # Duplicate and scale object.
        bpy.ops.object.duplicate()
        flipped_o = context.active_object
        flipped_o.scale = (-1, 1, 1)

        # Flip vertex group names.
        done = []  # Don't flip names twice...
        for vg in flipped_o.vertex_groups:
            if vg in done:
                continue
            old_name = vg.name
            flipped_name = flip_name(vg.name)
            if old_name == flipped_name:
                continue

            opp_vg = flipped_o.vertex_groups.get(flipped_name)
            if opp_vg:
                vg.name = "temp"
                opp_vg.name = old_name
                vg.name = flipped_name
                done.append(opp_vg)

            vg.name = flipped_name
            done.append(vg)

        # Split/Flip shape keys.
        if self.split_shape_keys:
            done = []  # Don't flip names twice...
            shape_keys = flipped_o.data.shape_keys
            if shape_keys:
                keys = shape_keys.key_blocks
                for sk in keys:
                    if sk in done:
                        continue
                    old_name = sk.name
                    flipped_name = flip_name(sk.name)
                    if old_name == flipped_name:
                        continue

                    opp_sk = keys.get(flipped_name)
                    if opp_sk:
                        sk.name = "temp"
                        opp_sk.name = old_name
                        done.append(opp_sk)

                    sk.name = flipped_name
                    done.append(sk)

        flip_driver_targets(flipped_o)

        # Joining objects does not seem to preserve drivers on any except the active object, at least for shape keys.
        # To work around this, we duplicate the flipped mesh again, so we can copy the drivers over from that copy to the merged version...
        bpy.ops.object.duplicate()
        copy_of_flipped = context.active_object
        copy_of_flipped.select_set(False)

        flipped_o.select_set(True)
        obj.select_set(True)
        # We want to be sure the original is the active so the object name doesn't get a .001
        context.view_layer.objects.active = obj
        bpy.ops.object.join()

        combined_object = context.active_object

        # Copy drivers from the duplicate.
        if hasattr(copy_of_flipped.data.shape_keys, "animation_data") and hasattr(
            copy_of_flipped.data.shape_keys.animation_data, "drivers"
        ):
            for old_D in copy_of_flipped.data.shape_keys.animation_data.drivers:
                for sk in combined_object.data.shape_keys.key_blocks:
                    if sk.name in old_D.data_path:
                        # Create the driver...
                        new_D = combined_object.data.shape_keys.driver_add(
                            'key_blocks["' + sk.name + '"].value'
                        )
                        new_d = new_D.driver
                        old_d = old_D.driver

                        expression = old_d.expression
                        # The beginning of shape key names will indicate which axes should be flipped... What an awful solution! :)
                        flip_x = False
                        flip_y = False
                        flip_z = False
                        flip_flags = sk.name.split("_")[0]
                        # This code is just getting better :)
                        if flip_flags in ['XYZ', 'XZ', 'XY', 'YZ', 'Z']:
                            if ('X') in flip_flags:
                                flip_x = True
                            if ('Y') in flip_flags:
                                flip_y = True
                            if ('Z') in flip_flags:
                                flip_z = True

                        for v in old_d.variables:
                            new_v = new_d.variables.new()
                            new_v.name = v.name
                            new_v.type = v.type
                            for i in range(len(v.targets)):
                                if new_v.type == 'SINGLE_PROP':
                                    new_v.targets[i].id_type = v.targets[i].id_type
                                new_v.targets[i].id = v.targets[i].id
                                new_v.targets[i].bone_target = v.targets[i].bone_target
                                new_v.targets[i].data_path = v.targets[i].data_path
                                new_v.targets[i].transform_type = v.targets[i].transform_type
                                new_v.targets[i].transform_space = v.targets[i].transform_space

                            if (
                                new_v.targets[0].bone_target
                                and "SCALE" not in v.targets[0].transform_type
                                and (v.targets[0].transform_type.endswith("_X") and flip_x)
                                or (v.targets[0].transform_type.endswith("_Y") and flip_y)
                                or (v.targets[0].transform_type.endswith("_Z") and flip_z)
                            ):
                                # Flipping sign - this is awful, I know.
                                if "-" + new_v.name in expression:
                                    expression = expression.replace(
                                        "-" + new_v.name, "+" + new_v.name
                                    )
                                elif "+ " + new_v.name in expression:
                                    expression = expression.replace(
                                        "+ " + new_v.name, "- " + new_v.name
                                    )
                                else:
                                    expression = expression.replace(new_v.name, "-" + new_v.name)

                        new_d.expression = expression

        # Delete the copy
        copy_of_flipped.select_set(True)
        combined_object.select_set(False)
        bpy.ops.object.delete(use_global=False)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)

        # Mesh cleanup
        if self.remove_doubles:
            bpy.ops.mesh.remove_doubles()

        bpy.ops.object.mode_set(mode='OBJECT')
        if self.weighted_normals and "calculate_weighted_normals" in dir(bpy.ops.object):
            bpy.ops.object.calculate_weighted_normals()

        # Restore scale
        context.active_object.scale = org_scale

        self.report({'INFO'}, "Applied X-Mirror modifier with shape keys.")

        return {'FINISHED'}


def draw_force_apply_mirror(self, context):
    self.layout.separator()
    self.layout.operator(EASYWEIGHT_OT_force_apply_mirror.bl_idname, icon='MOD_MIRROR')

registry = [EASYWEIGHT_OT_force_apply_mirror]

def register():
    bpy.types.MESH_MT_shape_key_context_menu.append(draw_force_apply_mirror)

def unregister():
    bpy.types.MESH_MT_shape_key_context_menu.remove(draw_force_apply_mirror)
