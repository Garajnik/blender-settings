# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright: https://github.com/jayanam/bl_ui_widgets

import bpy

import blf

from . bl_ui_widget import BL_UI_Widget

app_version = bpy.app.version


class BL_UI_Label(BL_UI_Widget):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)

        self._text_color = (1.0, 1.0, 1.0, 1.0)
        self._text = "Label"
        self._text_size = 16
        self._text_scale = 1.0

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    @property
    def text_scale(self):
        return self._text_scale

    @text_scale.setter
    def text_scale(self, value):
        self._text_scale = value

    def is_in_rect(self, x, y):
        return False

    def draw(self):
        if not self.visible:
            return

        area_height = self.get_area_height()

        ui_scale = bpy.context.preferences.view.ui_scale

        p_font_size = self._text_size * self._text_scale * ui_scale
        if app_version < (3, 1, 0):
            p_font_size = round(p_font_size)

        if app_version < (3, 4, 0):
            blf.size(0, p_font_size, 72)
        else:
            blf.size(0, p_font_size)

        textpos_y = area_height - self.y_screen - self.height
        blf.position(0, self.x_screen, textpos_y, 0)

        r, g, b, a = self._text_color

        blf.color(0, r, g, b, a)

        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(0, 1, -1)

        blf.draw(0, self._text)

        blf.disable(0, blf.SHADOW)
