import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from pathlib import Path
import tempfile
import shutil
import os
import numpy as np
import sys

from .utils import SBConstants, get_bake_objects
from .messages import print_message
from .background_and_progress import BakeInProgress as Bip
from . import __package__ as base_package

FILE_EXTENSIONS = {"PNG": "png", "JPEG": "jpg", "TIFF": "tiff", "TARGA": "tga","TARGA_RAW": "tga", "OPEN_EXR": "exr"}


def load_image(image_path):
    # Load an image file as a numpy array
    try:
        image = bpy.data.images.load(image_path)
        pixels = np.array(image.pixels)
        width, height = image.size
        # Reshape and isolate the desired channel (r, g, b or a)
        channel_data = pixels.reshape((height, width, 4))
        return channel_data[:, :, :3], channel_data[:, :, 3], image  # RGB and Alpha
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None, None, image

def load_image_as_grayscale(image_path):
    # Load an image file and convert it to grayscale
    try:
        image = bpy.data.images.load(image_path)
        pixels = np.array(image.pixels)
        width, height = image.size
        # Reshape and convert to grayscale
        channel_data = pixels.reshape((height, width, 4))
        grayscale_data = np.mean(channel_data[:, :, :3], axis=2)  # Average of RGB
        return grayscale_data, channel_data[:, :, 3], image  # Grayscale and Alpha
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None, None, image

def channel_pack_images_isolate(red_image, green_image, blue_image, alpha_image, imgname):

    archetype_img_data = None
    to_remove = []

    # Load each image and extract its corresponding channel
    if red_image != None:
        r_data, r_alpha, r_loaded = load_image(red_image)
        packed_image = np.zeros(r_data.shape)
        archetype_img_data = r_data
        to_remove.append(r_loaded)

    if green_image != None:
        g_data, g_alpha, g_loaded = load_image(green_image)
        packed_image = np.zeros(g_data.shape)
        archetype_img_data = g_data
        to_remove.append(g_loaded)

    if blue_image != None:
        b_data, b_alpha, b_loaded = load_image(blue_image)
        packed_image = np.zeros(b_data.shape)
        archetype_img_data = b_data
        to_remove.append(b_loaded)

    if alpha_image != None:
        a_data, a_alpha, a_loaded = load_image(alpha_image)
        packed_image = np.zeros(a_data.shape)
        archetype_img_data = a_data
        to_remove.append(a_loaded)

    packed_image[:, :, 0] = r_data[:, :, 0] if red_image != None else np.zeros_like(archetype_img_data[:, :, 0])  # Red
    packed_image[:, :, 1] = g_data[:, :, 1] if green_image != None else np.zeros_like(archetype_img_data[:, :, 0]) # Green
    packed_image[:, :, 2] = b_data[:, :, 2] if blue_image != None else np.zeros_like(archetype_img_data[:, :, 0]) # Blue
    packed_alpha = a_data[:, :, 0] if alpha_image != None else np.zeros_like(archetype_img_data[:, :, 0])   # Alpha
    packed_pixels = np.concatenate((packed_image, packed_alpha[:, :, None]), axis=2)

    packed_pixels = packed_pixels.flatten()

    # Create a new image in Blender and assign the pixels
    bpy.data.images.remove(bpy.data.images[imgname]) if imgname in bpy.data.images else False
    output_image = bpy.data.images.new(name=imgname, width=archetype_img_data.shape[1], height=archetype_img_data.shape[0], alpha=True)
    output_image.pixels = packed_pixels

    for i in to_remove:
        bpy.data.images.remove(i)

    return output_image

def channel_pack_images_grayscale(red_image, green_image, blue_image, alpha_image, imgname):

    archetype_img_data = None
    to_remove = []

    if red_image != None:
        r_data, _, r_loaded = load_image_as_grayscale(red_image)
        archetype_img_data = r_data
        packed_image = np.zeros((r_loaded.size[1], r_loaded.size[0], 4))
        to_remove.append(r_loaded)

    if green_image != None:
        g_data, _, g_loaded = load_image_as_grayscale(green_image)
        archetype_img_data = g_data
        packed_image = np.zeros((g_loaded.size[1], g_loaded.size[0], 4))
        to_remove.append(g_loaded)

    if blue_image != None:
        b_data, _, b_loaded = load_image_as_grayscale(blue_image)
        archetype_img_data = b_data
        packed_image = np.zeros((b_loaded.size[1], b_loaded.size[0], 4))
        to_remove.append(b_loaded)

    if alpha_image != None:
        a_data, _, a_loaded = load_image_as_grayscale(alpha_image)
        archetype_img_data = a_data
        packed_image = np.zeros((a_loaded.size[1], a_loaded.size[0], 4))
        to_remove.append(a_loaded)

    if red_image != None: packed_image[:, :, 0] = r_data
    if green_image != None: packed_image[:, :, 1] = g_data
    if blue_image != None: packed_image[:, :, 2] = b_data
    if alpha_image != None: packed_image[:, :, 3] = a_data

    # Save the combined image
    packed_pixels = packed_image.flatten()

    # Create a new image in Blender and assign the pixels
    bpy.data.images.remove(bpy.data.images[imgname]) if imgname in bpy.data.images else False
    output_image = bpy.data.images.new(name=imgname, width=archetype_img_data.shape[1], height=archetype_img_data.shape[0], alpha=True)
    output_image.pixels = packed_pixels

    for i in to_remove:
        bpy.data.images.remove(i)

    return output_image
    

class SimpleBake_OT_Channel_Packing(Operator):
    """Perform channel packing"""
    bl_idname = "simplebake.channel_packing"
    bl_label = "Pack"
    
    bake_operation_id: StringProperty()
    pbrtarget_only: BoolProperty(default=False)
    in_background: BoolProperty(default=False)
    global_mode: StringProperty()
    target_obj_name_override: StringProperty(default="")
    
    def delete_components(self,context):
        sbp = context.scene.SimpleBake_Props
        #Delete externally saved CPT components if the user wants us to do that

        del_list = []
        for obj_name in self.objects:
            if not (obj:=context.scene.objects.get(obj_name)):
                continue
            for cpt in self.cp_list:
                r_img = self.find_images_merged(context, cpt.R) if self.merged_bake else self.find_images(context, cpt.R, obj.name)
                g_img = self.find_images_merged(context, cpt.G) if self.merged_bake else self.find_images(context, cpt.G, obj.name)
                b_img = self.find_images_merged(context, cpt.B) if self.merged_bake else self.find_images(context, cpt.B, obj.name)
                a_img = self.find_images_merged(context, cpt.A) if self.merged_bake else self.find_images(context, cpt.A, obj.name)

                if r_img != None and r_img.name in bpy.data.images:
                    print_message(context, f"Deleting {r_img.name} from local file system")
                    filepath = bpy.path.abspath(r_img.filepath)
                    if len(r_img.tiles)>1:
                        for t in r_img.tiles:
                            thispath = filepath.replace("<UDIM>", str(t.number))
                            os.remove(thispath) if os.path.isfile(thispath) else False
                    else:
                        os.remove(filepath) if os.path.isfile(filepath) else False
                    del_list.append(r_img.name)

                if g_img != None and g_img.name in bpy.data.images:
                    print_message(context, f"Deleting {g_img.name} from local file system")
                    filepath = bpy.path.abspath(g_img.filepath)
                    if len(g_img.tiles)>1:
                        for t in g_img.tiles:
                            thispath = filepath.replace("<UDIM>", str(t.number))
                            os.remove(thispath) if os.path.isfile(thispath) else False
                    else:
                        os.remove(filepath) if os.path.isfile(filepath) else False
                    del_list.append(g_img.name)

                if b_img != None and b_img.name in bpy.data.images:
                    print_message(context, f"Deleting {b_img.name} from local file system")
                    filepath = bpy.path.abspath(b_img.filepath)
                    if len(b_img.tiles)>1:
                        for t in b_img.tiles:
                            thispath = filepath.replace("<UDIM>", str(t.number))
                            os.remove(thispath) if os.path.isfile(thispath) else False
                    else:
                        os.remove(filepath) if os.path.isfile(filepath) else False
                    del_list.append(b_img.name)

                if a_img != None and a_img.name in bpy.data.images:
                    print_message(context, f"Deleting {a_img.name} from local file system")
                    filepath = bpy.path.abspath(a_img.filepath)
                    if len(a_img.tiles)>1:
                        for t in a_img.tiles:
                            thispath = filepath.replace("<UDIM>", str(t.number))
                            os.remove(thispath) if os.path.isfile(thispath) else False
                    else:
                        os.remove(filepath) if os.path.isfile(filepath) else False
                    del_list.append(a_img.name)


        for iname in del_list:
            if iname in bpy.data.images:
                bpy.data.images.remove(bpy.data.images[iname])



    def find_images(self, context, selection, objname):

        if selection == "none":
            return None
        else:
            img = ([i for i in bpy.data.images if 
                        "SB_this_bake" in i and i["SB_this_bake"] == selection and
                        "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == self.bake_operation_id and
                        "SB_bake_object" in i and i["SB_bake_object"] == objname])
            assert(len(img)==1), f"Found {len(img)} images, should have been 1"
            img = img[0]
            return img
    
    def find_images_merged(self, context, selection):
        if selection == "none":
            return None
        else:
            img = ([i for i in bpy.data.images if 
                        "SB_this_bake" in i and i["SB_this_bake"] == selection and
                        "SB_bake_operation_id" in i and i["SB_bake_operation_id"] == self.bake_operation_id])
            assert(len(img)==1), f"Found {len(img)} images, should have been 1"
            img = img[0]
            return img
    
    def execute(self, context):
        sbp = context.scene.SimpleBake_Props

        #Grab what we need from panel
        self.merged_bake = sbp.merged_bake
        self.merged_bake_name = sbp.merged_bake_name
        self.export_folder_per_object = sbp.export_folder_per_object
        self.batch_name = sbp.batch_name
        self.in_background = True if "--background" in sys.argv or sbp.fake_background else False

        to_del = []
        for cp in sbp.cp_list:
            if cp["R"]=="none" and cp["G"]=="none" and cp["B"]=="none" and cp["A"]=="none":
                to_del.append(cp.name)
        for d in to_del:
            if (i:=sbp.cp_list.find(d))!=-1:
                sbp.cp_list.remove(i)

        self.cp_list = sbp.cp_list

        #Just in case
        if len(self.cp_list) == 0:
            print_message(context, "No channel packing")
            return {'FINISHED'}


        self.objects = get_bake_objects(context)

        
        #Figure out the save folder for each object
        efpo = self.export_folder_per_object
        mb = self.merged_bake
        mbn = self.merged_bake_name
        obj_savefolders = {}
        
        if self.in_background:
            p = sbp.export_path.replace("//", "")
            base_save_folder = Path(sbp.base_folder_override) / p
        else:
            base_save_folder = Path(bpy.path.abspath(sbp.export_path))
        
        
        for obj_name in self.objects:
            if not (obj:=context.scene.objects.get(obj_name)):
                continue

            if efpo and mb:
                savefolder = base_save_folder / mbn
                obj_savefolders[obj.name] = savefolder #Every object gets the same based on merged bake name
            elif efpo:
                savefolder = base_save_folder / obj.name
                obj_savefolders[obj.name] = savefolder
            else:
                savefolder = base_save_folder
                obj_savefolders[obj.name] = savefolder
        
        #Create each of the CPTs
        for obj_name in self.objects:
            if not (obj:=context.scene.objects.get(obj_name)):
                continue
            #Hacky
            if not mb: t_name = obj.name
            else: t_name = mbn 
            
            
            for cpt in self.cp_list:
                file_format = cpt.file_format
                cpt_name = cpt.name
                extension = FILE_EXTENSIONS[file_format]
                
                print_message(context, f"Creating packed texture \"{cpt_name}\" for object \"{t_name}\" with format {file_format}")
                
                r_img = self.find_images_merged(context, cpt.R) if self.merged_bake else self.find_images(context, cpt.R, obj.name)
                g_img = self.find_images_merged(context, cpt.G) if self.merged_bake else self.find_images(context, cpt.G, obj.name)
                b_img = self.find_images_merged(context, cpt.B) if self.merged_bake else self.find_images(context, cpt.B, obj.name)
                a_img = self.find_images_merged(context, cpt.A) if self.merged_bake else self.find_images(context, cpt.A, obj.name)
                
                #--Create the texture--
                prefs = context.preferences.addons[base_package].preferences

                #Determine the name
                proposed_name = prefs.img_name_format
                if Bip.running_sequence == True:
                    if "%FRAME%" not in proposed_name:
                        proposed_name = f"{proposed_name}.%FRAME%"
                        proposed_name = proposed_name.replace("%FRAME%", f"{context.scene.frame_current:04d}")
                    else:
                        proposed_name = proposed_name.replace(".%FRAME%", "")
                        proposed_name = proposed_name.replace("%FRAME%", "")
                proposed_name = proposed_name.replace("%OBJ%", t_name)
                proposed_name = proposed_name.replace("%BAKEMODE%", self.global_mode)
                proposed_name = proposed_name.replace("%BAKETYPE%", cpt.name)
                proposed_name = proposed_name.replace("%BATCH%", self.batch_name)
                res = f"{sbp.outputwidth}x{sbp.outputheight}"
                proposed_name = proposed_name.replace("%RESOLUTION%", res)
                imgname = proposed_name


                #Isolate or not
                if cpt.R == SBConstants.PBR_DIFFUSE and cpt.G == SBConstants.PBR_DIFFUSE and cpt.B == SBConstants.PBR_DIFFUSE:
                    mode = "ISOLATE"
                elif cpt.R == SBConstants.PBR_SSSCOL and cpt.G == SBConstants.PBR_SSSCOL and cpt.B == SBConstants.PBR_SSSCOL:
                    mode = "ISOLATE"
                elif cpt.R == SBConstants.PBR_EMISSION and cpt.G == SBConstants.PBR_EMISSION and cpt.B == SBConstants.PBR_EMISSION:
                    mode = "ISOLATE"
                else:
                    mode = "GREYSCALE"

                #Let's go
                def save_external(img, cpt, output_path, file_format):
                    #Save the image
                    output_image.file_format = file_format
                    output_image.filepath_raw = output_path
                    output_image.alpha_mode = 'CHANNEL_PACKED'

                    s = bpy.data.scenes.new("SB_CP_Export_Temp")
                    s.render.image_settings.file_format = file_format
                    s.view_settings.view_transform = "Standard" #default

                    s.render.image_settings.color_mode = "RGBA"
                    if file_format == "OPEN_EXR":
                        s.render.image_settings.exr_codec = cpt.exr_codec
                        s.render.image_settings.color_depth = "32"
                    if file_format == "PNG":
                        s.render.image_settings.exr_codec = cpt.exr_codec
                        s.render.image_settings.color_depth = "16" if sbp.everything_16bit else "8"
                        if "png_compression" in cpt:
                            s.render.image_settings.compression = cpt.png_compression
                        else:
                            s.render.image_settings.compression = 15

                    if file_format == "TARGA":
                        pass

                    img.save_render(str(output_path), scene=s)
                    img.source = "FILE"
                    bpy.data.scenes.remove(s)


                #Will we be working with tiled images or not
                #If one is tiled, they all wil be. However, they could also be None
                tiled = False
                tiles = []
                if r_img != None and len(r_img.tiles)>1:
                    tiled = True
                    tiles = r_img.tiles
                if g_img != None and len(g_img.tiles)>1:
                    tiled = True
                    tiles = g_img.tiles
                if b_img != None and len(b_img.tiles)>1:
                    tiled = True
                    tiles = b_img.tiles
                if a_img != None and len(a_img.tiles)>1:
                    tiled = True
                    tiles = a_img.tiles

                #UDIM image
                if tiled:
                    for t in tiles:
                        this_i_name = imgname + f".{str(t.number)}"
                        r_path = r_img.filepath.replace("<UDIM>", str(t.number)) if r_img!=None else None
                        g_path = g_img.filepath.replace("<UDIM>", str(t.number)) if g_img!=None else None
                        b_path = b_img.filepath.replace("<UDIM>", str(t.number)) if b_img!=None else None
                        a_path = a_img.filepath.replace("<UDIM>", str(t.number)) if a_img!=None else None

                        if mode == "ISOLATE":
                            output_image = channel_pack_images_isolate(r_path, g_path, b_path, a_path,\
                                this_i_name)
                        else:
                            output_image = channel_pack_images_grayscale(r_path, g_path, b_path, a_path,\
                                this_i_name)


                        output_path = Path(obj_savefolders[obj.name] / (this_i_name + f".{extension}"))
                        save_external(output_image, cpt, str(output_path), file_format)

                #Non-UDIM image
                else:
                    r_path = r_img.filepath if r_img!=None else None
                    g_path = g_img.filepath if g_img!=None else None
                    b_path = b_img.filepath if b_img!=None else None
                    a_path = a_img.filepath if a_img!=None else None

                    if mode == "ISOLATE":
                        output_image = channel_pack_images_isolate(r_path, g_path, b_path, a_path,\
                            imgname)
                    else:
                        output_image = channel_pack_images_grayscale(r_path, g_path, b_path, a_path,\
                            imgname)

                    output_path = Path(obj_savefolders[obj.name] / (imgname + f".{extension}"))
                    save_external(output_image, cpt, str(output_path), file_format)

                output_image["SB_bake_operation_id"] = self.bake_operation_id

                #------------------------------------------------------

            #Hacky - If this is a mergedbake, break out of the object loop
            if sbp.merged_bake:
                break
            
        if sbp.del_cptex_components:
            self.delete_components(context)

        return {'FINISHED'}

    

classes = ([
    SimpleBake_OT_Channel_Packing
        ])

def register():
    
    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
