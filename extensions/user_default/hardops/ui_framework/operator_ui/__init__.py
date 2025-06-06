import bpy, gpu, time
from mathutils import Vector
from gpu_extras.batch import batch_for_shader

from ..graphics.draw import render_text, render_quad, draw_border_lines
from ..utils.geo import get_blf_text_dims

from ... utility import addon
from ...utility import method_handler
from ...utils.blender_ui import get_dpi_factor


HANDLE = None
SPACE = None
ACTIVE_UI_TYPE = None


class Data():
    '''Global communications from operator to ui modal.'''
    # Fade Variables
    start_time = 0
    time_difference = 0
    hold_complete = False

    # Transitions
    active_count = 0

    # Display Data
    draw_data = []

    draw_bg = False
    draw_border = False
    compact_mode = False

    # Trigger a global reset on the running modal
    reset_all = False

    # Bad space
    close_now = False


class Master():
    '''Used from the modal to launch the drawing.'''

    def receive_draw_data(self, draw_data=[]):
        Data.draw_data = draw_data


    def draw(self, draw_bg=False, draw_border=False, compact_mode=False):

        global HANDLE, SPACE, ACTIVE_UI_TYPE
        context = bpy.context

        ACTIVE_UI_TYPE = context.area.ui_type

        if context.area.ui_type in {'GeometryNodeTree', 'ShaderNodeTree'}:
            if SPACE != bpy.types.SpaceNodeEditor:
                if HANDLE:
                    HANDLE = SPACE.draw_handler_remove(HANDLE, "WINDOW")
                SPACE = bpy.types.SpaceNodeEditor

        elif context.area.ui_type == 'VIEW_3D':
            if SPACE != bpy.types.SpaceView3D:
                if HANDLE:
                    HANDLE = SPACE.draw_handler_remove(HANDLE, "WINDOW")
                SPACE = bpy.types.SpaceView3D

        else:
            if SPACE and HANDLE:
                SPACE.draw_handler_remove(HANDLE, "WINDOW")
            HANDLE = None
            SPACE = None
            if Data.active_count > 0:
                Data.close_now = True
            return

        Data.close_now = False

        prefs = addon.preference()

        if prefs.ui.Hops_operator_display:
            Data.draw_bg = draw_bg
            Data.draw_border = draw_border
            Data.compact_mode = compact_mode

            # Reuse the same modal check
            if Data.active_count == 0:
                Data.active_count += 1
                Data.reset_all = False
                bpy.ops.hops.ui_draw('INVOKE_DEFAULT')
            else:
                Data.reset_all = True


class HOPS_OT_UI_Draw(bpy.types.Operator):
    '''UI Modal'''

    bl_idname = "hops.ui_draw"
    bl_label = "Drawing for operators"
    bl_options = {"INTERNAL"}


    def start(self):
        self.shader = None
        self.timer = None
        self.prefs = addon.preference()
        self.first_draw = False


    def invoke(self, context, event):
        self.start()
        # Globals
        Data.start_time = time.time()
        Data.hold_complete = False
        Data.time_difference = 0

        # Fail Safe
        self.start_time = time.time()
        self.max_time = self.prefs.ui.Hops_operator_display_time + self.prefs.ui.Hops_operator_display_time + 3

        #UI System
        self.shader = Shader(context)
        self.timer = context.window_manager.event_timer_add(0.025, window=context.window)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}


    def modal(self, context, event):

        # Called from bad space : remove self
        if Data.close_now:
            Data.close_now = False
            self.finished(context)
            return {'FINISHED'}

        # Reuse this modal if a new draw data is invoked
        if Data.reset_all == True:
            Data.reset_all = False
            Data.start_time = time.time()
            Data.hold_complete = False
            Data.time_difference = 0
            self.start_time = time.time()
            self.max_time = self.prefs.ui.Hops_operator_display_time + self.prefs.ui.Hops_operator_display_time + 3
            self.first_draw = False
            self.shader.setup_handle(context)

        # Fail Safe
        if time.time() - self.start_time > self.max_time:
            self.finished(context)
            return {'FINISHED'}

        # Get the time difference
        Data.time_difference = time.time() - Data.start_time

        # Remove modal if another starts
        if Data.active_count > 1:
            self.finished(context)
            return {'FINISHED'}

        # Hold the UI on screen until display time is completed
        if Data.hold_complete == False:

            if Data.time_difference >= self.prefs.ui.Hops_operator_display_time:
                Data.hold_complete = True
                Data.time_difference = 0
                Data.start_time = time.time()

            elif Data.time_difference <= self.prefs.ui.Hops_operator_display_time:

                # Redraw the viewport
                if context.area != None:
                    if self.first_draw == False:
                        self.first_draw = True
                        context.area.tag_redraw()
                return {'PASS_THROUGH'}

        # Fade is finished
        if Data.time_difference > self.prefs.ui.Hops_operator_fade:
            self.finished(context)
            return {'FINISHED'}

        # Redraw the viewport
        if context.area != None:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}


    def finished(self, context):
        '''Remove the timer, shader, and reset Data'''

        Data.time_difference = 0
        Data.active_count -= 1

        if self.timer != None:
            context.window_manager.event_timer_remove(self.timer)

        if self.shader != None:
            self.shader.destroy()
            del self.shader

        if context.area != None:
            context.area.tag_redraw()


class Shader():

    def __init__(self, context):
        self.context = context
        self.banner = Banner(context)
        self.setup_handle(context)


    def setup_handle(self, context):
        '''Setup the draw handle for the UI'''

        global HANDLE, SPACE
        # Error
        if SPACE == None:
            return
        # Create new handle
        if HANDLE == None:
            HANDLE = SPACE.draw_handler_add(self.safe_draw, (context, ), "WINDOW", "POST_PIXEL")


    def safe_draw(self, context):
        method_handler(self.draw,
            arguments = (context,),
            identifier = 'UI Framework',
            exit_method = self.destroy)


    def draw(self, context):
        global ACTIVE_UI_TYPE
        if context.area.ui_type != ACTIVE_UI_TYPE:
            return

        self.banner.draw()


    def destroy(self):

        global HANDLE, SPACE, ACTIVE_UI_TYPE

        if SPACE == None:
            HANDLE = None

        if HANDLE != None:
            HANDLE = SPACE.draw_handler_remove(HANDLE, "WINDOW")
            SPACE = None
            ACTIVE_UI_TYPE = None

            if self.banner:
                del self.banner
            return True

        else:
            return False


class Banner():
    '''Drawing class for operator UI.'''

    def __init__(self, context):

        self.context = context
        self.prefs = addon.preference()
        self.scale_factor = get_dpi_factor()
        self.setup_colors()

        # Font sizes
        self.header_font_size = 24
        self.body_font_size = 14

        # Font dims
        self.header_font_dims = get_blf_text_dims(text="Sample", size=self.header_font_size)
        self.body_font_dims = get_blf_text_dims(text="Sample", size=self.body_font_size)

        # Paddings
        self.text_padding = 6 * self.scale_factor
        self.column_gap = 150 * self.scale_factor
        self.side_padding = 15 * self.scale_factor
        self.padding_to_bottom_line = 10 * self.scale_factor
        self.line_width = 2

        # Offsets
        self.prefs_offset = (
            self.prefs.ui.Hops_operator_ui_offset[0] * self.scale_factor,
            self.prefs.ui.Hops_operator_ui_offset[1] * self.scale_factor)

        self.height_to_bottom = self.prefs_offset[1]

        # Totals
        self.total_width = self.get_total_width()
        self.total_height = self.get_total_height()
        self.left_offset = (self.context.area.width * .5) - (self.total_width * .5) + self.prefs_offset[0]

    #######################################
    # SETUPS
    #######################################

    def get_total_width(self):
        '''Get the total wdth of the box.'''

        # Get the widest text width
        if Data.draw_data == []: return

        # Only containts header
        if len(Data.draw_data) == 1:
            text = Data.draw_data[0][0]
            return get_blf_text_dims(text=text, size=self.header_font_size)[0] + self.side_padding * 2


        if Data.compact_mode:
            self.column_gap = 40 * self.scale_factor

            max_width = 0
            compare = 0
            for i, data in enumerate(Data.draw_data):
                # Set first
                if i == 0:
                    if type(data) == str:
                        max_width = get_blf_text_dims(text=data, size=self.header_font_size)[0]
                    else:
                        total = 0
                        for item in data:
                            if type(item) == str:
                                total += get_blf_text_dims(text=item, size=self.header_font_size)[0]
                        max_width = total
                    compare = max_width
                    continue

                # See if the descriptions are wider
                if type(data) == str:
                    compare = get_blf_text_dims(text=data, size=self.body_font_size)[0] + self.column_gap
                else:
                    total = 0
                    for item in data:
                        if type(item) == str:
                            total += get_blf_text_dims(text=item, size=self.body_font_size)[0]
                    total += self.column_gap
                    compare = total

                if compare > max_width:
                    max_width = compare

            return max_width + self.side_padding * 2

        # Header plus other data
        longest = ""
        for i in range(len(Data.draw_data)):

            # Only one item in list
            if len(Data.draw_data[i]) == 1:
                if len(Data.draw_data[i][0]) > len(longest):
                    longest = Data.draw_data[i][0]

            # Two items in list
            elif len(Data.draw_data[i]) == 2:
                compare = str(Data.draw_data[i][0]) + str(Data.draw_data[i][1])
                if len(compare) > len(longest):
                    longest = compare

        return get_blf_text_dims(text=str(longest), size=self.body_font_size)[0] + self.column_gap


    def get_total_height(self):
        '''Get the total height of the box.'''

        # Single line label only
        if len(Data.draw_data) == 1:
            return self.header_font_dims[1] + self.text_padding * 3

        # Full label
        else:

            # For each text add padding for top
            txt_padding_total = self.text_padding * (len(Data.draw_data) - 2)

            # Both divisor lines
            divisor_total = self.line_width * 2
            divisor_total += self.text_padding * 2
            divisor_total += self.padding_to_bottom_line * 2

            # All the text heights
            text_height_total = self.header_font_dims[1]
            text_height_total += self.body_font_dims[1] * (len(Data.draw_data) - 1)

            return text_height_total + txt_padding_total + divisor_total

    #######################################
    # COLORS
    #######################################

    def setup_colors(self):

        # Original
        self.prefs_colors = []
        self.prefs_colors.append(self.prefs.color.Hops_UI_text_color)
        self.prefs_colors.append(self.prefs.color.Hops_UI_secondary_text_color)
        self.prefs_colors.append(self.prefs.color.Hops_UI_text_highlight_color)
        self.prefs_colors.append(self.prefs.color.Hops_UI_cell_background_color)
        self.prefs_colors.append(self.prefs.color.Hops_UI_border_color)


    def set_colors(self):

        self.Hops_UI_text_color            = Vector((self.prefs_colors[0][0], self.prefs_colors[0][1], self.prefs_colors[0][2], self.prefs_colors[0][3]))
        self.Hops_UI_secondary_text_color  = Vector((self.prefs_colors[1][0], self.prefs_colors[1][1], self.prefs_colors[1][2], self.prefs_colors[1][3]))
        self.Hops_UI_text_highlight_color  = Vector((self.prefs_colors[2][0], self.prefs_colors[2][1], self.prefs_colors[2][2], self.prefs_colors[2][3]))
        self.Hops_UI_cell_background_color = Vector((self.prefs_colors[3][0], self.prefs_colors[3][1], self.prefs_colors[3][2], self.prefs_colors[3][3]))
        self.Hops_UI_border_color          = Vector((self.prefs_colors[4][0], self.prefs_colors[4][1], self.prefs_colors[4][2], self.prefs_colors[4][3]))


    def handle_fade(self):

        if Data.hold_complete == True:
            if self.prefs.ui.Hops_operator_fade > 0:

                original_alpha = self.prefs_colors[0][3]
                alpha = self.Hops_UI_text_color[3] - ((original_alpha / self.prefs.ui.Hops_operator_fade) * Data.time_difference)
                self.Hops_UI_text_color = Vector((self.prefs_colors[0][0], self.prefs_colors[0][1], self.prefs_colors[0][2], alpha))

                original_alpha = self.prefs_colors[1][3]
                alpha = self.Hops_UI_secondary_text_color[3] - ((original_alpha / self.prefs.ui.Hops_operator_fade) * Data.time_difference)
                self.Hops_UI_secondary_text_color = Vector((self.prefs_colors[1][0], self.prefs_colors[1][1], self.prefs_colors[1][2], alpha))

                original_alpha = self.prefs_colors[2][3]
                alpha = self.Hops_UI_text_highlight_color[3] - ((original_alpha / self.prefs.ui.Hops_operator_fade) * Data.time_difference)
                self.Hops_UI_text_highlight_color  = Vector((self.prefs_colors[2][0], self.prefs_colors[2][1], self.prefs_colors[2][2], alpha))

                original_alpha = self.prefs_colors[3][3]
                alpha = self.Hops_UI_cell_background_color[3] - ((original_alpha / self.prefs.ui.Hops_operator_fade) * Data.time_difference)
                self.Hops_UI_cell_background_color = Vector((self.prefs_colors[3][0], self.prefs_colors[3][1], self.prefs_colors[3][2], alpha))

                original_alpha = self.prefs_colors[4][3]
                alpha = self.Hops_UI_border_color[3] - ((original_alpha / self.prefs.ui.Hops_operator_fade) * Data.time_difference)
                self.Hops_UI_border_color = Vector((self.prefs_colors[4][0], self.prefs_colors[4][1], self.prefs_colors[4][2], alpha))

    #######################################
    # DRAW
    #######################################

    def draw(self):

        # Resets
        self.height_to_bottom = self.prefs_offset[1]
        self.total_width = self.get_total_width()
        self.total_height =self.get_total_height()
        self.left_offset = (self.context.area.width * .5) - (self.total_width * .5) + self.prefs_offset[0]

        if Data.draw_data != []:

            # Colors
            self.set_colors()
            self.handle_fade()

            # Draw header and lines
            if len(Data.draw_data) > 1:
                self.draw_background()
                self.draw_divisor_line()
                self.draw_body_text()
                self.draw_divisor_line()
                self.draw_header_text()

            # Draw only header
            else:
                self.draw_background()
                self.draw_header_text()


    def draw_background(self):

        # Setup for background and border : TL, BL, TR, BR
        quad = (
            (self.left_offset                   , self.height_to_bottom + self.total_height),
            (self.left_offset                   , self.height_to_bottom),
            (self.left_offset + self.total_width, self.height_to_bottom + self.total_height),
            (self.left_offset + self.total_width, self.height_to_bottom))

        # Draw background
        if Data.draw_bg:
            render_quad(quad=quad,
                        color=self.Hops_UI_border_color,
                        bevel_corners=True)

        # Draw border
        if Data.draw_border:
            draw_border_lines(vertices=quad, width=self.prefs.ui.Hops_operator_border_size, color=self.Hops_UI_cell_background_color)


    def draw_divisor_line(self):

        left_point  = (self.left_offset + self.side_padding                   , self.height_to_bottom + self.padding_to_bottom_line)
        right_point = (self.left_offset - self.side_padding + self.total_width, self.height_to_bottom + self.padding_to_bottom_line)

        self.height_to_bottom += self.line_width + self.text_padding + self.padding_to_bottom_line

        draw_divider_lines(
            vertices=[left_point, right_point],
            width=self.line_width,
            color=self.Hops_UI_cell_background_color,
            bevel_corners=False,
            format_lines=False)


    def draw_body_text(self):

        # Text items for the body
        for index, item in enumerate(Data.draw_data[1:]):
            # Left or Right
            count = 0
            for string in item:

                if type(string) == float:
                    string = "{0:.3f}".format(string)
                string = str(string)

                # Left Side
                if count == 0:
                    pos = (self.left_offset + self.side_padding, self.height_to_bottom)
                    render_text(
                        text=string,
                        position=pos,
                        size=self.body_font_size,
                        color=self.Hops_UI_text_color)

                # Right Side
                elif count == 1:
                    text_dims = get_blf_text_dims(text=string, size=self.body_font_size)
                    pos = (self.left_offset + self.total_width - text_dims[0] - self.side_padding, self.height_to_bottom)
                    render_text(
                        text=string,
                        position=pos,
                        size=self.body_font_size,
                        color=self.Hops_UI_secondary_text_color)

                count += 1

            self.height_to_bottom += self.body_font_dims[1] + self.text_padding
        self.height_to_bottom -= self.text_padding * 2


    def draw_header_text(self):

        string = Data.draw_data[0][0]
        pos = (self.left_offset + self.side_padding, self.height_to_bottom)

        # Single line label only
        if len(Data.draw_data) == 1:
            pos = (self.left_offset + self.side_padding, self.height_to_bottom + self.text_padding * 2)

        render_text(
            text=string,
            position=pos,
            size=self.header_font_size,
            color=self.Hops_UI_secondary_text_color)


def draw_divider_lines(vertices=[], width=1, color=(0,0,0,1), bevel_corners=True, format_lines=False):
    '''Render quads passed in. \n
        Top Left, Bottom Left, Top Right, Bottom Right
    '''

    built_in_shader = 'UNIFORM_COLOR' if bpy.app.version[0] >=4 else '2D_UNIFORM_COLOR'
    shader = gpu.shader.from_builtin(built_in_shader)
    #Enable(GL_LINE_SMOOTH)
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(width)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

    gpu.state.line_width_set(width)
    gpu.state.blend_set('NONE')

    del shader
    del batch


from bpy.app.handlers import persistent
@persistent
def remove_op_draw_shader(dummy):
    global HANDLE, SPACE, ACTIVE_UI_TYPE
    if HANDLE != None:
        HANDLE = SPACE.draw_handler_remove(HANDLE, "WINDOW")
        SPACE = None
        ACTIVE_UI_TYPE = None

    # Reset draw data
    Data.start_time = 0
    Data.time_difference = 0
    Data.hold_complete = False
    Data.active_count = 0
    Data.draw_data = []
    Data.draw_bg = False
    Data.draw_border = False
    Data.reset_all = False
