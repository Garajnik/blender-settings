from .op_mesh import MeshCreateOperator
from .qobjects.qcylinder import QCylinder
from .draw_module import draw_callback_cylinder


# box create op new
class CylinderCreateOperator(MeshCreateOperator):
    bl_idname = "object.cylinder_create"
    bl_label = "Cylinder Create Operator"

    drawcallback = draw_callback_cylinder
    objectType = 2
    basetype = 3
    isSmooth = True
    isCentered = False

    meshSegments = 16
    originalSegments = 16
    minSegment = 4

    # create Qobject tpye
    def CreateQobject(self):
        self.qObject = QCylinder(self)

    # toggle smooth mesh
    def ToggleMeshSmooth(self):
        self.isSmooth = self.qObject.ToggleSmoothFaces()

    def ChangeMeshSegments(self):
        allstep = int((self.mouse_pos[0] - self.mouseStart[0]) // self.inc_px)
        prevalue = max(self.minSegment, min(128, self.qObject.originalSegments + allstep))
        if prevalue != self.qObject.meshSegments:
            self.qObject.meshSegments = prevalue
            self.mouseEnd_x = self.mouseStart[0] + ((prevalue - self.qObject.originalSegments) * self.inc_px)
            self.qObject.UpdateMesh()
        self.meshSegments = self.qObject.meshSegments

    # step mesh segments dinamically
    def StepMeshSegments(self, _val):
        if _val == 1 and self.meshSegments < 128:
            self.meshSegments += 1
            self.qObject.meshSegments = self.meshSegments
            self.qObject.UpdateMesh()
        if _val == -1 and self.meshSegments > self.minSegment:
            self.meshSegments -= 1
            self.qObject.meshSegments = self.meshSegments
            self.qObject.UpdateMesh()
