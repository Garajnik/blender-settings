import bpy 
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

import os
import sys

from .utils import SBConstants
from .messages import print_message
from .background_and_progress import BakeInProgress as Bip


class SimpleBake_OT_Apply_Bakes_To_Original(Operator):
    """Apply the baked textures to the original objects"""
    bl_idname = "simplebake.apply_bakes_to_original"
    bl_description = "Apply the baked textures to the original objects"
    bl_label = "Apply bakes to original"

    bake_operation_id: StringProperty()

    def execute(self, context):

        if Bip.running_sequence and not Bip.running_sequenc_last:
            return {'FINISHED'} #Nope out if this is part of a sequence unless last

        for m in bpy.data.materials:
            if ("SB_baked_orig_objects" in m) and ("SB_bake_operation_id" in m):
                if m["SB_bake_operation_id"] == self.bake_operation_id:
                    os = list(m["SB_baked_orig_objects"])
                    for o_name in os:
                        if (obj:=context.scene.objects.get(o_name)):

                            actual_obj = None
                            #Is this a proxy object for sidestep?
                            if "SB_proxy_bake_object" in obj:
                                actual_obj_name = obj["SB_proxy_bake_object"]

                                #Find a sidestepped object with this tag
                                for o in context.scene.objects:
                                    if "SB_replaced_orig_name" in o and o["SB_replaced_orig_name"] == actual_obj_name:
                                        actual_obj = o
                            else:
                                actual_obj = obj

                            if actual_obj == None:
                                print_message(context, "ERROR: Apply bakes to original object operator couldn't locate original object!!")
                                return {'CANCELLED'}

                            for slot in actual_obj.material_slots:
                                slot.material = m
        return {'FINISHED'}

                
class SimpleBake_OT_Copy_And_Apply(Operator):
    """Copy the baked objects and apply baked textures"""
    bl_idname = "simplebake.copy_and_apply"
    bl_description = "Copy baked objects and apply bakes"
    bl_label = "Copy and apply"
    
    target_object_name: StringProperty()
    bake_operation_id: StringProperty()
    global_mode: StringProperty()
    decals_override: BoolProperty(default=False)

    def import_cyclesbake_mat_setup(self, context, new_obj, merged=False):


        if self.cyclesbake_mat_format == "emission":
            import_mat_name = "SB_cyclesbake_e"
        elif self.cyclesbake_mat_format == "background":
            import_mat_name = "SB_cyclesbake_b"
        else:
            import_mat_name = "SB_cyclesbake_p"

        rm_list = [mat.name for mat in bpy.data.materials if mat.name == import_mat_name]
        for rm_name in rm_list:
            mat = bpy.data.materials.get(rm_name)
            if mat != None:
                bpy.data.materials.remove(mat)

        path = os.path.dirname(__file__) + "/resources/copy_and_apply_mats.blend/Material/"
        bpy.ops.wm.append(filename=import_mat_name, directory=path)
        mat = bpy.data.materials[import_mat_name]
        
        if merged:
            mat.name = f"{self.merged_bake_name}_Baked"
            mat["SB_bake_operation_id"] = self.bake_operation_id
        elif not self.mat_only:
            mat.name = f"{new_obj.name}" #Already includes "_baked"
        else:
            mat.name = f"{self.target_object_name}_baked"

        if new_obj !=None:
            #Assign to object
            new_obj.data.materials.append(mat)

        return mat

    
    def import_pbr_mat_setup(self, context, new_obj, merged=False):
        sbp = context.scene.SimpleBake_Props
        
        #Decals
        if self.decals_override:
            if self.used_glossy and self.used_directx:
                import_mat_name = "SB_pbr_directx_and_glossy_decals"
            elif self.used_glossy:
                import_mat_name = "SB_pbr_glossy_decals"
            elif self.used_directx:
                import_mat_name = "SB_pbr_directx_decals"
            else:
                import_mat_name = "SB_standard_pbr_decals"

        #Not decals
        else:
            if self.used_glossy and self.used_directx:
                import_mat_name = "SB_pbr_directx_and_glossy"
            elif self.used_glossy:
                import_mat_name = "SB_pbr_glossy"
            elif self.used_directx:
                import_mat_name = "SB_pbr_directx"
            else:
                import_mat_name = "SB_standard_pbr"
        
        #Import the PBR node setup that we need and assign to object
        rm_list = [mat.name for mat in bpy.data.materials if mat.name == import_mat_name]
        for rm_name in rm_list:
            mat = bpy.data.materials.get(rm_name)
            if mat != None:
                bpy.data.materials.remove(mat)


        path = os.path.dirname(__file__) + "/resources/copy_and_apply_mats.blend/Material/"
        bpy.ops.wm.append(filename=import_mat_name, directory=path)
        mat = bpy.data.materials[import_mat_name]
        
        #Assign to object
        if new_obj != None:
            new_obj.data.materials.append(mat)
        
        if merged:
            mat.name = f"{self.merged_bake_name}_Baked"
            mat["SB_bake_operation_id"] = self.bake_operation_id
        elif not self.mat_only:
            mat.name = f"{new_obj.name}" #Already includes "_baked"
        else:
            mat.name = f"{self.target_object_name}_baked"

        #If we are baking alpha or transparency, set the blend mode
        if sbp.selected_alpha or sbp.selected_trans:
            mat.blend_method = "BLEND"

        return mat
        
    def create_cyclesbake_setup(self, context, new_obj):
        mat = self.import_cyclesbake_mat_setup(context, new_obj)
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        
        #The non-specials texture
        tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                and i["SB_bake_operation_id"] == self.bake_operation_id
                and "SB_this_bake" in i and i["SB_this_bake"] not in SBConstants.ALL_SPECIALS
                and i["SB_bake_object"] == self.target_object_name
                ])
        assert len(tex) == 1
        tex = tex[0]
        
        node = [n for n in nodes if n.label=="cyclesbake"]
        assert len(node) == 1
        node = node[0]
        node.image = tex
        
        #The specials textures
        for bake_type in SBConstants.ALL_SPECIALS:
            node = [n for n in nodes if n.label==bake_type]
            if len(node) == 0: continue #E.g. Glossy will not be there for standard
            else: node = node[0]
            tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                            and i["SB_bake_operation_id"] == self.bake_operation_id
                            and "SB_this_bake" in i and i["SB_this_bake"] == bake_type
                            and i["SB_bake_object"] == self.target_object_name
                            ])
            if len(tex) == 1:
                tex = tex[0]
                node.image = tex
            else:
                nodes.remove(node)
        return mat
    
    def create_cyclesbake_setup_merged(self, context, new_obj):
        
        #Check if we already have the merged texture
        mat_name = f"{self.merged_bake_name}_Baked"
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
            if "SB_bake_operation_id" in mat and mat["SB_bake_operation_id"] == self.bake_operation_id:
                mat = bpy.data.materials[mat_name]
                #Assign existing merged mat to object and leave
                if new_obj != None:
                    new_obj.data.materials.append(mat)
                return mat
        
        mat = self.import_cyclesbake_mat_setup(context, new_obj, merged=True)
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        
        #The non-specials texture
        tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                and i["SB_bake_operation_id"] == self.bake_operation_id
                and "SB_this_bake" in i and i["SB_this_bake"] not in SBConstants.ALL_SPECIALS
                ])
        assert len(tex) == 1
        tex = tex[0]
        
        node = [n for n in nodes if n.label=="cyclesbake"]
        assert len(node) == 1
        node = node[0]
        node.image = tex
        
        #The specials textures
        for bake_type in SBConstants.ALL_SPECIALS:
            node = [n for n in nodes if n.label==bake_type]
            if len(node) == 0: continue #E.g. Glossy will not be there for standard
            else: node = node[0]
            tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                            and i["SB_bake_operation_id"] == self.bake_operation_id
                            and "SB_this_bake" in i and i["SB_this_bake"] == bake_type])
            if len(tex) == 1:
                tex = tex[0]
                node.image = tex
            else:
                nodes.remove(node)
        return mat

    def create_pbrdecal_setup(self, context, new_obj):


        BAKE_OP_PREFIX = "DECALSBASE_"
        #Called with the prefix. S2A textures will NOT have the prefix


        #Setup
        mat = self.import_pbr_mat_setup(context, new_obj)
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        bake_types = SBConstants.ALL_PBR_MODES #Every possible bake mode for PBR
        bake_types += SBConstants.ALL_SPECIALS #Every possible bake mode for specials


        #Find the master decal alpha
        decal_alpha_tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i
                            and i["SB_bake_operation_id"]== self.bake_operation_id.replace(BAKE_OP_PREFIX, "") and
                            "SB_this_bake" in i and i["SB_this_bake"] == SBConstants.PBR_ALPHA and
                            "SB_global_mode" in i and i["SB_global_mode"] == SBConstants.PBRS2A
                           ])
        assert(len(decal_alpha_tex)==1)
        node = [n for n in nodes if n.label=="Master_Decal_Alpha"]
        assert(len(node)==1)
        node[0].image = decal_alpha_tex[0]


        #Now the base/target object PBR textures:
        for bake_type in bake_types:
            node = [n for n in nodes if n.label==bake_type]
            if len(node) == 0: continue #E.g. Glossy will not be there for standard
            else: node = node[0]
            tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i and
                            i["SB_bake_operation_id"] == self.bake_operation_id and
                            "SB_this_bake" in i and i["SB_this_bake"] == bake_type and
                            "SB_bake_object" in i and i["SB_bake_object"] == self.target_object_name])
            if len(tex) == 1:
                tex = tex[0]
                node.image = tex
            else:
                nodes.remove(node)



        # #Now the Decal/S2A textures:
        for bake_type in bake_types:
            node = [n for n in nodes if n.label=="Decal_" + bake_type]
            if len(node) == 0: continue #E.g. Glossy will not be there for standard
            else: node = node[0]
            tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i and
                            i["SB_bake_operation_id"] == self.bake_operation_id.replace(BAKE_OP_PREFIX, "") and
                            "SB_this_bake" in i and i["SB_this_bake"] == bake_type and
                            "SB_bake_object" in i and i["SB_bake_object"] == self.target_object_name])
            if len(tex) == 1:
                tex = tex[0]
                node.image = tex
            else:
                nodes.remove(node)

        #Now get rid of the unused MixRGB nodes
        mnodes = [n for n in nodes if n.bl_idname == "ShaderNodeMix"]
        for mnode in mnodes:
            a_color_input = [i for i in mnode.inputs if i.identifier=="A_Color"][0]
            #factor_float_input = [i for i in mnode.inputs if i.identifier=="Factor_Float"][0]
            #color_output = [o for o in mnode.outputs if o.identifier=="Result_Color"][0]

            if len(a_color_input.links) == 0:
                #fsocket = factor_float_input.links[0].from_socket
                #tsocket = color_output.links[0].to_socket
                #node_tree.links.new(fsocket, tsocket)
                nodes.remove(mnode)


        return mat
        
        
    def create_pbr_setup(self, context, new_obj):

        
        mat = self.import_pbr_mat_setup(context, new_obj)
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        
        bake_types = SBConstants.ALL_PBR_MODES #Every possible bake mode for PBR
        bake_types += SBConstants.ALL_SPECIALS #Every possible bake mode for specials
        #Set the textures
        for bake_type in bake_types:
            node = [n for n in nodes if n.label==bake_type]
            if len(node) == 0: continue #E.g. Glossy will not be there for standard
            else: node = node[0]
            tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                            and i["SB_bake_operation_id"] == self.bake_operation_id
                            and "SB_this_bake" in i and i["SB_this_bake"] == bake_type
                            and "SB_bake_object" in i and i["SB_bake_object"] == self.target_object_name])
            if len(tex) == 1:
                tex = tex[0]
                node.image = tex
            else:
                nodes.remove(node)
        return mat
        
    def create_pbr_setup_merged(self, context, new_obj):

        
        #Check if we already have the merged texture
        mat_name = f"{self.merged_bake_name}_Baked"
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
            if "SB_bake_operation_id" in mat and mat["SB_bake_operation_id"] == self.bake_operation_id:
                mat = bpy.data.materials[mat_name]
                #Assign existing merged mat to object and leave
                if new_obj !=None:
                    new_obj.data.materials.append(mat)
                return mat
                
        #No existing merged bake material
        mat = self.import_pbr_mat_setup(context, new_obj, merged=True)
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        
        bake_types = SBConstants.ALL_PBR_MODES #Every possible bake mode for PBR
        bake_types += SBConstants.ALL_SPECIALS #Every possible bake mode for specials
        #Set the textures
        for bake_type in bake_types:
            node = [n for n in nodes if n.label==bake_type]
            if len(node) == 0: continue #E.g. Glossy will not be there for standard
            else: node = node[0]
            tex = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                            and i["SB_bake_operation_id"] == self.bake_operation_id
                            and "SB_this_bake" in i and i["SB_this_bake"] == bake_type
                            and "SB_merged_bake" in i and i["SB_merged_bake"] == True
                            and "SB_merged_bake_name" in i and i["SB_merged_bake_name"] == self.merged_bake_name
                            ])
            if len(tex) == 1:
                tex = tex[0]
                node.image = tex
            else:
                nodes.remove(node)
        
        return mat
        
    def hook_up_glTF_node(self, context, mat):
        node_tree = mat.node_tree
        nodes = node_tree.nodes
        
        glTF_node = [n for n in nodes if n.label == "gltf"]
        assert(len(glTF_node))
        glTF_node = glTF_node[0]
        
        target_option = self.glTF_option
        
        target_node = [n for n in nodes if n.label == target_option]
        assert(len(target_node))
        target_node = target_node[0]
            
        node_tree.links.new(target_node.outputs[0], glTF_node.inputs[0])
            
    def create_object(self,context):
        sbp = context.scene.SimpleBake_Props

        source_obj = context.scene.objects[self.target_object_name]

        if (source_obj.name + "_Baked") in context.scene.objects:
            bpy.data.objects.remove(context.scene.objects[source_obj.name + "_Baked"])

        new_obj = source_obj.copy()
        new_obj.data = source_obj.data.copy()

        new_obj["SB_copy_and_apply_from"] = source_obj.name
        new_obj["SB_bake_operation_id"] = self.bake_operation_id

        new_obj.name = source_obj.name + "_Baked"

        new_obj.data.materials.clear()

        if "SB_BG_HIDE" in new_obj:
            del new_obj["SB_BG_HIDE"]

        #Create a collection for our baked objects if it doesn't exist
        col_name = "SimpleBake_Bakes_Background" if self.in_background else "SimpleBake_Bakes"

        if col_name not in bpy.data.collections:
            col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(col)
        else:
            col = bpy.data.collections[col_name]
            if col_name not in context.scene.collection.children:
                context.scene.collection.children.link(col)

        try: col.color_tag = "COLOR_05"
        except AttributeError: pass

        #Make sure it's visible and enabled for current view laywer
        context.view_layer.layer_collection.children[col_name].exclude = False
        context.view_layer.layer_collection.children[col_name].hide_viewport = False

        #Link object to our new collection
        col.objects.link(new_obj)

        #Remove tags from geo nodes sidestep
        if "SB_proxy_bake_object" in new_obj:
            del new_obj["SB_proxy_bake_object"]
        if "SB_sidestepd_orig_target" in new_obj:
            del new_obj["SB_sidestepd_orig_target"]
        if "SB_replaced_orig_name" in new_obj:
            del new_obj["SB_replaced_orig_name"]


        #Set active uv to one we used for bake for this object. Remove others.
        bake_uv_name = source_obj["SB_uv_used_for_bake"]
        new_obj.data.uv_layers.active = new_obj.data.uv_layers[bake_uv_name]
        del_list = [uvl.name for uvl in new_obj.data.uv_layers if uvl.name != bake_uv_name]
        [new_obj.data.uv_layers.remove(new_obj.data.uv_layers[name]) for name in del_list]

        #Hide source objects?
        if self.hide_source_objects:
            source_obj.hide_set(True)

        return new_obj


    def remove_unused_pbr(self,context,mat):

        node_tree = mat.node_tree
        nodes = node_tree.nodes

        d_nodes_names = [n.name for n in nodes if n.bl_idname == "ShaderNodeDisplacement"]
        nm_nodes_names = [n.name for n in nodes if n.bl_idname == "ShaderNodeNormalMap"]
        gltf_node_names =[n.name for n in nodes if n.bl_idname == "ShaderNodeGroup" and n.label == "gltf"]

        node_names = d_nodes_names + nm_nodes_names + gltf_node_names

        for name in node_names:
            if (n := nodes.get(name)):
                unused = True
                for i in n.inputs:
                    if len(i.links)>0:
                        unused = False
                if unused:
                    nodes.remove(n)

        rr_nodes = [n.name for n in nodes if n.bl_idname == "NodeReroute"]

        for name in rr_nodes:
            if (n := nodes.get(name)):
                unused = True
                for o in n.outputs:
                    if len(o.links)>0:
                        unused = False
                if unused:
                    nodes.remove(n)


    def execute(self, context):
        sbp = context.scene.SimpleBake_Props

        if Bip.running_sequence and not Bip.running_sequence_last:
            print_message(context, "No object preperation - sequence and not last run")
            return {'FINISHED'} #Nope out if this is part of a sequence

        used_glossy = True if sbp.rough_glossy_switch == SBConstants.PBR_GLOSSY else False
        used_directx = True if sbp.normal_format_switch == SBConstants.NORMAL_DIRECTX else False

        #Grab what we need from the panel
        self.used_glossy = used_glossy
        self.used_directx = used_directx
        self.hide_source_objects = sbp.hide_source_objects
        self.glTF = sbp.create_glTF_node
        self.glTF_option = sbp.glTF_selection
        self.merged_bake = sbp.merged_bake
        self.cyclesbake_mat_format = sbp.cyclesbake_copy_and_apply_mat_format
        self.merged_bake_name = sbp.merged_bake_name
        self.mat_only = True if sbp.apply_bakes_to_original else False
        self.in_background = True if "--background" in sys.argv or sbp.fake_background else False


        print_message(context, f"Creating prepared object {self.target_object_name}")

        if self.mat_only:
            new_obj = None
        else:
            new_obj=self.create_object(context)

        if self.decals_override:
            mat = self.create_pbrdecal_setup(context,new_obj)
        elif self.global_mode in [SBConstants.PBR, SBConstants.PBRS2A] and self.merged_bake:
            mat = self.create_pbr_setup_merged(context,new_obj)
        elif self.global_mode in [SBConstants.PBR, SBConstants.PBRS2A]:
            mat = self.create_pbr_setup(context, new_obj)
        elif self.global_mode in [SBConstants.CYCLESBAKE, SBConstants.CYCLESBAKE_S2A] and self.merged_bake:
            mat = self.create_cyclesbake_setup_merged(context, new_obj)
        elif self.global_mode in [SBConstants.CYCLESBAKE, SBConstants.CYCLESBAKE_S2A]:
            mat = self.create_cyclesbake_setup(context, new_obj)
        else:
            print_message(context, "Something went wrong with Copy and Apply")

        #Need to find this if applying to original objects:
        if "SB_baked_orig_objects" in mat:
            orig_objects = mat["SB_baked_orig_objects"]
        else:
            orig_objects = []
        orig_objects.append(self.target_object_name)
        mat["SB_baked_orig_objects"] = orig_objects
        mat["SB_bake_operation_id"] = self.bake_operation_id
        
        #Hook up glTF node?
        if self.glTF:
            self.hook_up_glTF_node(context, mat)

        #Make sure this happens after the GLTF node is corrected
        if self.global_mode in [SBConstants.PBR, SBConstants.PBRS2A] or self.decals_override:
            self.remove_unused_pbr(context, mat)


        # #If in background, save the Blend file on the way out
        # if self.in_background:
        #     print_message(context, "Running in BG - Saving blend file")
        #     bpy.ops.wm.save_mainfile()

        return {'FINISHED'}

classes = ([
    SimpleBake_OT_Copy_And_Apply,
    SimpleBake_OT_Apply_Bakes_To_Original
        ])

def register():
    
    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
