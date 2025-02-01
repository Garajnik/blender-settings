# SPDX-License-Identifier: GPL-2.0-or-later

from bpy.types import Panel
from bpy.utils import (
  register_class,
  unregister_class,
)


class NA_PT_Panel(Panel):
    bl_label = "Node Arrange"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Arrange"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        scene = context.scene
        settings = scene.na_settings

        layout.operator("node.na_arrange_selected")

        layout.prop(settings, "margin")

        row = layout.row(align=True, heading="Adjust Vertical")
        row.prop(settings, "move_to_linked_y", text="")
        sub = row.row(align=True)
        sub.active = settings.move_to_linked_y
        sub.prop(settings, "move_to_linked_y_type", text="")


classes = [NA_PT_Panel]


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        if cls.is_registered:
            unregister_class(cls)
