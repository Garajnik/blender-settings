import bpy
from bpy.props import *
from . icons import icons
from . ui.addon_checker import draw_addon_diagnostics
from . utils.addons import addon_exists
from . utils.blender_ui import get_dpi_factor
from . utility import addon
from . utility import modifier
from . import bl_info


class HOPS_OT_LearningPopup(bpy.types.Operator):
    """
    Learn more about Hard Ops / Boxcutter and how to use them.

    """
    bl_idname = "hops.learning_popup"
    bl_label = "Learning Popup Helper"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.system.dpi

        return context.window_manager.invoke_props_dialog(self, width=int(200 * get_dpi_factor(force=False)))

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        row = col.row()
        box = col.box()

        for name, url in weblinks:
            col.operator("wm.url_open", text=name).url = url

weblinks = [
    (f'''{bl_info['version'][0]}.{bl_info['version'][1]}{bl_info['version'][2]} Release Log''',   "https://masterxeon1001.com/2021/01/10/hard-ops-987-francium-release/"),
    ("H9 Learning Playlist",         "https://www.youtube.com/playlist?list=PLjqpj14voWsXlLHjT8jMnn5uKLfXKFki8"),
    ("Glebs Lighting Course",      "https://gumroad.com/a/14423155/tpodw"),
    ("Blender Bros",                "https://gumroad.com/a/739308659"),
    ("Josh's Youtube",        "https://www.youtube.com/playlist?list=PLLnvxH5YKLoKWtvIJT2-SdOql2QpewslQ"),
    ("Ryuu's Youtube",        "https://www.youtube.com/playlist?list=PLJrcFnBj2iIgOelGfcdz5ZKof-D4LSphA"),
    ("StellarWorks",                "https://www.youtube.com/channel/UCK4RSljZQXfpwBrAUxwwxjw"),
    ("Rachel's Helmet Tutorial",  "https://gum.co/scifihelmet"),
    ("Hard Ops Manual",         "http://hardops-manual.readthedocs.io/en/latest/"),
    ("Hard Ops Documentation",  "http://hardops-manual.readthedocs.io/en/latest/"),
    ("HOPS / BC Playlist",        "https://www.youtube.com/playlist?list=PL0RqAjByAphEUuI2JDxIjjCQtfTRQlRh0"),
    ("HOPScutter Playlist",      "https://www.youtube.com/playlist?list=PL0RqAjByAphHoCDKWy6OU4BwB7hTi8lo_"),
    ("Classic Video Playlist", "https://www.youtube.com/playlist?list=PL0RqAjByAphGlunfvu2mM6aFyOJkdywyZ"),
    ("Hard Ops User Gallery",   "https://www.pinterest.com/masterxeon1001/hard-ops-users/"),
    ("Challenge Board",         "https://www.pinterest.com/masterxeon1001/-np/"),
    ("Blender Transition Group",  "https://www.facebook.com/groups/701978080244781/"),
    ("Hard Ops Facebook Group", "https://www.facebook.com/groups/HardOps/"),
    ("Hard Ops Discord Channel","https://discord.gg/ySRW6u9"),
    ("BoxCutter Release Log", "https://masterxeon1001.com/2020/10/03/boxcutter-717-update-log/")
]

ko_weblinks = [
    ("KitOps Free",           "https://gumroad.com/l/kitops"),
    ("HOPS Classic Inserts",  "https://gumroad.com/l/hopsclassicinserts"),
    ("Kit OPS Homepage",      "https://www.kit-ops.com/")
]


class HOPS_OT_InsertsPopupPreview(bpy.types.Operator):
    """Asset Multiloader
    KitOps / DecalMachine / PowerLink

    LMB - Insert Popup Window
    Shift - Insert Popup Persistent (Digital only)
    Alt - KitOps Insert Popup (alt)

    """
    #Ctrl + Shift - Mark as cutter (E)

    bl_idname = "view3d.insertpopup"
    bl_label = "Kit Ops"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        preference = addon.preference().ui
        dpi_value = bpy.context.preferences.system.dpi
        wm = context.window_manager

        if event.shift and event.ctrl and not event.alt:
            selected = context.selected_objects

            for obj in selected:
                bpy.ops.object.convert(target='MESH')
                bpy.context.object.location[2] = 0.01
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                bpy.ops.hops.soft_sharpen()
                bpy.context.object.kitops.type = 'CUTTER'
                bpy.context.object.kitops.main = True
                bpy.context.object.kitops.boolean_type = 'DIFFERENCE'
            return {'FINISHED'}
        elif event.ctrl:
            bpy.ops.hops.kit_ops_window("INVOKE_DEFAULT")
            return {'FINISHED'}
        else:
            if addon.preference().property.ko_popup_type == 'DEFAULT' or event.alt:
                if preference.use_kitops_popup:
                    return context.window_manager.invoke_popup(self, width=int(200 * get_dpi_factor(force=False)))
                else:
                    return context.window_manager.invoke_props_dialog(self, width=int(200 * get_dpi_factor(force=False)))
            else:
                if addon_exists("DECALmachine") or hasattr(wm, 'kitops'):
                    bpy.ops.hops.kit_ops_window("INVOKE_DEFAULT")
                else:
                    self.report({'INFO'}, F'An error has occured')
                return {'FINISHED'}

    def draw(self, context):
        wm = context.window_manager
        if hasattr(wm, 'kitops'):

            import importlib
            kitops = importlib.import_module(bpy.context.window_manager.kitops.addon)

            KO_PT_ui = kitops.addon.interface.panel.KO_PT_ui
            KO_PT_ui.draw(self,context)

            preference = kitops.addon.utility.addon.preference

            preference = preference()

            self.layout.separator()

            row = self.layout.row()
            row.label(text='Sort Modifiers')
            row.prop(preference, 'sort_modifiers', text='')

            if preference.sort_modifiers:
                row = self.layout.row(align=True)
                row.alignment = 'RIGHT'
                split = row.split(align=True, factor=0.85)

                row = split.row(align=True)
                for type in modifier.sort_types:
                    icon = F'MOD_{type}'
                    if icon == 'MOD_WEIGHTED_NORMAL':
                        icon = 'MOD_NORMALEDIT'
                    elif icon == 'MOD_SIMPLE_DEFORM':
                        icon = 'MOD_SIMPLEDEFORM'
                    elif icon == 'MOD_DECIMATE':
                        icon = 'MOD_DECIM'
                    elif icon == 'MOD_WELD':
                        icon = 'AUTOMERGE_OFF'
                    elif icon == 'MOD_UV_PROJECT':
                        icon = 'MOD_UVPROJECT'
                    elif icon == 'MOD_NODES':
                        icon = 'GEOMETRY_NODES'

                    prop_str = F'sort_{type.lower()}'
                    if hasattr(preference, prop_str):
                        row.prop(preference,prop_str, text='', icon=icon)

                row = split.row(align=True)
                row.scale_x = 1.5
                row.popover('KO_PT_sort_last', text='', icon='SORT_ASC')

        else:
            layout = self.layout

            col = layout.column(align=True)
            row = col.row()
            box = col.box()

            for name, url in ko_weblinks:
                box.operator("wm.url_open", text=name).url = url


    def check(self, context):
        try:
            return True
        except:
            return {"RUNNING_MODAL"}

class HOPS_OT_AddonPopupPreview(bpy.types.Operator):
    """
    Addon checker popup

    """
    bl_idname = "view3d.addoncheckerpopup"
    bl_label = "Addon Popup"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.system.dpi

        return context.window_manager.invoke_props_dialog(self, width=int(200 * get_dpi_factor(force=False)))

    def draw(self, context):
        draw_addon_diagnostics(self.layout, columns=2)

    def check(self, context):
        return True


class HOPS_OT_PizzaPopupPreview(bpy.types.Operator):
    """
    Order A Pizza!

    """
    bl_idname = "view3d.pizzapopup"
    bl_label = "Pizza Popup"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        dpi_value = bpy.context.preferences.system.dpi

        return context.window_manager.invoke_props_dialog(self, width=int(200 * get_dpi_factor(force=False)))

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.label(text="Pizza Ops")
        layout.label(text="")
        layout.label(text="")

        row = layout.row()

        layout.label(text="Dominos Pizza")
        layout.operator("wm.url_open", text="Order Dominoes").url = "https://order.dominos.com/"
        layout.label(text="")
        layout.separator()

        layout.label(text="Pizza Hut Pizza")
        layout.operator("wm.url_open", text="Order Pizza Hut").url = "http://www.pizzahut.com/"
        layout.label(text="")
        layout.separator()

        layout.label(text="Papa John's Pizza")
        layout.operator("wm.url_open", text="Order Papa John's").url = "https://www.papajohns.com/order/menu"
        layout.label(text="")
        layout.separator()
