import bpy
import gpu
import mathutils
from gpu_extras.batch import batch_for_shader


def QWPlaneDrawHandler(wPlane, context):
    gpu.state.depth_test_set('LESS')
    gpu.state.blend_set('ALPHA')

    coords = []
    aVcolors = []

    for x in range(wPlane.numSteps * 2 + 1):
        coordX = wPlane.bRectMinMax[0] + x * wPlane.gridstep
        posX1 = wPlane.matrix @ mathutils.Vector((coordX, wPlane.bRectMinMax[0], 0))
        posX2 = wPlane.matrix @ mathutils.Vector((coordX, wPlane.bRectMinMax[1], 0))
        posY1 = wPlane.matrix @ mathutils.Vector((wPlane.bRectMinMax[0], coordX, 0))
        posY2 = wPlane.matrix @ mathutils.Vector((wPlane.bRectMinMax[1], coordX, 0))
        coords.extend([posX1, posX2, posY1, posY2])
        aVcolors.extend([wPlane.gridcolor, wPlane.gridcolor, wPlane.gridcolor, wPlane.gridcolor])

    # shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords, "color": aVcolors})

    shader.bind()
    shader.uniform_float("lineWidth", 2)
    batch.draw(shader)
    gpu.state.depth_test_set('NONE')
    gpu.state.blend_set('NONE')


class WorkingPlane:
    Instance = None
    matrix = mathutils.Matrix()
    gridstep = 1.0
    origFloor = True
    isActive = False
    wasActive = False
    _handle = None

    numSteps = 5
    gridcolor = [0.655, 0.655, 0.655, 0.2]
    bRectMinMax = (0, 0)

    def __init__(self, _context, _matrix, _addon_prefs):
        self.numSteps = _addon_prefs.grid_count
        self.gridcolor = _addon_prefs.grid_color
        self.matrix = _matrix.copy()
        self.gridstep = _context.space_data.overlay.grid_scale_unit
        edgeDist = self.numSteps * self.gridstep
        self.bRectMinMax = (-edgeDist, edgeDist)

    @classmethod
    def InvokeClass(cls, _context, _addon_prefs):
        if not cls.Instance:
            cls.Instance = WorkingPlane(_context, mathutils.Matrix(), _addon_prefs)
        workingplane = cls.Instance
        if workingplane.wasActive:
            workingplane.numSteps = _addon_prefs.grid_count
            workingplane.gridcolor = _addon_prefs.grid_color
            workingplane.SetActive(_context, True)
        return workingplane

    def SetMatrix(self, _matrix):
        self.matrix = _matrix.copy()

    def SetActive(self, _context, _state):
        if _state:
            # self.gridstep = _context.space_data.overlay.grid_scale_unit
            edgeDist = self.numSteps * self.gridstep
            self.bRectMinMax = (-edgeDist, edgeDist)
            args = (self, _context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(QWPlaneDrawHandler, args, 'WINDOW', 'POST_VIEW')
            self.origFloor = _context.space_data.overlay.show_floor
            _context.space_data.overlay.show_floor = False
            self.isActive = True
        else:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            _context.space_data.overlay.show_floor = self.origFloor
            self.isActive = False

    def SetGridSize(self, _matrix):
        actpos = _matrix.to_translation()
        localPos = self.matrix.inverted() @ actpos
        if abs(localPos.x) > abs(localPos.y):
            self.gridstep = abs(localPos.x)
        else:
            self.gridstep = abs(localPos.y)
        edgeDist = self.numSteps * self.gridstep
        self.bRectMinMax = (-edgeDist, edgeDist)

    def ResetSize(self, _context):
        self.gridstep = _context.space_data.overlay.grid_scale_unit
        edgeDist = self.numSteps * self.gridstep
        self.bRectMinMax = (-edgeDist, edgeDist)

    def SetCursorToGrid(self, _context):
        _context.scene.cursor.matrix = self.matrix
