from scripted_pipeline import GenericScenario, extract_param
from uvpm_core import packer, IslandSet, SimilarityParams, SimilarityMode, LogType, Axis, CoordSpace


class SimilarityScenario(GenericScenario):

    TOPOLOGY_MODE_VERT_COUNT_WARNING_THRESHOLD = 10 * 1000
    TOPOLOGY_MODE_VERT_COUNT_WARNING_MSG = 'The Topology mode may be slow when used with islands with a huge number of vertices (>{})'.format(TOPOLOGY_MODE_VERT_COUNT_WARNING_THRESHOLD)

    VERTEX_BASED_TIP_SENT = False
    VERTEX_BASED_TIP_MSG_ARRAY = [
        "you are checking island similarity using a vertex-based similarity mode",
        "if you are getting inconsistent results using that mode, running 'Merge UVs By Distance' with a small distance may solve the problem"
    ]

    def pre_run(self):
        self.stack_group_iparam_desc = None

        cx_simi_params = self.cx.params['simi_params']

        mode = extract_param(SimilarityMode, cx_simi_params['mode'])

        if mode == SimilarityMode.TOPOLOGY:
            for island in self.cx.input_islands:
                if island.vert_count() >= self.TOPOLOGY_MODE_VERT_COUNT_WARNING_THRESHOLD:
                    packer.send_log(LogType.WARNING, self.TOPOLOGY_MODE_VERT_COUNT_WARNING_MSG)
                    break

        self.simi_params = SimilarityParams()
        self.simi_params.mode = mode
        self.simi_params.precision = cx_simi_params['precision']
        self.simi_params.threshold = cx_simi_params['threshold']
        self.simi_params.check_holes = cx_simi_params['check_holes']
        self.simi_params.flipping_enable = cx_simi_params['flipping_enable']
        self.simi_params.adjust_scale = cx_simi_params['adjust_scale']
        self.simi_params.non_uniform_scaling_tolerance = cx_simi_params['non_uniform_scaling_tolerance']
        self.simi_params.match_3d_axis = extract_param(Axis, cx_simi_params['match_3d_axis'])
        self.simi_params.match_3d_axis_space = extract_param(CoordSpace, cx_simi_params['match_3d_axis_space'])
        self.simi_params.correct_vertices = cx_simi_params['correct_vertices']
        self.simi_params.vertex_threshold = cx_simi_params['vertex_threshold']

        stack_group_iparam_name = cx_simi_params.get('stack_group_iparam_name')
        if stack_group_iparam_name:
            self.stack_group_iparam_desc = self.iparams_manager.iparam_desc(stack_group_iparam_name)

        align_priority_iparam_name = cx_simi_params.get('align_priority_iparam_name')
        if align_priority_iparam_name:
            self.simi_params.align_priority_iparam_desc = self.iparams_manager.iparam_desc(align_priority_iparam_name)

        if self.is_vertex_based():
            self.send_vertex_based_tip()

    @staticmethod
    def is_vertex_based_impl(mode):
        return mode == SimilarityMode.TOPOLOGY or mode == SimilarityMode.VERTEX_POSITION

    def is_vertex_based(self):
        return self.is_vertex_based_impl(self.simi_params.mode)
    
    def send_vertex_based_tip(self, suffix=None):
        if SimilarityScenario.VERTEX_BASED_TIP_SENT:
            return
        
        SimilarityScenario.VERTEX_BASED_TIP_SENT = True
        suffix = ' ({})'.format(suffix) if suffix is not None else ''
        assert len(self.VERTEX_BASED_TIP_MSG_ARRAY) == 2

        self.send_tip(self.VERTEX_BASED_TIP_MSG_ARRAY[0] + suffix)
        self.send_tip(self.VERTEX_BASED_TIP_MSG_ARRAY[1])

    def align_similar(self, input_islands):
        return input_islands.align_similar(self.simi_params)

    def align_similar_by_stack_group(self, input_islands):
        islands_by_stack_group = input_islands.split_by_iparam(self.stack_group_iparam_desc)

        out_aligned_groups = []
        out_non_aligned_islands = IslandSet()

        for stack_group, islands in islands_by_stack_group.items():
            if stack_group == self.stack_group_iparam_desc.default_value:
                out_non_aligned_islands += islands
                continue

            (aligned_groups, non_aligned_islands) = self.align_similar(islands)
            out_aligned_groups += aligned_groups
            out_non_aligned_islands += non_aligned_islands

        return (out_aligned_groups, out_non_aligned_islands)
