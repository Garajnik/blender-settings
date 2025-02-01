import bpy
import math

def set_texture_properties(texture, properties):
    if 'contrast' in properties and hasattr(texture, 'contrast'):
        texture.contrast = properties['contrast']
    if 'intensity' in properties and hasattr(texture, 'intensity'):
        texture.intensity = properties['intensity']
    if 'turbulence' in properties and hasattr(texture, 'turbulence'):
        texture.turbulence = properties['turbulence']
    if 'use_clamp' in properties and hasattr(texture, 'use_clamp'):
        texture.use_clamp = properties['use_clamp']
    if 'noise_basis' in properties and hasattr(texture, 'noise_basis'):
        texture.noise_basis = properties['noise_basis']


def set_OCD_texture_properties(ocd_tex, tex_type, has_noise_basis):
    ocd_tex.type = tex_type
    if tex_type == 'MUSGRAVE':
        ocd_tex.contrast = 1
        ocd_tex.intensity = 1
        ocd_tex.use_clamp = True
        if hasattr(ocd_tex, 'noise_basis'):
            ocd_tex.noise_basis = 'VORONOI_CRACKLE'
    elif tex_type == 'CLOUDS':
        ocd_tex.contrast = 1.5
        ocd_tex.intensity = 1
        ocd_tex.use_clamp = True
        if hasattr(ocd_tex, 'noise_basis'):
            ocd_tex.noise_basis = 'VORONOI_CRACKLE'
    elif tex_type == 'MARBLE':
        ocd_tex.contrast = 1.5
        ocd_tex.intensity = 1.5
        ocd_tex.use_clamp = True
        if hasattr(ocd_tex, 'turbulence'):
            ocd_tex.turbulence = 5
        if hasattr(ocd_tex, 'noise_basis'):
            ocd_tex.noise_basis = 'IMPROVED_PERLIN'
    elif tex_type == 'VORONOI':
        ocd_tex.contrast = 0.5
        ocd_tex.intensity = 1.4
        ocd_tex.use_clamp = True
        if has_noise_basis and hasattr(ocd_tex, 'noise_basis'):
            ocd_tex.noise_basis = 'VORONOI_CRACKLE'
    elif tex_type == 'WOOD':
        ocd_tex.contrast = 1.5
        ocd_tex.intensity = 2
        ocd_tex.use_clamp = True
        if hasattr(ocd_tex, 'turbulence'):
            ocd_tex.turbulence = 15
        if hasattr(ocd_tex, 'noise_basis'):
            ocd_tex.noise_basis = 'IMPROVED_PERLIN'
    return ocd_tex