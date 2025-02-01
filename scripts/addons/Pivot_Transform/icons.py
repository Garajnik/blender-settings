import os
import bpy
from bpy.utils import previews #Thanks Andrew Doll ;)


icons_collections = {}


def register():
    global icons_collections

    icoll = previews.new()

# --- General
    my_icons_dir = os.path.join(os.path.dirname(__file__), './icons/prefs')
    icoll.load('market', os.path.join(my_icons_dir, 'market.png'), 'IMAGE')
    icoll.load('gumroad', os.path.join(my_icons_dir, 'gumroad.png'), 'IMAGE')
    icoll.load('artstation', os.path.join(my_icons_dir, 'artstation.png'), 'IMAGE')
    icoll.load('discord', os.path.join(my_icons_dir, 'discord.png'), 'IMAGE')
    icoll.load('blenderboi', os.path.join(my_icons_dir, 'blenderboi.png'), 'IMAGE')
    icoll.load('update', os.path.join(my_icons_dir, 'update.png'), 'IMAGE')
    icoll.load('settings', os.path.join(my_icons_dir, 'settings.png'), 'IMAGE')
    icoll.load('pt', os.path.join(my_icons_dir, 'anchor.png'), 'IMAGE')

    #my_icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
    #icoll.load('gg_icon', os.path.join(my_icons_dir, 'gg.png'), 'IMAGE')
    


# --- Pivot General
    my_icons_dir = os.path.join(os.path.dirname(__file__), './icons/pivot')
    #icoll.load('pt', os.path.join(my_icons_dir, 'PT.png'), 'IMAGE')
    icoll.load('bbox', os.path.join(my_icons_dir, 'bbox.png'), 'IMAGE')
    icoll.load('flow', os.path.join(my_icons_dir, 'flow.png'), 'IMAGE')
    icoll.load('drop', os.path.join(my_icons_dir, 'drop.png'), 'IMAGE')
    icoll.load('apply', os.path.join(my_icons_dir, 'apply.png'), 'IMAGE')
    icoll.load('run', os.path.join(my_icons_dir, 'run.png'), 'IMAGE')
    icoll.load('normals', os.path.join(my_icons_dir, 'normals.png'), 'IMAGE')
    icoll.load('fix', os.path.join(my_icons_dir, 'fix.png'), 'IMAGE')
    icoll.load('select', os.path.join(my_icons_dir, 'select.png'), 'IMAGE')
    icoll.load('cursor', os.path.join(my_icons_dir, 'cursor.png'), 'IMAGE')
    icoll.load('tg_on', os.path.join(my_icons_dir, 'toggle_on.png'), 'IMAGE')
    icoll.load('tg_off', os.path.join(my_icons_dir, 'toggle_off.png'), 'IMAGE')
    icoll.load('to_bottom', os.path.join(my_icons_dir, 'to_bottom.png'), 'IMAGE')
    icoll.load('mesh_to_pivot', os.path.join(my_icons_dir, 'mesh_to_pivot.png'), 'IMAGE')
    icoll.load('to_pivot', os.path.join(my_icons_dir, 'to_pivot.png'), 'IMAGE')
    icoll.load('geom', os.path.join(my_icons_dir, 'geom.png'), 'IMAGE')
    icoll.load('pt_save', os.path.join(my_icons_dir, 'pt_save.png'), 'IMAGE')


# --- Pivot Apply
    my_icons_dir = os.path.join(os.path.dirname(__file__), './icons/pivot_apply')
    icoll.load('pa_location', os.path.join(my_icons_dir, 'pa_location.png'), 'IMAGE')
    icoll.load('pa_rotation', os.path.join(my_icons_dir, 'pa_rotation.png'), 'IMAGE')
    icoll.load('pa_scale', os.path.join(my_icons_dir, 'pa_scale.png'), 'IMAGE')
    icoll.load('pa_rotation_scale', os.path.join(my_icons_dir, 'pa_rotation_scale.png'), 'IMAGE')
    icoll.load('pa_xf', os.path.join(my_icons_dir, 'pa_xf.png'), 'IMAGE')


# --- Pivot Save
    my_icons_dir = os.path.join(os.path.dirname(__file__), './icons/pivot_save')
    icoll.load('ps_add', os.path.join(my_icons_dir, 'ps_add.png'), 'IMAGE')
    icoll.load('ps_remove', os.path.join(my_icons_dir, 'ps_remove.png'), 'IMAGE')
    icoll.load('ps_global', os.path.join(my_icons_dir, 'ps_global.png'), 'IMAGE')
    icoll.load('ps_up', os.path.join(my_icons_dir, 'ps_up.png'), 'IMAGE')
    icoll.load('ps_down', os.path.join(my_icons_dir, 'ps_down.png'), 'IMAGE')
    icoll.load('ps_location', os.path.join(my_icons_dir, 'ps_location.png'), 'IMAGE')
    icoll.load('ps_rotation', os.path.join(my_icons_dir, 'ps_rotation.png'), 'IMAGE')
    icoll.load('ps_save', os.path.join(my_icons_dir, 'ps_save.png'), 'IMAGE')


# --- 3D Cursor
# --- Cursor Save
    my_icons_dir = os.path.join(os.path.dirname(__file__), './icons/cursor_save')
    icoll.load('cur_add', os.path.join(my_icons_dir, 'cur_add.png'), 'IMAGE')
    icoll.load('cur_remove', os.path.join(my_icons_dir, 'cur_remove.png'), 'IMAGE')
    icoll.load('cur_up', os.path.join(my_icons_dir, 'cur_up.png'), 'IMAGE')
    icoll.load('cur_down', os.path.join(my_icons_dir, 'cur_down.png'), 'IMAGE')
    icoll.load('cur_location', os.path.join(my_icons_dir, 'cur_location.png'), 'IMAGE')
    icoll.load('cur_rotation', os.path.join(my_icons_dir, 'cur_rotation.png'), 'IMAGE')
    icoll.load('cur_save', os.path.join(my_icons_dir, 'cur_save.png'), 'IMAGE')


    my_icons_dir = os.path.join(os.path.dirname(__file__), './icons/cursor')
    icoll.load('3d_cursor', os.path.join(my_icons_dir, '3d_cursor.png'), 'IMAGE')
    
    

    icoll.load('gg_cursor', os.path.join(my_icons_dir, 'gg.png'), 'IMAGE')
    icoll.load('loc_cursor', os.path.join(my_icons_dir, 'loc.png'), 'IMAGE')
    icoll.load('rot_cursor', os.path.join(my_icons_dir, 'rot.png'), 'IMAGE')
    icoll.load('to_sel_cursor', os.path.join(my_icons_dir, 'to_sel.png'), 'IMAGE')
    icoll.load('view_cursor', os.path.join(my_icons_dir, 'view.png'), 'IMAGE')
    icons_collections[ 'main' ] = icoll
    

    


def unregister():
    global icons_collections
    for icoll in icons_collections.values():
        bpy.utils.previews.remove(icoll)
    icons_collections.clear()