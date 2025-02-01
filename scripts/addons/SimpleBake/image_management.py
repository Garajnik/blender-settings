import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from bpy.props import BoolProperty, StringProperty, IntProperty

import uuid
import numpy as np

from .utils import SBConstants, get_udim_tiles, get_bake_objects
from .messages import print_message
from .background_and_progress import BakeInProgress as Bip
from . import __package__ as base_package

def gen_image_name(context, name, globalmode, baketype):
    sbp = context.scene.SimpleBake_Props
    prefs = context.preferences.addons[base_package].preferences
    proposed_name = prefs.img_name_format

    if Bip.running_sequence == True:
        if "%FRAME%" not in proposed_name:
            proposed_name = f"{proposed_name}.%FRAME%"
        proposed_name = proposed_name.replace("%FRAME%", f"{context.scene.frame_current:04d}")
    else:
        proposed_name = proposed_name.replace(".%FRAME%", "")
        proposed_name = proposed_name.replace("%FRAME%", "")

    proposed_name = proposed_name.replace("%OBJ%", name)
    proposed_name = proposed_name.replace("%BAKEMODE%", globalmode)
    proposed_name = proposed_name.replace("%BAKETYPE%", baketype)
    proposed_name = proposed_name.replace("%BATCH%", sbp.batch_name)
    res = f"{sbp.outputwidth}x{sbp.outputheight}"
    if prefs.abbr_res and sbp.outputwidth % 1024 == 0 and sbp.outputheight % 1024 == 0:
        res = f"{int(sbp.outputwidth / 1024)}K"


    proposed_name = proposed_name.replace("%RESOLUTION%", res)

    return proposed_name


class SimpleBake_OT_Bake_Image(Operator):
    """Generate image to be baked to if needed"""
    bl_idname = "simplebake.bake_image"
    bl_description = "Generates image to be baked to if needed"
    bl_label = "GenImage"
    
    need_first_time_settings = []


    bake_operation_id: StringProperty()
    this_bake: StringProperty()
    target_object_name: StringProperty()
    global_mode: StringProperty()
    bake_mode: StringProperty()


    
    def create_individual_bake_image(self, context):
        sbp = context.scene.SimpleBake_Props
        print_message(context, "Getting individual baked image")
        
        prefs = context.preferences.addons[base_package].preferences

        alias_dict = prefs.get_alias_dict()
        if self.this_bake in alias_dict: this_bake = alias_dict[self.this_bake]
        else: this_bake = self.this_bake

        proposed_name = gen_image_name(context, self.target_object_name, self.global_mode, this_bake)

        need_new = False
        if proposed_name in bpy.data.images and not self.clear_image:
            #It's there, and we aren't going to clear it

            #No action for now
            i = bpy.data.images[proposed_name]
            self.created_images.append(i)
            self.set_image_tags(i)
            need_new = False

        elif proposed_name in bpy.data.images:
            #It's there, but we want to clear it
            bpy.data.images.remove(bpy.data.images[proposed_name])
            need_new = True

        else:
            #It's not there
            need_new = True
        
        if need_new:
            #Actually Create the image
            tiled = True if (self.total_tiles > 1 and sbp.auto_detect_udims) else False
            i = bpy.data.images.new(proposed_name, self.img_width, self.img_height, alpha=self.use_alpha, float_buffer=self.float_buffer, tiled=tiled)

            #Create all the tiles
            if tiled:
                for t in self.active_tiles:
                    i.tiles.new(t)

            self.created_images.append(i)
            self.set_image_tags(i)
            self.need_first_time_settings.append(i)
        else:
            #self.need_first_time_settings = False
            pass
        
    
    def create_merged_bake_image(self, context):
        sbp = context.scene.SimpleBake_Props
        print_message(context, "Getting merged bake image")
        
        prefs = context.preferences.addons[base_package].preferences

        alias_dict = prefs.get_alias_dict()
        if self.this_bake in alias_dict: this_bake = alias_dict[self.this_bake]
        else: this_bake = self.this_bake

        proposed_name = gen_image_name(context, self.merged_bake_name, self.global_mode, this_bake)

        need_new = False
        
        if proposed_name not in bpy.data.images:
            need_new = True
        else:
            i = bpy.data.images[proposed_name]
            if "SB_bake_operation_id" in i and i["SB_bake_operation_id"] != self.bake_operation_id:
                #It's there, but different bake ID
                if self.clear_image:
                    bpy.data.images.remove(i)
                    need_new = True
                else:
                    #Essentially do nothing
                    pass

            elif "SB_bake_operation_id" not in i:
                 #It's there, but it doesn't even have an ID. This will be a weird coincidence
                if self.clear_image:
                    bpy.data.images.remove(i)
                    need_new = True
                else:
                    #Essentially do nothing
                    pass

            elif "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == self.bake_operation_id:
                #It's there, and it's our bake
                need_new = False
                
        if need_new:
            tiled = True if (self.total_tiles > 1 and sbp.auto_detect_udims) else False
            i = bpy.data.images.new(proposed_name, self.img_width, self.img_height, alpha=self.use_alpha, float_buffer=self.float_buffer, tiled=tiled)

            #Create all the tiles
            if tiled:
                for t in self.active_tiles:
                    i.tiles.new(t)

            self.created_images.append(i)
            self.set_image_tags(i)
            self.need_first_time_settings.append(i)

        else:
            #Just using existing image, pretend we created it
            #i is created up on line 113
            self.created_images.append(i)
            self.set_image_tags(i)


    
    def set_image_tags(self, i):
        i["SB_bake_object"] = self.target_object_name
        i["SB_global_mode"] = self.global_mode
        i["SB_this_bake"] = self.this_bake
        i["SB_merged_bake"] = self.merged_bake
        i["SB_merged_bake_name"] = self.merged_bake_name
        i["SB_bake_operation_id"] = self.bake_operation_id
        i["SB_float_buffer"] = self.float_buffer
        i["SB_scaled"] = False
        i["SB_exported_list"] = []
        i["SB_denoised"] = False
    

    def set_image_settings(self, context, imgs):

        sbp = context.scene.SimpleBake_Props

        for i in imgs:
            print_message(context, f"Adjusting settings on new image {i.name}")

            if self.this_bake == SBConstants.PBR_NORMAL:
                gc = (0.5,0.5,1.0,1.0) #Normal ignores the use alpha option
            elif self.this_bake == "NORMAL": #CyclesBake normal
                gc = (0.5,0.5,1.0,1.0) #Normal ignores the use alpha option
            elif self.use_alpha:
                gc = (0.0,0.0,0.0,0.0)
            else:
                gc = (0.0,0.0,0.0,1.0)

            i.generated_color = gc
            #If this is a tiled image, let's go for all the tiles too
            if len(i.tiles) > 1: #Even an untiled image has tile length of 1
                area = context.screen.areas[0]

                old_type = area.type
                area.type = "IMAGE_EDITOR"
                area.spaces[0].image = i
                with context.temp_override(area=area):
                    for t in i.tiles:
                        index = t.number-1000
                        i.tiles.active_index = index
                        bpy.ops.image.tile_fill(\
                            color=gc, width=self.img_width, height=self.img_height, float=self.float_buffer, alpha=self.use_alpha)

                area.type = old_type


            prefs = context.preferences.addons[base_package].preferences
            cs_dict = prefs.get_cs_dict()
            
            if self.this_bake in cs_dict:
                cs = cs_dict[self.this_bake]
            elif self.global_mode in [SBConstants.CYCLESBAKE,SBConstants.CYCLESBAKE_S2A] and context.scene.cycles.bake_type != "NORMAL":
                cs = sbp.cyclesbake_cs
            else:
                cs = "Non-Color"

            i.colorspace_settings.name = cs
            print_message(context, f"Image colour space set to {cs}")

            i.use_fake_user = True

    
    def execute(self, context):


        sbp = context.scene.SimpleBake_Props
        self.merged_bake = sbp.merged_bake

        if not self.merged_bake:
            #Nice and simple
            r = get_udim_tiles(context, self.target_object_name)
            self.total_tiles = r["total_tiles"]
            self.active_tiles = r["active_tiles"]
            print_message(context, f"Object {self.target_object_name} has maximum UDIM tile {self.total_tiles}")
            print_message(context, f"Object {self.target_object_name} has active UDIM tiles {self.active_tiles}")
        else:
            #Way more complicated
            self.active_tiles = set()
            self.total_tiles = 0
            objects = get_bake_objects(context)
            for o_name in objects:
                if not (o:=context.scene.objects.get(o_name)):
                    continue
                r = get_udim_tiles(context, o.name)
                these_active_tiles = r["active_tiles"]
                self.active_tiles.update(these_active_tiles)

                this_total_tiles = r["total_tiles"]
                self.total_tiles = this_total_tiles if this_total_tiles > self.total_tiles else self.total_tiles
            self.active_tiles = list(self.active_tiles)

            print_message(context, f"Merged bake with maximum UDIM tile {self.total_tiles}")
            print_message(context, f"Merged bake with active UDIM tiles {self.active_tiles}")



        #Grab what we need from the panel
        self.merged_bake_name = sbp.merged_bake_name
        self.use_alpha = sbp.use_alpha
        self.img_height = sbp.imgheight
        self.img_width = sbp.imgwidth
        self.clear_image = sbp.clear_image
        self.float_buffer = True if (self.bake_mode == SBConstants.PBR_NORMAL and not sbp.no_force_32bit_normals) or sbp.everything32bitfloat else False

        self.need_first_time_settings = []
        self.created_images = []


        if self.merged_bake:
            self.create_merged_bake_image(context)
        else:
            self.create_individual_bake_image(context)
            
            
        #We had to create a new image
        if self.created_images != []:
            #Set image settings for images that are freshly created
            self.set_image_settings(context, self.need_first_time_settings)
        
        else:
            print_message(context, "Using existing image")
        
        return {'FINISHED'}
    


classes = ([
        SimpleBake_OT_Bake_Image
        ])

def register():
    
    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
