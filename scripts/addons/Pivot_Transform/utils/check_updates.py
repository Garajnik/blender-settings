import bpy
from bpy.types import Operator



def update_version():
    import urllib, re, addon_utils

    page = urllib.request.urlopen( 'https://github.com/ilumetric/Poly_Source/blob/main/Versions' ).read()
    txt = str(page)

    version_site = re.search(r'PT\b......', txt)
    version = version_site[0][3:]

    addon_version = [addon.bl_info.get('version', (-1,-1,-1)) for addon in addon_utils.modules() if addon.bl_info['name'] == 'Pivot Transform'][0]
    current_version = str(addon_version[0]) + '.' + str(addon_version[1]) + '.' + str(addon_version[2])
    print('Pivot Transform: Current Version ' + current_version)
    if version <= current_version:
        return False, version
    else:
        return True, version



class PT_OT_check_updates(Operator):
    bl_idname = "pt.check_updates"
    bl_label = "Check For Updates"
    bl_description = "Check If There Is An Update For The Addon"

    def execute(self, context):
        props = bpy.context.preferences.addons['Pivot_Transform'].preferences
        try:
            check, version = update_version()
            
            if check:
                props.update = True
                props.version = version
            else:
                props.update = False
        except:
            props.update = False
        return {'FINISHED'}



classes = [
    PT_OT_check_updates,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)