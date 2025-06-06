import bpy
from bpy.types import Operator
from . import bl_info
from collections import defaultdict
import re
import os


class UNITY_OT_changelog(Operator):
    """Get latest changelog"""

    bl_label = "Changelog"
    bl_idname = "unity.changelog"

    def draw(self, context):
        layout = self.layout

        layout.label(
            text=f"Changelog - v{'.'.join(map(str, bl_info.get('version')))}",
            icon="RECOVER_LAST",
        )

        for change_type, icon in [
            ("added", "ADD"),
            ("fixed", "MODIFIER_DATA"),
            ("changed", "TRACKING_FORWARDS_SINGLE"),
            ("improved", "SHADERFX"),
            ("removed", "REMOVE"),
        ]:
            if self.changes[change_type]:
                layout.label(text=change_type.upper())
                self.draw_changes(layout, self.changes[change_type], icon)

    def draw_changes(self, layout, changes, icon):
        box = layout.box()
        col = box.column(align=True)
        for change in changes:
            row = col.row()
            if "https://discord.com" in change:
                thread = re.search("\/(\d*)\)", change)[1]
                row.label(
                    text=change.replace(
                        f"(https://discord.com/channels/959138815602229389/{thread})",
                        "",
                    ),
                    icon=icon,
                )
                row.operator("wm.url_open", icon="LINKED", emboss=False).url = f"https://discord.com/channels/959138815602229389/{thread}"
            else:
                row.label(text=change, icon=icon)

    def invoke(self, context, event):
        self.execute(context)
        return context.window_manager.invoke_popup(self, width=500)

    def execute(self, context):
        self.changes = defaultdict(list)

        with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as file:
            changlog_start = False
            key = None

            for line in file:
                line = line.strip()

                if line.startswith("## Changelog"):
                    changlog_start = True
                elif line.startswith("##"):
                    changlog_start = False

                if not changlog_start:
                    continue

                if line.startswith("**"):
                    key = line.split("**")[1].lower()

                if key is None:
                    continue

                if line.startswith("-"):
                    line = line.strip("- ")
                    self.changes[key].append(line)

        return {"FINISHED"}


classes = (UNITY_OT_changelog,)

register, unregister = bpy.utils.register_classes_factory(classes)
