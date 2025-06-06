from pack_utils import PackScenario
from uvpm_core import (
    packer,
    LogType,
    PackTask,
    Stage,
    StageParams,
    StdStageTarget)


class Scenario(PackScenario):

    def run(self):
   
        self.pack_params.groups_together = True
        self.pack_params.grouping_compactness = self.g_scheme.group_compactness
        task = PackTask(0, self.pack_params)

        stage_params = StageParams()

        stage_target = StdStageTarget()
        for box in self.target_boxes:
            stage_target.append(box)

        group_islands = [group.islands for group in self.g_scheme.groups if group.islands is not None]

        stage = Stage()
        stage.params = stage_params
        stage.target = stage_target
        stage.input_islands = group_islands
        stage.static_islands = self.static_islands
        
        self.add_stage_to_task(task, stage)

        self.pack_manager.add_task(task)
        return self.pack_manager.pack()
