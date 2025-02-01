
#Background is weird, Need to look at criteria for importing them then see if we can start just one task..?
#Node groups causes crash
#Channel packing?


import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator
from bpy.props import StringProperty
from ..background_and_progress import BakeInProgress as Bip
from ..messages import print_message

class SimpleBake_OT_Image_Sequence(Operator):
    """SimpleBake Image Sequence Operator"""
    bl_idname = "simplebake.image_sequence"
    bl_label = "SimpleBake Image Squence Bake Operator"

    _timer = []
    start_frame = 0
    end_frame = 0

    cmd: StringProperty()

    def modal(self, context, event):
        if event.type == 'TIMER':

            if Bip.was_error:
                print_message(context, "Cancelling Image Sequence timer after error")
                self.cancel(context)
                return {'CANCELLED'}

            cur_frame = context.scene.frame_current
            if cur_frame < self.end_frame:
                if not Bip.is_baking:

                    #Must be after the first run
                    Bip.running_sequence_first = False

                    #Check if this will be the last run
                    if cur_frame + 1 == self.end_frame:
                        #This restores all operators to normal operation (e.g. copy and apply)
                        #Bip.running_sequence = False
                        #Common bake finishing turns this off again when message has been displayed
                        Bip.running_sequence_last = True

                    #Advance frame and run the bake again
                    context.scene.frame_current += 1
                    print_message(context, f"Image sequence calling main operator for frame {context.scene.frame_current}")
                    eval("bpy.ops."+self.cmd+"()")
            else:
                self.cancel(context)
                return {'CANCELLED'}

        return {'PASS_THROUGH'}


    def execute(self, context):

        sbp = context.scene.SimpleBake_Props
        print_message(context, f"Image sequence calling main operator: {self.cmd}")


        self.start_frame = sbp.bake_sequence_start_frame
        self.end_frame = sbp.bake_sequence_end_frame

        Bip.running_sequence = True
        Bip.running_sequence_last = False
        Bip.sequence_frames = (self.end_frame+1) - self.start_frame

        context.scene.frame_set(self.start_frame)

        wm = context.window_manager
        self._timer.append(wm.event_timer_add(1.0, window=context.window))
        wm.modal_handler_add(self)

        #First run of the chosen command
        Bip.running_sequence_first = True
        eval("bpy.ops."+self.cmd+"()")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        for t in self._timer:
            wm.event_timer_remove(t)


classes = ([
    SimpleBake_OT_Image_Sequence
        ])

def register():

    global classes
    for cls in classes:
        register_class(cls)

def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
