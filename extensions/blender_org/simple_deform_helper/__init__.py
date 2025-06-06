from . import (
    ops,
    ui,
    gizmo,
    props,
    update,
    msgbus,
    translate,
    preferences,
)

bl_info = {
    "name": "Simple Deform Helper",
    "author": "AIGODLIKE Community:小萌新",
    "version": (0, 2, 4),
    "blender": (4, 0, 0),
    "location": "3D View -> Select an object and the active modifier is "
                "simple deformation",
    "description": "Simple Deform visualization adjustment tool",
    "doc_url": "https://gitee.com/AIGODLIKE/simple_deform_helper/wikis",
    "category": "AIGODLIKE"
}

"""
TODO 文本的修改器支侍，暂时未找到解决方法获取原始加界框
Text modifier support , have not yet found a solution to get the original bounding box

# -------------------------
__init__.py:
    Register All Module
    
gizmo/__init__.py:
    Register All Gizmo
    
    /angle_and_factor.py:
        Ctrl Modifier Angle
        
    /bend_axis.py:
        Bend Method Switch Direction Gizmo
        
    /set_deform_axis.py:
        Three Switch Deform Axis Operator Gizmo
    
    /up_down_limits_point.py:
        Main control part
        use utils.py PublicProperty._get_limits_point_and_bound_box_co 
            Obtain and calculate boundary box and limit point data


draw.py:
    Draw 3D Bound And Line

gizmo.json:
    Draw Custom Shape Vertex Data

operator.py:
    Set Deform Axis Operator

panel.py:
    Draw Gizmo Tool Property in Options and Tool Settings Right
    
preferences.py:
    Addon Preferences

translate.py:
    temporary only Cn translate
    
update.py:
    In Change Depsgraph When Update Addon Data And Del Redundant Empty

utils.py:
    Main documents used
    Most computing operations are placed in classes GizmoUtils
# -------------------------
"""
module_tuple = (
    ops,
    ui,
    gizmo,
    props,
    update,
    msgbus,
    translate,
    preferences,
)


def register():
    for item in module_tuple:
        item.register()


def unregister():
    for item in module_tuple:
        item.unregister()
