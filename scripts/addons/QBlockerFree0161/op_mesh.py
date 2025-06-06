import bpy
import math
import mathutils
from .snap_module import SnappingClass
# from .draw_module import *
from .utilities.raycast_utils import GetPlaneLocation, GetHeightLocation
from .qspace import CoordSysClass
from .qwplane import WorkingPlane

numkeyList = {'NUMPAD_1', 'NUMPAD_2', 'NUMPAD_3', 'NUMPAD_4', 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8', 'NUMPAD_9'}


# box create op new
class MeshCreateOperator(bpy.types.Operator):
    bl_idname = ""
    bl_label = ""
    bl_context = "objectmode"

    addon_prefs = None

    drawcallback = None
    mainMouse = 'LEFTMOUSE'
    wMatrix = mathutils.Matrix()

    objectType = 1
    basetype = 1
    minSegment = 4

    toolstage = 0

    firstPoint = mathutils.Vector((0, 0, 0))
    secondPoint = mathutils.Vector((0, 0, 0))
    heightcoord = 0
    mouse_pos = (0, 0)

    # classes
    qObject = None
    snapClass = None
    coordsysClass = None
    workingplane = None

    # for save to reuse
    isWorkingPlane = False
    isSmooth = False
    isCentered = False
    isIncrement = False
    isFlat = False
    isOriented = False
    isHelpDraw = True
    isParamDraw = True
    meshSegments = 0
    lastdefmeshSegs = 0
    edgediv = 2
    object_ignorebehind = 'ALL'
    lastobject_ignorebehind = 'ALL'
    # last_isHelpDraw = True

    mouseStart = [0, 0]
    mouseEnd_x = 0
    inc_px = 30

    segkeyHold = False
    snapSegHold = False
    wPlaneHold = False
    mScrolled = False
    zSnapState = False

    def ResetOpValues(self):
        self.secondPoint = mathutils.Vector((0, 0, 0))
        self.firstPoint = mathutils.Vector((0, 0, 0))
        self.coordsysClass.ToggleAxis(True)
        self.isIncrement = False
        self.toolstage = 0

    # set mouse buttons based on preferences
    def GetMainMouseButton(self):
        addonMpref = self.addon_prefs.mouse_enum
        if addonMpref == 'LEFT':
            return ('LEFTMOUSE', 'RIGHTMOUSE')
        elif addonMpref == 'RIGHT':
            return ('RIGHTMOUSE', 'LEFTMOUSE')

    # overide it if need smoothing
    def ToggleMeshSmooth(self):
        pass

    # set mesh segments dinamically
    def ChangeMeshSegments(self):
        pass

    # step mesh segments dinamically
    def StepMeshSegments(self, _val):
        pass

    # create Qobject type
    def CreateQobject(self):
        pass

    def ChangeSnapSegments(self):
        allstep = int((self.mouse_pos[0] - self.mouseStart[0]) // self.inc_px)
        prevalue = max(1, min(10, self.snapClass.orig_edgediv + allstep))
        if prevalue != self.snapClass.edgediv:
            self.mouseEnd_x = self.mouseStart[0] + ((prevalue - self.snapClass.orig_edgediv) * self.inc_px)
            self.snapClass.SetSnapPoints(self.mouse_pos, prevalue)

    # Stage One: create object set matrix
    def Stage_Create(self, _context):
        self.wMatrix = self.coordsysClass.GetCoordSys(_context, self.mouse_pos, self.isOriented)
        # check if snap. Set matrix and first point
        if self.snapClass.isSnapActive and self.snapClass.closestPoint is not None:
            self.firstPoint = self.snapClass.closestPoint
            self.wMatrix.translation = self.firstPoint
        else:
            self.firstPoint = self.wMatrix.to_translation()
        # create object
        self.qObject.CreateBObject(self.wMatrix)
        bpy.context.view_layer.update()
        # select object if not in edit mode
        activeOB = _context.active_object
        if activeOB is not None and activeOB.mode != 'EDIT':
            self.qObject.SelectObject()
        # self.qObject.bObject.hide_viewport = True
        self.qObject.HideObject(True)

    # Stage Two: set base
    def Stage_Base(self, _context, _event):
        # self.qObject.bObject.hide_viewport = False
        self.qObject.HideObject(False)
        # change base type with ctrl and shift
        self.SetBaseType(_event)
        # set second position point on grid or object.
        if self.snapClass.isSnapActive and self.snapClass.closestPoint is not None:
            self.secondPoint = self.snapClass.GetClosestPoint(self.qObject.bMatrix)
        else:
            self.secondPoint = GetPlaneLocation(_context, self.mouse_pos, self.qObject.bMatrix)

        self.qObject.UpdateBase(self.firstPoint, self.secondPoint)

    # Stage Three: set height
    def Stage_Height(self, _context):
        if not self.segkeyHold:
            # if snap active
            if self.snapClass.isSnapActive and self.snapClass.closestPoint is not None:
                mat_inv = self.qObject.bMatrix.inverted()
                l_closestPoint = mat_inv @ self.snapClass.closestPoint
                self.heightcoord = l_closestPoint[2]
            else:  # no snap
                self.heightcoord = GetHeightLocation(_context, self.mouse_pos, self.qObject.bMatrix, self.secondPoint)
            # if increment height
            if self.isIncrement:
                gridstep = _context.space_data.overlay.grid_scale
                self.heightcoord = math.floor((self.heightcoord / gridstep)) * gridstep
            self.qObject.UpdateHeight(self.heightcoord)

    def SetBaseType(self, _event):
        if _event.ctrl and not _event.shift:  # CTRL
            self.basetype = self.qObject.SetBaseType(2)
        elif not _event.ctrl and _event.shift:  # SHIFT
            self.basetype = self.qObject.SetBaseType(3)
        elif _event.ctrl and _event.shift:  # CTRL and SHIFT
            self.basetype = self.qObject.SetBaseType(4)
        else:
            self.basetype = self.qObject.SetBaseType(1)  # NONE

    # main operator loop
    def modal(self, context, event):
        context.area.tag_redraw()
        # allow navigation
        if event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}

        # allow numpad view keys
        if self.toolstage == 0 and event.type in numkeyList and event.value == 'PRESS':
            return {'PASS_THROUGH'}

        # click not allowed
        if event.type == self.mainMouse[0] and event.value == 'CLICK':
            return {'RUNNING_MODAL'}

        # pass through alt for maya camera control keys
        if event.type == self.mainMouse[0] and event.alt:
            return {'PASS_THROUGH'}

        # snap active
        if self.snapClass.isSnapActive:
            if self.toolstage != 0:
                self.wMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)
            self.snapClass.CheckSnappingTarget(self.mouse_pos)

        # mouse move event handling
        if event.type == 'MOUSEMOVE':
            # get act mouse pos
            self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)

            # segments calculation
            if self.segkeyHold and not self.mScrolled:
                self.ChangeMeshSegments()

            # edge div for snapping
            elif self.snapSegHold and not self.mScrolled:
                self.ChangeSnapSegments()

            # adjust working plane size
            if self.wPlaneHold and event.ctrl and self.isWorkingPlane:
                hMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)
                if self.snapClass.isSnapActive and self.snapClass.closestPoint is not None:
                    hMatrix.translation = self.snapClass.closestPoint
                self.workingplane.SetGridSize(hMatrix)

            # refresh matrix while moving mouse in 0 stage
            elif self.toolstage == 0 and not self.wPlaneHold:
                self.wMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)
                # change base type with ctrl and shift
                self.SetBaseType(event)
            # set second point (mouse move stage)
            elif self.toolstage == 1:
                self.Stage_Base(context, event)

            # set height (mouse move stage)
            elif self.toolstage == 2 and not self.qObject.basetype == 4 and not self.qObject.isFlat:
                self.Stage_Height(context)

        # left mouse click handling
        elif event.type == self.mainMouse[0] and not self.wPlaneHold:
            if event.value == 'PRESS':
                self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
                # FirstClick(create object and matrix)
                if self.toolstage == 0:
                    self.Stage_Create(context)
                    self.toolstage = 1
                # last stage end
                elif self.toolstage == 2:
                    self.toolstage = 0
            # set height
            elif event.value == 'RELEASE':
                # if just mouseclick reset state
                if self.toolstage == 1 and not self.secondPoint:
                    self.qObject.DeleteBObject()
                    self.ResetOpValues()
                # skip height stage if Uniform All
                elif self.toolstage == 1:
                    self.coordsysClass.ToggleAxis(False)
                    # turn off snap on Z height
                    if self.addon_prefs.zsnaptoggle_bool:
                        self.zSnapState = self.snapClass.snapState
                        self.snapClass.SetState(self.mouse_pos, 0)
                    self.toolstage = 2
                else:
                    # finalize mesh scale and normals, create new class instance
                    self.qObject.FinalizeMeshData()
                    activeOB = bpy.context.active_object
                    if activeOB is not None and activeOB.mode == 'EDIT':
                        self.coordsysClass.ResetResult()

                    self.qObject = self.qObject.copyData(self)
                    bpy.ops.ed.undo_push(message="QObject Create")
                    self.ResetOpValues()
                    # restore snap on Z height
                    if self.addon_prefs.zsnaptoggle_bool:
                        if self.snapClass.snapState == 0:
                            self.snapClass.SetState(self.mouse_pos, self.zSnapState)

        # toggle help text
        elif event.type == 'F1' and event.value == 'PRESS':
            self.isHelpDraw = not self.isHelpDraw
            self.addon_prefs.ishelp = self.isHelpDraw

        # toggle param text
        elif event.type == 'F2' and event.value == 'PRESS':
            self.isParamDraw = not self.isParamDraw
            self.addon_prefs.iscursorparam = self.isParamDraw

        # toggle matrix orientation
        elif event.type == 'Q' and event.value == 'PRESS':
            self.isOriented = not self.isOriented
            self.coordsysClass.ResetResult()
            self.wMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)

        # toggle centered
        elif event.type == 'O' and event.value == 'PRESS':
            self.isCentered = self.qObject.ToggleMeshCenter()

        # toggle flat
        elif event.type == 'H' and event.value == 'PRESS':
            if self.objectType != 3:
                self.isFlat = self.qObject.SwitchMeshType()
            else:
                self.isFlat = False

        # set snap segments with keyhold
        if event.type == 'C':
            if event.value == 'PRESS':
                if not self.snapSegHold:
                    self.mScrolled = False
                    self.mouseStart = (event.mouse_region_x, event.mouse_region_y)
                    self.mouseEnd_x = self.mouseStart[0]
                    self.snapClass.orig_edgediv = self.snapClass.edgediv
                    self.snapSegHold = True
            elif event.value == 'RELEASE':
                self.snapSegHold = False
                self.mScrolled = False

        # set working plane
        if event.type == 'W' and self.toolstage == 0:
            if event.value == 'PRESS':
                # RESET : if shift key hold, reset working plane to system grid size
                if event.shift and self.isWorkingPlane:
                    self.workingplane.ResetSize(context)
                # SET FIRST : if w not hold set matrix and turn on wplane (it need to avoid repeated press event call)
                elif not self.wPlaneHold:
                    # turn on if exist
                    if not self.isWorkingPlane:
                        hMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)
                        if self.snapClass.isSnapActive and self.snapClass.closestPoint is not None:
                            hMatrix.translation = self.snapClass.closestPoint
                        self.workingplane.SetMatrix(hMatrix)
                        self.workingplane.SetActive(context, True)
                        if self.addon_prefs.wpcursor_bool:
                            self.workingplane.SetCursorToGrid(context)
                        self.isWorkingPlane = True
                        self.wPlaneHold = True
                    # only turn on size tweak with mouse
                    elif event.ctrl:
                        self.wPlaneHold = True
                    # turn off if exist
                    else:
                        self.workingplane.SetActive(context, False)
                        self.isWorkingPlane = False
            elif event.value == 'RELEASE':
                self.wPlaneHold = False

        # set ignore tpye
        elif event.type == 'E' and event.value == 'PRESS':
            if self.object_ignorebehind == 'ALL':
                self.object_ignorebehind = 'FRONT'
            elif self.object_ignorebehind == 'FRONT':
                self.object_ignorebehind = 'GRID'
            else:
                self.object_ignorebehind = 'ALL'
            self.coordsysClass.ResetResult()
            self.wMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)

        # toggle smooth mesh (virtual)
        elif event.type == 'D' and event.value == 'PRESS':
            self.ToggleMeshSmooth()

        # set mesh segments (virtual)
        if event.type == 'S':
            if event.value == 'PRESS':
                if not self.segkeyHold:
                    self.mScrolled = False
                    self.mouseStart = (event.mouse_region_x, event.mouse_region_y)
                    self.mouseEnd_x = self.mouseStart[0]
                    self.qObject.originalSegments = self.qObject.meshSegments
                    self.segkeyHold = True
            elif event.value == 'RELEASE':
                self.segkeyHold = False
                self.mScrolled = False

        # increase snap points
        if event.type == 'WHEELUPMOUSE':
            if self.snapSegHold:
                self.mScrolled = True
                self.snapClass.ChangeSnapPoints(self.mouse_pos, 1)
            elif self.segkeyHold:
                self.mScrolled = True
                self.StepMeshSegments(1)
            else:
                # self.coordsysClass.ResetResult()
                # self.wMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)
                return {'PASS_THROUGH'}

        # decrease snap points
        if event.type == 'WHEELDOWNMOUSE':
            if self.snapSegHold:
                self.mScrolled = True
                self.snapClass.ChangeSnapPoints(self.mouse_pos, -1)
            elif self.segkeyHold:
                self.mScrolled = True
                self.StepMeshSegments(-1)
            else:
                # self.coordsysClass.ResetResult()
                # self.wMatrix = self.coordsysClass.GetCoordSys(context, self.mouse_pos, self.isOriented)
                return {'PASS_THROUGH'}

        # toggle increments
        if event.type == 'LEFT_SHIFT' and self.toolstage == 2:
            if event.value == 'PRESS':
                self.isIncrement = True
            elif event.value == 'RELEASE':
                self.isIncrement = False

        # toggle snap
        if event.type in {'Y', 'Z'} and event.value == 'PRESS':
            self.snapClass.ToggleState(self.mouse_pos, 1)

        if event.type == 'X' and event.value == 'PRESS':
            self.snapClass.ToggleState(self.mouse_pos, 2)

        # exit operator
        if event.type in {self.mainMouse[1], 'ESC'}:  # Cancel
            # delete object if creation not finished
            if self.toolstage != 0 and self.qObject:
                self.qObject.DeleteBObject()
                self.qObject.DeleteBMesh()
            else:
                self.qObject.DeleteBMesh()
            # save values for next use
            self.__class__.edgediv = self.snapClass.edgediv
            self.__class__.isFlat = self.isFlat
            self.__class__.isCentered = self.isCentered
            self.__class__.isSmooth = self.isSmooth
            self.__class__.meshSegments = self.qObject.meshSegments
            self.__class__.basetype = self.basetype
            self.__class__.isOriented = self.isOriented
            self.__class__.lastdefmeshSegs = self.addon_prefs.segs_int
            self.__class__.lastobject_ignorebehind = self.addon_prefs.object_ignorebehind
            # remove handlers, cleanup
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self.snapClass.CleanUp()
            self.coordsysClass.CleanUp()
            self.workingplane.wasActive = self.workingplane.isActive
            if self.workingplane.isActive:
                self.workingplane.SetActive(context, False)
            context.area.tag_redraw()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D':
            preferences = context.preferences
            self.addon_prefs = preferences.addons[__package__].preferences
            # Instantiate modul classes
            self.coordsysClass = CoordSysClass(context, self, self.addon_prefs.axis_bool, self.addon_prefs)
            self.snapClass = SnappingClass(self, self.coordsysClass, context, self.edgediv, self.addon_prefs)
            self.mainMouse = self.GetMainMouseButton()
            # Get Working Plane
            self.workingplane = WorkingPlane.InvokeClass(context, self.addon_prefs)
            self.isWorkingPlane = self.workingplane.wasActive
            # gridhit reload
            if self.lastobject_ignorebehind != self.addon_prefs.object_ignorebehind:
                self.object_ignorebehind = self.addon_prefs.object_ignorebehind
                self.lastobject_ignorebehind = self.addon_prefs.object_ignorebehind
            # Mesh segment reload
            if self.lastdefmeshSegs != self.addon_prefs.segs_int:
                self.meshSegments = self.addon_prefs.segs_int
                self.lastdefmeshSegs = self.addon_prefs.segs_int
            # Default help state
            self.isHelpDraw = self.addon_prefs.ishelp
            self.isParamDraw = self.addon_prefs.iscursorparam
            # add draw handler
            uidpi = int((72 * preferences.system.ui_scale))
            uifactor = preferences.system.ui_scale * (self.addon_prefs.text_size_int / 14)
            args = (self, context, uidpi, uifactor, self.addon_prefs)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.drawcallback, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)

            # set first mesh data
            self.CreateQobject()
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
