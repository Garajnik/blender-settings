
#PBR bake with Target = Sidestep everything
#Decals = Sidestep everything
#Automatch = Sidestep everything
#CyclesBake = No sidetep unless specials
#Message about mods being applied?



import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, BoolProperty

import os
from pathlib import Path
import tempfile
from datetime import datetime
from math import floor
import sys
import shutil

from ..utils import SBConstants, transfer_tags, show_message_box, object_list_to_names_list, find_closest_obj, get_bake_objects, blender_refresh, is_blend_saved, find_3d_viewport, disable_impossible, specials_selection_to_list
from ..material_management import SimpleBake_OT_Material_Backup as MatManager
from ..background_and_progress import BakeInProgress as Bip
from ..messages import print_message
import re
from .. import __package__ as base_package


class PrestartFailed(Exception):
    pass


def common_prestart(context, decals=False, automatch=False):

    sbp = context.scene.SimpleBake_Props
    prefs = context.preferences.addons[base_package].preferences

    pbr_bake = True if sbp.global_mode == "PBR" else False

    def prestart_actions():

        Bip.was_error = False

        #Refresh objects list
        bpy.ops.simplebake.refresh_bake_object_list()

        disable_impossible(context)

        #Things are much easier if we fix this
        if (to:=sbp.targetobj)!=None and (i:=sbp.objects_list.find(to.name))!=-1:
            print_message(context,f"Removing target object {to.name} from bake list")
            sbp.objects_list.remove(i)

        #Save file?
        if prefs.saveonbake and is_blend_saved():
            bpy.ops.wm.save_mainfile()

        #Switch to solid shading?
        if prefs.solidshadingonbake:
            for screen in bpy.data.screens:
                for space in find_3d_viewport(screen=screen):
                    space.shading.type = "SOLID"

        #Sidestep any geometary nodes (before starting checks so materials becomme "real")
        if pbr_bake or len(specials_selection_to_list(context))>0:
            bpy.ops.simplebake.sidestep_geo_nodes()
            #if decals and sbp.targetobj!=None:
                #bpy.ops.simplebake.sidestep_geo_nodes(decals_target_name = sbp.targetobj.name)

        #Starting checks
        if automatch:
            match_mode = "NAME" if sbp.auto_match_mode=="name" else "POSITION"
            hl_matches = {}
            orig_objects_list=[]
            result = match_high_low_objects(context, hl_matches, orig_objects_list, match_mode)
            if not result:
                raise PrestartFailed

            #Starting checks
            for lo in hl_matches.keys():
                if pbr_bake:
                    sbp.targetobj = context.scene.objects[lo]
                else:
                    sbp.targetobj_cycles = context.scene.objects[lo]
                if 'CANCELLED' in bpy.ops.simplebake.starting_checks():
                    raise PrestartFailed

                if pbr_bake:
                    sbp.targetobj = None
                else:
                    sbp.targetobj_cycles = None
        else:
            if 'CANCELLED' in bpy.ops.simplebake.starting_checks():
                raise PrestartFailed("Starting checks failed!")

        #Fresh start for materials
        bpy.ops.simplebake.material_backup(mode=MatManager.MODE_INITIALISE)

        #If newer than Blender 4.0, run this before the Macro!! But after existing material tags have been wiped and after starting checks
        if bpy.app.version >= (4,1,0) and pbr_bake:
            bpy.ops.simplebake.pbr_pre_bake()
            if decals:
                bpy.ops.simplebake.pbr_pre_bake(override_target_object_name = sbp.targetobj.name)

    try:
        prestart_actions()
    except PrestartFailed as e:
        print_message(context, "BAKE ABORTED - Check pop-up for errors")
        Bip.is_baking = False
        Bip.was_error = True

        #Undo actions from sidestep and also pre-bake
        bpy.ops.simplebake.material_backup(mode="working_restore")
        bpy.ops.simplebake.material_backup(mode="master_restore")
        bpy.ops.simplebake.reverse_geo_nodes_sidestep()

        return False

    print_message(context,"Common Prestart Actions Complete")
    return True

def clean_up_after_bg_spawn(context):
    print_message(context, "Cleaning up after BG spawn")
    #Undo actions from sidestep and also pre-bake
    bpy.ops.simplebake.material_backup(mode="master_restore")
    bpy.ops.simplebake.reverse_geo_nodes_sidestep()

    return True



def match_high_low_objects(context, hl_matches, orig_objects_list, match_mode):
    print_message(context, "Matching high and low poly objects commencing")
    sbp = context.scene.SimpleBake_Props

    #Refresh the bake objects list (couldn't hurt)
    bpy.ops.simplebake.refresh_bake_object_list()

    #If name mode, remove invalid before we consider anything else
    if match_mode == "NAME":
        #Remove invalid
        to_remove = []
        for o in sbp.objects_list:
            if "_high" not in o.name.lower():
                to_remove.append(o.name)
        for r in to_remove:
            i = sbp.objects_list.find(r)
            sbp.objects_list.remove(i)

    hl_matches.clear()
    objs = [i.obj_point for i in sbp.objects_list]
    orig_objects_list.clear()
    orig_objects_list.extend(objs)

    if match_mode == "NAME":

        hs = [o.name for o in objs if o.name.lower().endswith("_high")]
        hs_dict = {}#Lowcase to real
        for i in hs:
            hs_dict[i.lower()] = i

        #ls = [o.name for o in context.scene.objects] #Every object is a potential low at this point
        ls = [o.name for o in context.scene.objects if o.name.lower().endswith("_low")]
        ls_dict = {}#Lowcase to real
        for i in ls:
            ls_dict[i.lower()] = i

        matched_ls = []

        for i in hs_dict.keys(): #LOWER names of high poly objects
            if i.replace("_high", "_low") in ls_dict.keys():
                hl_matches[ls_dict[i.replace("_high", "_low")]] = hs_dict[i]

        # Create a normalized version of lows to map to highs
        #normalized_to_original = {re.sub(r'_low$', '', s, flags=re.IGNORECASE): s for s in ls}

        #for high in hs:
            #base_string = re.sub(r'_high$', '', high, flags=re.IGNORECASE)
            #if base_string in normalized_to_original:
                # low_string = normalized_to_original[base_string]
                # hl_matches[low_string] = high
                # matched_ls.append(low_string)



        ls = matched_ls

    if match_mode == "POSITION":
        hs = [o.name for o in sbp.objects_list]
        ls = []
        #Detect low by position for every high object
        for h in hs:
            l = find_closest_obj(context, h)
            if l != None:
                ls.append(l.name)
                hl_matches[l.name] = h

    #If there were actually no matches, abort here:
    if len(hl_matches) <1:
        print_message(context, "BAKE ABORTED (AUTO) - Check pop-up for errors")
        messages = ([
            "ERROR: You are trying to bake auto match",
            "high and low poly, but there are no matches!"
            ])
        show_message_box(context, messages, "Errors occured", icon = 'ERROR')
        Bip.is_baking = False
        return False


    #Now we have our list, purge all low objects from the bake objects list
    #Not sure it's useful, but you could have an object being both a high and a low. Only remove if not also a high
    ls_unique = [lo for lo in ls if lo not in hs]
    # for lo in ls_unique:
    #     i = sbp.objects_list.find(lo)
    #     if i>-1: sbp.objects_list.remove(i)

    for lo in ls:
        i = sbp.objects_list.find(lo)
        if i>-1: sbp.objects_list.remove(i)


    #Dry run for starting checks
    for lo in ls:
        if sbp.global_mode == SBConstants.PBR: sbp.targetobj = context.scene.objects[lo]
        else: sbp.targetobj_cycles = context.scene.objects[lo]
        if 'CANCELLED' in bpy.ops.simplebake.starting_checks(): #Should work out it's own mode from panel selections
            print_message(context, "BAKE ABORTED (AUTO) - Check pop-up for errors")
            Bip.is_baking = False
            return False
    return True



class SimpleBake_OT_Set_Sample_Count(Operator):
    bl_idname = "simplebake.set_sample_count"
    bl_label = "Set the sample count"
    
    sample_count: IntProperty()
    
    def execute(self, context):
        context.scene.cycles.samples = self.sample_count
        print_message(context, f"Sample count now {self.sample_count}")
        return {'FINISHED'}

class SimpleBake_OT_Compositor_Denoise(Operator):
    """Run the target image through compositor denoise"""
    bl_idname = "simplebake.compositor_denoise"
    bl_label = "Denoise"
    
    bake_operation_id: StringProperty()
    #bake_type: StringProperty()
    
    def execute(self, context):
        
        print_message(context, "Running compositor denoiser")
        
        imgs = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
                 and i["SB_bake_operation_id"] == self.bake_operation_id
                 and i["SB_this_bake"] not in SBConstants.ALL_PBR_MODES #Never denoise PBR
                 and i["SB_this_bake"] not in SBConstants.COMP_NODENOISE_SPECIALS #Only certian specials get denoise
                 and i["SB_denoised"] == False
                 ])

        if len(imgs)== 0:
            print_message(context, "No images for compositor denoiser")
            return {'FINISHED'}

        print_message(context, f"Compositor denoise for {[i.name for i in imgs]}")

        #[bpy.data.scenes.remove(s) for s in bpy.data.scenes if s.name == "compositor_denoise"]
        s = bpy.data.scenes.get("compositor_denoise")
        if s!=None:
            bpy.data.scenes.remove(s)

        path = os.path.dirname(__file__) + "/../resources/denoise.blend/Scene/"
        bpy.ops.wm.append(filename="compositor_denoise", directory=path)

        s = bpy.data.scenes.get("compositor_denoise")
        if s==None:
            print("ERROR: Import of compositor denoise scene failed")
            return {'CANCELLED'}

        
        #Should all be same size
        s.render.resolution_x = imgs[0].size[0]
        s.render.resolution_y = imgs[0].size[1]
        
        node_tree = s.node_tree
        nodes = node_tree.nodes
        
        i_node = [n for n in nodes if n.label == "image"]
        assert(len(i_node) == 1)
        i_node= i_node[0]
        
        temp_dir = Path(tempfile.TemporaryDirectory().name)

        
        for img in imgs:

            #Get some settings
            #s.render.image_settings.color_management = "OVERRIDE"
            s.render.image_settings.file_format = img.file_format
            s.render.image_settings.color_depth = img["SB_bit_depth"]
            s.render.image_settings.color_mode = img["SB_channels"]
            #s.view_settings.view_transform = img["SB_view_transform"]
            s.view_settings.view_transform = "Standard"

            name = img.name
            external_path = img.filepath

            #Save the image to tmp dir
            #img.save_render(str(temp_dir / f"{name}.exr"), scene=s)

            tiles_nums = [t.number for t in img.tiles]
            for tile_num in tiles_nums:
                #Load the tile in as an individual image
                i = bpy.data.images.load(external_path.replace("<UDIM>", str(tile_num)))
                #i.colorspace_settings.name = img.colorspace_settings.name
                i_node.image =i

                #Render and get result
                bpy.ops.render.render(use_viewport=False, scene=s.name)
                render_result_image = bpy.data.images["Render Result"]

                #File should already exist. Remove it or will silently fail.
                if os.path.exists(bpy.path.abspath(external_path)):
                    os.remove(bpy.path.abspath(external_path))

                #Save this over the file path of the tile image
                #Only seems to work for abspath?
                external_path = bpy.path.abspath(external_path)
                render_result_image.save_render(external_path.replace("<UDIM>", str(tile_num)), scene=s)

                #Remove the tile image we loaded individually
                bpy.data.images.remove(i)

            #All tiles done for this image, reload the UDIM image
            img.reload() #We've updated 1 or more tiles and Blender still has them in the buffer'
            img.save()
            img["SB_denoised"] = True

            #transfer_tags(img, new_img)

        #All done
        [bpy.data.scenes.remove(s) for s in bpy.data.scenes if s.name == "compositor_denoise"]

        return {'FINISHED'}

class SimpleBake_OT_Select_Only_This(Operator):
    """Select only the specified object"""
    bl_idname = "simplebake.select_only_this"
    bl_label = "Select"
    
    hidden = []
    
    target_object_name: StringProperty()
    high_object_name: StringProperty()
    isolate: BoolProperty(default=False)
    isolate_s2a: BoolProperty(default=False)
    auto_match: BoolProperty(default=False)

    def execute(self, context):

        obj = context.scene.objects[self.target_object_name]

        if self.auto_match:
            #Hide everything
            for o in context.scene.objects:
                if o.type=="MESH":
                    o.hide_render = True
                    self.__class__.hidden.append(o.name)

            #Unhide target and high
            context.scene.objects[self.target_object_name].hide_render = False
            context.scene.objects[self.high_object_name].hide_render = False

            #Return here - we don't actually want to mess with the selection
            return {'FINISHED'}


        if self.isolate_s2a:
            bake_objs = object_list_to_names_list(context)
            bake_objs.append(self.target_object_name)

            #Cage object too if there is one
            if context.scene.render.bake.cage_object != None:
                bake_objs.append(context.scene.render.bake.cage_object.name)

            #Hide everything
            for o in context.scene.objects:
                #if o.name not in bake_objs and o.type=="MESH":
                if o.hide_render == False:
                    o.hide_render = True
                    self.__class__.hidden.append(o.name)

            #Unhide object in bake objects list
            for o_name in bake_objs:
                context.scene.objects[o_name].hide_render = False

            #Return here - we don't actually want to mess with the selection
            return {'FINISHED'}

        if self.isolate:
            #Unhide the object we are baking. It may not have been unhidden yet
            obj.hide_render = False

            #Hide all other objects
            for o in context.scene.objects:
                if o.name != self.target_object_name and o.type=="MESH":
                    if o.hide_render == False:
                        o.hide_render = True
                        self.__class__.hidden.append(o.name)


        #bpy.ops.object.select_all(action="DESELECT")
        [o.select_set(state=False) for o in context.scene.objects]
        obj.select_set(state=True)
        context.view_layer.objects.active = obj
        
        return {'FINISHED'}


class SimpleBake_OT_Select_Selected_To_Active(Operator):
    """Select the bake objects as selected, and target object as active"""
    bl_idname = "simplebake.select_selected_to_active"
    bl_label = "Select"
    
    mode: StringProperty()
    specific_high: StringProperty()
    specific_low: StringProperty()
    
    def execute(self, context):
        sbp = context.scene.SimpleBake_Props
        objs = [i.obj_point for i in sbp.objects_list]

        bpy.ops.object.select_all(action="DESELECT")

        if self.mode == SBConstants.PBRS2A:
            target_obj = sbp.targetobj

        if self.mode == SBConstants.CYCLESBAKE_S2A:
            target_obj = sbp.targetobj_cycles

        if self.mode == SBConstants.PBRS2A_AUTOMATCH:
            target_obj = context.scene.objects[self.specific_low]
            #Overide objects list for this purpose
            objs = [context.scene.objects[self.specific_high]]

        [obj.select_set(state=True) for obj in objs]
        target_obj.select_set(state=True)
        context.view_layer.objects.active = target_obj
        
        return {'FINISHED'}

class CommonBakePrepandFinish:
    #Non-Blender class. No register
    orig_object_selection = []
    orig_active_object = None
    
    orig_object_uvs = {}
    orig_object_uvs_render = {}
    
    orig_render_engine = None
    #packed_images = []
    start_time = None

    high_low_matching_list = {}
    
    

class SimpleBake_OT_Pack_Baked_Images(Operator):
    """Preperation shared by all types of bake"""
    bl_idname = "simplebake.pack_baked_images"
    bl_description = "Pack all baked images into blend file"
    bl_label = "Pack"
    
    bake_operation_id: StringProperty()
    bake_mode: StringProperty()
    
    def execute(self, context):

        #BLOCK THIS FOR NOW
        return {'FINISHED'}


        #Get all primary images for this operation
        imgs = ([i for i in bpy.data.images if "SB_bake_operation_id" in i 
            and i["SB_bake_operation_id"] == self.bake_operation_id
            #and i.name not in CommonBakePrepandFinish.packed_images and
            and "SB_this_bake" in i and i["SB_this_bake"] == self.bake_mode
            ])

        for img in imgs:
            #if img.is_dirty == True:
            if img.packed_file == None:
            #if True:
                print_message(context, f"Packing image {img.name} to blend file")
                img.pack()
                img.use_fake_user = True
                #CommonBakePrepandFinish.packed_images.append(img.name)
        
        return {'FINISHED'}
    
class SimpleBake_OT_Scale_Images_If_Needed(Operator):
    """Preperation shared by all types of bake"""
    bl_idname = "simplebake.scale_images_if_needed"
    bl_description = "Scale images if needed"
    bl_label = "Scale"
    
    bake_operation_id: StringProperty()
    this_bake: StringProperty()
    
    def execute(self, context):
        
        #Scale images if needed
        print_message(context, "Scaling images if needed")
        imgs = ([i for i in bpy.data.images
                 if "SB_bake_operation_id" in i and 
                 i["SB_bake_operation_id"] == self.bake_operation_id and
                 "SB_this_bake" in i and
                 "SB_scaled" in i and not i["SB_scaled"]
                 ])
        sbp = context.scene.SimpleBake_Props
        for img in imgs:
            width = img.size[0]
            height = img.size[1]
            #Just gonna assume if one tile has been resized they all have
            if width != sbp.outputwidth or height != sbp.outputheight:
                print_message(context, f"Scaling {img.name} to {sbp.outputwidth} by {sbp.outputheight}")

                i=0
                ts=len(img.tiles)
                while i < ts:
                    img.tiles.active_index = i
                    img.scale(sbp.outputwidth, sbp.outputheight, tile_index=i)
                    i+=1
            #Either way, we considered it
            img["SB_scaled"] = True
        
        
        return {'FINISHED'} 

def disable_auto_smooth(context):


    obj_names = get_bake_objects(context)
    modded_objs = []
    for o_name in obj_names:
        if not (o:=context.scene.objects.get(o_name)):
            continue
        if o.data.has_custom_normals and o.data.use_auto_smooth:
            o.data.use_auto_smooth = False
            print_message(context, f"Disabling auto-smooth setting for object {o.name} (custom split normals)")
            modded_objs.append(o.name)
    yield True

    for o_name in modded_objs:
        if (obj:=context.scene.objects.get(o_name)):
            print_message(context, f"Renabling auto-smooth setting for object {o_name}")
            obj.data.use_auto_smooth = True

    yield True
das_gen = None

class SimpleBake_OT_Common_Bake_Prep(Operator):
    """Preperation shared by all types of bake"""
    bl_idname = "simplebake.common_bake_prep"
    bl_description = "Preperation shared by all types of bake"
    bl_label = "BakePrep"
    
    def execute(self, context):
        
        print_message(context, "================================")
        print_message(context, "--------SIMPLEBAKE START--------")
        print_message(context, "================================")
        
        if "SB_Crash_Log" in bpy.data.texts:
            bpy.data.texts.remove(bpy.data.texts["SB_Crash_Log"])

        CommonBakePrepandFinish.start_time = datetime.now()
        
        sbp = context.scene.SimpleBake_Props

        #Disable autosmooth for all objects that are relevant to us and have custom normals
        prefs = context.preferences.addons[base_package].preferences
        if prefs.disable_auto_smooth_for_split_normals and bpy.app.version < (4,1,0):
            global das_gen
            das_gen=disable_auto_smooth(context)
            next(das_gen)

        #Auto matching high low needs special treatment
        if (sbp.selected_s2a or sbp.cycles_s2a) and sbp.s2a_opmode=="automatch":
            from .auto_match_operators import SimpleBake_OT_AutoMatch_Operation as amo
            hl_matches = amo.hl_matches
            bake_objects_names = []
            bake_objects_names.extend(list(hl_matches.keys()))
            bake_objects_names.extend(list(hl_matches.values()))
            bake_objects_names = list(set(bake_objects_names)) #Just to be sure
        else:
            bake_objects_names = [o.obj_point.name for o in sbp.objects_list]

        
        print_message(context, "Common bake prep starting")
        
        
        #Tracking number reset
        sbp.current_bake_image_number = 0
        sbp.percent_complete = 0
        
        #Render engine
        CommonBakePrepandFinish.orig_render_engine = context.scene.render.engine
        context.scene.render.engine = 'CYCLES'
        
        #Object selection
        CommonBakePrepandFinish.orig_object_selection = context.selected_objects
        CommonBakePrepandFinish.orig_active_object = context.active_object
        
        #Object orig_object_uvs
        uv_objs_names = bake_objects_names
        if sbp.targetobj != None: uv_objs_names.append(sbp.targetobj.name)
        if sbp.targetobj_cycles != None: uv_objs_names.append(sbp.targetobj_cycles.name)
        for o_name in uv_objs_names:
            obj = context.scene.objects[o_name]
            if obj.data.uv_layers.active != None:
                CommonBakePrepandFinish.orig_object_uvs[o_name] = obj.data.uv_layers.active.name
            #Get UV layer active for render
            uv_active_render = [uv for uv in obj.data.uv_layers if uv.active_render]
            for uv in uv_active_render:
                CommonBakePrepandFinish.orig_object_uvs_render[o_name] = uv.name
            
        #Create a new collection, and add selected objects and target objects to it
        c = bpy.data.collections.get("SimpleBake_Working")
        if c!=None:
            bpy.data.collections.remove(c)

        c = bpy.data.collections.new("SimpleBake_Working")
        context.scene.collection.children.link(c)
        for o_name in bake_objects_names:
            obj = context.scene.objects[o_name]
            if o_name not in c.objects:
                c.objects.link(obj)
            if sbp.targetobj != None and sbp.targetobj.name not in c.objects:
                c.objects.link(sbp.targetobj)
            if sbp.targetobj_cycles != None and sbp.targetobj_cycles.name not in c.objects:
                c.objects.link(sbp.targetobj_cycles)
    
        #Every object must have at least camera ray visibility
        for o_name in bake_objects_names:
            obj = context.scene.objects[o_name]
            obj.visible_camera = True
        if sbp.targetobj != None:
            sbp.targetobj.visible_camera = True
        if sbp.targetobj_cycles != None:
            sbp.targetobj_cycles.visible_camera = True
        
        #In case of crash
        for m in bpy.data.materials:
            if "SB_working_dup" in m: del m["SB_working_dup"]

        return {'FINISHED'}
    
class SimpleBake_OT_Common_Bake_Finishing(Operator):
    """Finishing actions shared by all types of bake"""
    bl_idname = "simplebake.common_bake_finishing"
    bl_description = "Finishing shared by all types of bake"
    bl_label = "BakeFinish"
    
    #baked_number: IntProperty()
    bake_operation_id: StringProperty()
    suppress_report: BoolProperty(default=False)

    #Determined from panel setting
    decal_first_run: BoolProperty(default=False)
    #Determined from overide from this function, as panel setting not reliable when baking target object (update function turns it off)
    decal_second_run: BoolProperty(default=False)
    #Class variable
    decal_orig_objects = []
    t_object_name = ""
    baked_images_running_total = 0
    
    def execute(self, context):


        sbp = context.scene.SimpleBake_Props

        #Renable autosmooth
        prefs = context.preferences.addons[base_package].preferences
        if prefs.disable_auto_smooth_for_split_normals and bpy.app.version < (4,1,0):
            global das_gen
            next(das_gen)

        self.in_background = True if "--background" in sys.argv or sbp.fake_background else False
        
        bake_objects_names = [o.obj_point.name for o in sbp.objects_list]
        
        #print_message(context, "Common bake finishing")
        

        #Working collection
        to_del = []
        for c in bpy.data.collections:
            if "SimpleBake_Working" in c.name: to_del.append(c.name)
        for name in to_del:
            c = bpy.data.collections.get(name)
            if c:
                bpy.data.collections.remove(c)

        #Render engine
        context.scene.render.engine = CommonBakePrepandFinish.orig_render_engine

        #Force to object mode
        if context.active_object == None:
            context.view_layer.objects.active = context.view_layer.objects[0] #Pick arbitary
        try: bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        except Exception as e: pass # Weird crash when SimpleBake is displayed in the n-panel

        #Object selection
        bpy.ops.object.select_all(action="DESELECT")
        for obj in CommonBakePrepandFinish.orig_object_selection:
            try: obj.select_set(True)
            except Exception as e: print(str(e)) #E.g. if user had a copy and apply object selected, and now it's gone
        try: context.view_layer.objects.active = CommonBakePrepandFinish.orig_active_object
        except: pass

        # #If we applied bakes to the original object, let's assume we want that UV map to end up active for render
        # #May be overriden by the next check for the restore option. The user is warned about this on the panel
        if sbp.new_uv_option and sbp.apply_bakes_to_original:
            objs = [o.obj_point for o in sbp.objects_list]
            if sbp.targetobj != None: objs = [sbp.targetobj]
            if sbp.targetobj_cycles != None: objs = [sbp.targetobj_cycles]

            for obj in objs:
                for uvm in obj.data.uv_layers:
                    if uvm.name == "SimpleBake":
                        uvm.active_render = True


        #If we didn't export the bakes, pack them into the Blend file for safe keeping
        if not sbp.save_bakes_external:
            #Don't forget decal images. This is only called by the "regular" bake at the end'
            decal_op_id = self.bake_operation_id.replace("DECALSBASE_", "")
            bis = [i.name for i in bpy.data.images if "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == self.bake_operation_id]
            decal_bis = [i.name for i in bpy.data.images if "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == decal_op_id]
            bis = list(set(bis + decal_bis))
            for iname in bis:
                if i:=bpy.data.images.get(iname):
                    i.pack()

        #Object orig_object_uvs
        #TODO: Is this actually wrong? Target object UVs will never be changed?
        if sbp.restore_orig_uv_map:
            uv_objs_names = bake_objects_names
            if sbp.targetobj != None: uv_objs_names.append(sbp.targetobj.name)
            if sbp.targetobj_cycles != None: uv_objs_names.append(sbp.targetobj_cycles.name)

            for o_name in uv_objs_names:
                obj = context.scene.objects[o_name]
                if o_name in CommonBakePrepandFinish.orig_object_uvs:
                    uv_name = CommonBakePrepandFinish.orig_object_uvs[o_name]
                    if uv_name in obj.data.uv_layers:
                        obj.data.uv_layers.active = obj.data.uv_layers[uv_name]
                if o_name in CommonBakePrepandFinish.orig_object_uvs_render:
                    uv_name = CommonBakePrepandFinish.orig_object_uvs_render[o_name]
                    if uv_name in obj.data.uv_layers:
                        obj.data.uv_layers[uv_name].active_render = True

        #Clear packed list
        #CommonBakePrepandFinish.packed_images.clear()

        #Remove SimpleBake_Bakes if it's empty
        c = bpy.data.collections.get("SimpleBake_Bakes")
        if c and len(c.objects) == 0:
            bpy.data.collections.remove(c)

        bpy.ops.simplebake.material_backup(mode=MatManager.MODE_MASTER_RESTORE)

        m = bpy.data.materials.get("SimpleBake_Placeholder")
        if m:
            bpy.data.materials.remove(m, do_unlink=True)

        #Report
        #Get all images with this bake ID
        bis = [i for i in bpy.data.images if "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == self.bake_operation_id]
        for bi in bis:
            if "SB_counted" not in bi or ("SB_counted" in bi and not bi["SB_counted"]):
                __class__.baked_images_running_total+=1
                bi["SB_counted"] = True
        if not self.in_background and not Bip.was_error and not self.decal_first_run and not self.suppress_report and not sbp.suppress_report\
            and not Bip.running_sequence or (Bip.running_sequence and Bip.running_sequence_last):
            #message=f"Foreground bake is complete|{str(self.baked_number)} images baked"
            message=f"Foreground bake is complete|{__class__.baked_images_running_total} images baked"
            if Bip.running_sequence and Bip.running_sequence_last:
                message = message + f" for {Bip.sequence_frames} frames"
                Bip.running_sequence_last = False
                Bip.running_sequence_first = False
                Bip.running_sequence = False

            icon="INFO"
            centre = True
            bpy.ops.simplebake.show_message_box('INVOKE_DEFAULT', message=message, icon=icon, centre=centre)
            __class__.baked_images_running_total = 0
            for bi in bis:
                bi["SB_counted"] = False
        

        #Always reset this -
        Bip.was_error = False
        #Can't be the first run anymore
        #Bip.running_sequence_first = False
        
        
        if self.in_background:
            bpy.ops.wm.save_mainfile()
            print_message(context, "Saving file")
        
        #If this was an S2A bake, also hide the bake objects (only target will be hidden by Copy and Apply)
        #NOTE: Target may also be in bake objects list
        #NOTE: Target object won't be hidden for first decals run, but that's what we want
        if not Bip.running_sequence or (Bip.running_sequence and Bip.running_sequence_last):
            if (sbp.selected_s2a or sbp.cycles_s2a) and sbp.hide_source_objects: #Some kind of S2A bake
                hide_obj_names = bake_objects_names
                if sbp.targetobj != None:
                    if sbp.targetobj.name in hide_obj_names:
                        hide_obj_names = [h for h in hide_obj_names if h != sbp.targetobj.name]

                if sbp.targetobj_cycles != None:
                    if sbp.targetobj_cycles.name in hide_obj_names:
                        hide_obj_names = [h for h in hide_obj_names if h != sbp.targetobj_cycles.name]

                for obj_name in hide_obj_names:
                    obj = context.scene.objects[obj_name]
                    obj.hide_set(True)

        ##If this was an S2A bake, also hide the cage object if user requested this
        if not Bip.running_sequence or (Bip.running_sequence and Bip.running_sequence_last):
            if (sbp.selected_s2a or sbp.cycles_s2a) and sbp.copy_and_apply and sbp.hide_cage_object:
                obj = context.scene.render.bake.cage_object
                if obj != None: #May not have a cage object actually set
                    obj.hide_set(True)

                
        #Do we want to keep the internal images after export?
        #Will not affect background bakes anyway, as we are being called after the file save
        del_list = []
        if sbp.save_bakes_external and not sbp.keep_internal_after_export:# and not self.in_background:
            print_message(context, "Deleting internal baked images")
            del_list = [i.name for i in bpy.data.images if "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == self.bake_operation_id]

            for name in del_list:
                i = bpy.data.images.get(name)
                if i!=None:
                    print_message(context, f"Deleting {i.name}")
                    bpy.data.images.remove(i)
        
        #Unhide for rendering any objects we hid for the isolation function and clear
        for o_name in SimpleBake_OT_Select_Only_This.hidden:
            context.scene.objects[o_name].hide_render = False
        SimpleBake_OT_Select_Only_This.hidden = []
        
        #Reload all baked images
        imgs = [i for i in bpy.data.images if ("SB_bake_operation_id" in i and 
                                               i["SB_bake_operation_id"] == self.bake_operation_id)]
        # for i in imgs:
        #     i.reload()

        #Unhide all objects in SimpleBake bakes
        if (c:=bpy.data.collections.get("SimpleBake_Bakes")):
            for o in c.objects:
                if "SB_bake_operation_id" in o and o["SB_bake_operation_id"] == self.bake_operation_id:
                    o.hide_render = False

        start_time = CommonBakePrepandFinish.start_time
        finish_time = datetime.now()
        s = (finish_time-start_time).seconds
        print_message(context, f"Time taken - {s} seconds ({floor(s/60)} minutes, {s%60} seconds)")

        Bip.is_baking = False

        blender_refresh()

        #Reverse any sidestepping of geo nodes objects
        bpy.ops.simplebake.reverse_geo_nodes_sidestep()


        return {'FINISHED'}
    




classes = ([
    SimpleBake_OT_Pack_Baked_Images,
    SimpleBake_OT_Scale_Images_If_Needed,
    SimpleBake_OT_Common_Bake_Prep,
    SimpleBake_OT_Common_Bake_Finishing,
    SimpleBake_OT_Select_Only_This,
    SimpleBake_OT_Compositor_Denoise,
    SimpleBake_OT_Select_Selected_To_Active,
    SimpleBake_OT_Set_Sample_Count
        ])

def register():
    
    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
    
