# import time
# import traceback
# import sys

import bpy
import bmesh

from mathutils import Vector #, Matrix
from bpy.types import Operator, Object
from bpy.props import *

# from ... utility.shape import modifier
# from ... utility import shape, shader, data, lattice, mesh
# # from .. utility import shape, shader, data, lattice, mesh, modifier
from .. utility.change import last
# from .... sound import time_code
from .... import icon, toolbar
from .... property import new
# from .. utility import tool, addon, object, ray, timed, method_handler, view3d
# from .. utility import addon, object
from ..... utility import method_handler, addon, modifier
# from ..... __init__ import bl_info
# from ... utility import tracked_events, tracked_states
from .. utility import tracked_events, tracked_states, dimensions
from .. utility.modal import refresh


from . import invoke, modal, execute, cancel


description = { #TODO: move other shape releated descriptions here, needs to be a nested dict i.e.
                    # description['mode']['CUT']
                #TODO: move to property operator draw
    'CUT': 'Cut\n\n Modal Shortcut: X\n\n'
           ' Cuts selected meshes using difference boolean modifier\n\n'
           ' Hold shift (on apply) to keep shape live for adjustment.\n'
           ' Tab to edit shape during draw.\n\n'
           ' Cut supports edit mode. \n'
           ' Shift to live can also be used in edit mode',
    'SLICE': 'Slice\n\n Modal Shortcut: X\n\n'
             ' Slices mesh selection using intersect boolean modifier\n\n'
             ' Hold shift (on apply) to keep shape live for adjustment.\n'
             ' The behavior panel contains additional customizations.\n'
             ' Tab to edit shape during draw',
    'INTERSECT': 'Intersect\n\n Modal Shortcut: X >> X \n\n'
             ' Intersect mesh using intersect boolean modifier\n'
             ' Hold shift (on apply) to keep shape live for adjustment. \n'
             ' Tab to edit shape during draw',
    'INSET': 'Inset\n\n Modal Shortcut: I or X >> X >> X \n\n'
             ' Insets mesh using intersect slice with solidify modifier\n'
             ' T (during draw) - adjust inset\n\n'
             ' Hold shift (on apply) to keep shape live for adjustment. \n'
             ' Tab to edit shape during draw',
    'JOIN': 'Join\n\n Modal Shortcut: J\n\n'
            ' Joins meshes using union boolean modifier\n\n'
            ' Hold shift (on apply) to keep shape live for adjustment.\n'
            ' Tab to edit shape during draw.\n\n'
            ' Join supports edit mode.\n'
            ' Shift to live can also be used in edit mode',
    'KNIFE': 'Knife\n\n Modal Shortcut: K or Ctrl + X\n\n'
             ' Knife slice implied geometry on selected mesh\n\n'
             ' Knife will only work on real meshes unaffected by booleans.\n'
             ' Knife supports edit mode.\n\n'
             ' Knife modes:\n'
             ' 3d Knife (experimental) - when utilizing surface draw knife can work in 3d and be realtime\n'
             ' Blue Box - when utilizing off mesh drawing or bypassing extrude blue box utilizes knife project.\n'
             ' ** View Align ensures classic Blue Box is used. **\n\n'
             ' Only blue box state can project cut edges based on 2d geometry without FACES / only edges\n'
                ' ',
    'EXTRACT': 'Extract\n\n Modal Shortcut: Y\n\n'
               ' Extracts live boolean operations into a custom mesh as a custom cutter\n\n'
               ' After extraction the shape will be custom cutter with the extraction set as the cutter.\n'
               ' Can have issues with unapplied scale, loc, rot\n\n'
               ' Extractions are automatically placed in the cutters collection and hidden from view.\n\n'
               ' Extract only works with LIVE BOOLEANS at this time',
    'MAKE': 'Make\n\n Modal Shortcut: A\n\n'
            ' Creates neutral shapes without boolean\n\n'
            ' The behavior panel contains additional customizations.\n'
            ' Make is typically used for general shape creation',
    }


def change_operation(op, context):
    bc = context.scene.bc

    in_operation = op.operation in {'ARRAY', 'SOLIDIFY', 'BEVEL', 'MIRROR'}

    if in_operation and op.operation != bc.start_operation:
        bc.start_operation = op.operation

    elif not in_operation and bc.start_operation != 'NONE':
        try:
            bc['start_operation'] = 'NONE'
        except:
            bc['start_operation'] = 0

    context.workspace.tools.update()


def get_view_align(_):
    return addon.preference().surface == 'VIEW'


previous_surface = 'OBJECT'
def set_view_align(_, value):
    global previous_surface

    preference = addon.preference()

    if value:
        if preference.surface != 'VIEW' and preference.surface != previous_surface:
            previous_surface = preference.surface
        preference.surface = 'VIEW'

    elif preference.surface == 'VIEW':
        preference.surface = previous_surface


def get_knife_mode(op):
    return op.mode == 'KNIFE'


previous_mode = 'CUT'
def set_knife_mode(op, value):
    global previous_mode

    if value:
        if op.mode != 'KNIFE' and op.mode != previous_mode:
            previous_mode = op.mode
        op.mode = 'KNIFE'

    elif op.mode == 'KNIFE':
        op.mode = previous_mode
    # op.mode = 'KNIFE' if value else 'CUT'



class BC_OT_shape_draw(Operator):
    bl_idname = 'bc.shape_draw'
    bl_label = 'BoxCutter'
    bl_description = toolbar.description
    bl_options = {'UNDO'}

    exit: bool = False

    tool = None

    cancelled: bool = False
    alt_skip: bool = False
    alt: bool = False
    ctrl: bool = False
    shift: bool = False
    lmb: bool = False
    mmb: bool = False
    rmb: bool = False
    alt_lock: bool = False
    click_count: int = 0
    original_selected: list = []
    original_visible: list = []
    allow_menu: bool = False

    last: dict = last
    datablock: dict = new.datablock
    ray: dict = new.ray_cast
    start: dict = new.start
    geo: dict = new.geo
    mouse: dict = new.mouse
    view3d: dict = new.view3d
    plane_checks: int = 0
    prior_to_shift: str = 'NONE'

    draw_vert = None
    draw_dot_index: int = 0
    bounds: list = []

    mouse: Vector = (0, 0)
    init_mouse: Vector = (0, 0)
    tweak: bool = False
    track: int = 0
    angle: int = 1

    orthographic: bool = False
    auto_ortho: bool = False

    extruded: bool = False
    mirrored: bool = False

    lazorcut: bool = False
    lazorcut_performed: bool = False
    show_shape: bool = False
    expand_offset: int = 0
    add_point: bool = False
    add_point_lock: bool = False
    move_lock: bool = False

    flip: bool = False
    flip_z: bool = False
    translated: bool = False
    rotated: bool = False
    scaled: bool = False
    segment_state: bool = False
    width_state: bool = False
    wires_displayed: bool = False
    inverted_extrude: bool = False

    snap: BoolProperty(default=False)
    modified: BoolProperty()

    material: str = ''
    existing: dict = {}

    active_only: BoolProperty(
        name = 'Active only',
        description = 'Cut only the active object and align to selected',
        default = False)

    mode: EnumProperty(
        name = 'Mode',
        # description = 'Mode',
        update = toolbar.change_mode,
        items = [
            ('CUT', 'Cut', description['CUT'], icon.id('red'), 0),
            ('SLICE', 'Slice', description['SLICE'], icon.id('yellow'), 1),
            ('INTERSECT', 'Intersect', description['INTERSECT'], icon.id('orange'), 3),
            ('INSET', 'Inset', description['INSET'], icon.id('purple'), 4),
            ('JOIN', 'Join', description['JOIN'], icon.id('green'), 5),
            ('KNIFE', 'Knife', description['KNIFE'], icon.id('blue'), 6),
            ('EXTRACT', 'Extract', description['EXTRACT'], icon.id('black'), 7),
            ('MAKE', 'Make', description['MAKE'], icon.id('grey'), 8)],
        default = 'CUT')

    shape_type: EnumProperty(
        name = 'Shape Type',
        # description = 'Shape',
        update = toolbar.change_mode_behavior,
        items = [
            ('CIRCLE', 'Circle', 'Circle\n\n Draws using circle shape utilizing center draw by default.\n\n'
                                , 'MESH_CIRCLE', 0),
            ('BOX', 'Box', 'Box\n\n Draws using box shape utilizing corner draw by default.\n\n'
                                , 'MESH_PLANE', 1),
            ('NGON', 'Ngon', 'Ngon\n\n Draws using custom points determined by the user.\n\n'
                                'Usage of C during draw to draw toggles closed ngon or open solid line'
                                , 'MOD_SIMPLIFY', 2),
            ('CUSTOM', 'Custom', 'Custom\n\n Draws utilizing custom shape.\n\n'
                                 ' Without a specified mesh the boxcutter logo will be drawn\n'
                                 ' Specify custom mesh using dropdown in tool options or select mesh and press C\n'
                                 ' Capable of utilizing itself as cutter for self.cut. itterative generation\n\n'
                                , 'FILE_NEW', 3)],
        default = 'BOX')

    operation: EnumProperty(
        name = 'Operation',
        # description = 'Modal Operation',
        update = change_operation,
        items = [
            ('NONE', 'Default', '\n Modal Shortcut: TAB', 'LOCKED', 0),
            ('DRAW', 'Draw', '\n Modal Shortcut: D', 'GREASEPENCIL', 1),
            ('EXTRUDE', 'Extrude', '\n Modal Shortcut: E', 'ORIENTATION_NORMAL', 2),
            ('OFFSET', 'Offset', '\n Modal Shortcut: O', 'MOD_OFFSET', 3),
            ('MOVE', 'Move', 'Modal Shortcut: G', 'RESTRICT_SELECT_ON', 4),
            ('ROTATE', 'Rotate', 'Modal Shortcut: R', 'DRIVER_ROTATIONAL_DIFFERENCE', 5),
            ('SCALE', 'Scale', 'Modal Shortcut: S', 'FULLSCREEN_EXIT', 6),
            ('ARRAY', 'Array', '\n Modal Shortcut: V\n\n'
                               ' X, Y, Z, keys to change axis during array\n'
                               ' Shift + R - to reset array distance\n'
                               ' V - cycle radial array / remove array', 'MOD_ARRAY', 7),
            ('SOLIDIFY', 'Solidify', '\n Modal Shortcut: T\n\n'
                                     ' T - adjust thickness / Remove Modifier\n'
                                     ' 1, 2, 3, - cycles offset type on solidify modifier', 'MOD_SOLIDIFY', 8),
            ('BEVEL', 'Bevel', '\n Modal Shortcut: B\n\n'
                               ' B - add bevel / remove modifier\n'
                               ' Q: Toggle back face bevel', 'MOD_BEVEL', 9),
            ('MIRROR', 'Mirror', '\n Modal Shortcut: 1, 2, 3\n\n'
                                 ' Press 1, 2, 3 for axis X, Y, Z\n'
                                 ' Shift + 1, 2, or 3 to flip axis', 'MOD_MIRROR', 10),
            ('DISPLACE', 'Displace', '', 'MOD_DISPLACE', 11),
            ('TAPER', 'Taper', '', 'FULLSCREEN_ENTER', 12),
            ('GRID', 'Grid', '', 'MOD_LATTICE', 13)],
        default = 'NONE')

    behavior: EnumProperty(
        name = 'Behavior',
        # description = '\n Behavior',
        items = [
            ('DESTRUCTIVE', 'Destructive', '\n Modifiers will be applied'),
            ('NONDESTRUCTIVE', 'Non-Destructive', '\n Modifiers will not be applied')],
        default = 'NONDESTRUCTIVE')

    origin: EnumProperty(
        name = 'Draw Origin',
        # description = '\n Shape Origin',
        items = [
            ('CORNER', 'Corner', '\n Modal Shortcut: . (Period)\n\n'
                                 '\n Utilizes Corner for drawing. Default for Box / Custom\n\n', 'SNAP_PERPENDICULAR', 0),
            ('CENTER', 'Center', '\n Modal Shortcut: . (Period)\n\n'
                                 ' Utilizes Center for drawing. Default for Circle\n\n', 'SNAP_FACE_CENTER', 1)],
        default = 'CORNER')

    # TODO: share description with surface enum view align
    align_to_view: BoolProperty(
        name = 'Align to view',
        description = '\n Aligns the shape to the viewport bypassing surface orientation\n\n'
                      ' Disables mesh snapping dots.\n'
                      ' Bypasses object draw alignment.\n\n'
                      ' Sets knife to work via knife project. Supporting (edge-only) 2d shapes',
        get = get_view_align,
        set = set_view_align)

    knife: BoolProperty(
        name = 'Knife',
        description = description['KNIFE'],
        get = get_knife_mode,
        set = set_knife_mode)

    live: BoolProperty(
        name = 'Live',
        description = '\n Display the cuts during the modal\n\n'
                      ' When off cuts will appear after apply',
        default = True)

    repeat: BoolProperty(
        name = 'Repeat',
        description = '\n Repeat the last shape created',
        default = False)


    def invoke(self, context, event):
        return method_handler(
            method=self._invoke,
            arguments=(context, event),
            exit_method=self.cancel,
            exit_arguments =(context, ))


    def _invoke(self, context, event):
        return invoke.operator(self, context, event)


    def modal(self, context, event):
        return method_handler(
            method=self._modal,
            arguments=(context, event),
            exit_method=self.cancel,
            exit_arguments =(context, ))


    def _modal(self, context, event):
        return modal.method(self, context, event)


    def execute(self, context):
        return execute.operator(self, context)


    def cancel(self, context):
        return cancel.operator(self, context)


    def update(self):
        preference = addon.preference()
        bc = bpy.context.scene.bc

        # self.shader.update_handler(self, bpy.context)
        # self.widgets.update_handler(self, bpy.context)

        tracked_events.mouse = self.mouse
        tracked_events.lmb = self.lmb
        tracked_events.mmb = self.mmb
        tracked_events.rmb = self.rmb
        tracked_events.ctrl = self.ctrl
        tracked_events.alt = self.alt
        tracked_events.shift = self.shift

        tracked_states.running = bc.running

        tracked_states.draw_dot_index = self.draw_dot_index

        tracked_states.mode = self.mode
        tracked_states.operation = self.operation
        tracked_states.shape_type = self.shape_type
        tracked_states.origin = self.origin
        tracked_states.rotated = self.rotated
        tracked_states.scaled = self.scaled
        tracked_states.cancelled = self.cancelled
        tracked_states.lazorcut = self.lazorcut

        if self.lmb and self.rmb:
            tracked_states.rmb_lock = True

        elif not self.lmb and tracked_states.rmb_lock:
            tracked_states.rmb_lock = False

        tracked_states.modified = self.modified
        tracked_states.bounds = self.bounds

        if bc.lattice:
            tracked_states.thin = dimensions()[2] <= preference.shape.offset

        tracked_states.extruded = self.extruded

        tracked_states.active_only = self.active_only
