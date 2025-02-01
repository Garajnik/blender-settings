
from uvpm_core import (
    packer,
    RetCode,
    LogType,
    InputError,
    LogFlags,
    InvalidIslandsError,
    InvalidIslandsExtendedError,
    InvalidTopologyExtendedError,
    OpCancelledException,
    StdStageTarget,
    StageParams,
    PackStrategyParams,
    Stage
)
from utils import box_from_coords, eprint, flag_islands


def extract_param(param_type, value, default_value=None):
    if value is None:
        return default_value
        
    return param_type(value)


class Struct(object):
    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap_str(self, value):
        return value

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)): 
            return type(value)([self._wrap(v) for v in value])
        elif isinstance(value, dict):
            return Struct(value)
        elif isinstance(value, str):
            return self._wrap_str(value)
        else:
            return value

GROUP_COUNTER = 0

class GroupInfo:

    def __init__(self, in_group):
        self.num = in_group['num']
        self.name = in_group['name']
        self.in_group = in_group
        self.tdensity_cluster = in_group.get('tdensity_cluster')

        global GROUP_COUNTER
        self.create_id = GROUP_COUNTER
        GROUP_COUNTER += 1

        self.islands = None
        self.stage_target = None
        self.target_boxes = []
        for box_coords in in_group['target_boxes']:
            self.target_boxes.append(box_from_coords(box_coords))

    def get_stage_target(self):
        if self.stage_target is not None:
            return self.stage_target

        if len(self.target_boxes) == 0:
            raise InputError("Group with no target box encountered. Group name: {}".format(self.name))

        stage_target = StdStageTarget()

        for box in self.target_boxes:
            stage_target.append(box)

        self.stage_target = stage_target
        return self.stage_target

    def to_stage(self):
        stage_params = StageParams()

        def process_attr(attr_type, attr_name, target_name=None):
            if target_name is None:
                target_name = attr_name
            
            attr_val = self.in_group.get(attr_name)
            if attr_val is None:
                return
            
            setattr(stage_params, target_name, extract_param(attr_type, attr_val))

        process_attr(bool, 'rotation_enable')
        process_attr(bool, 'pre_rotation_disable')
        process_attr(int, 'rotation_step')
        process_attr(int, 'pixel_margin')
        process_attr(int, 'pixel_padding')
        process_attr(int, 'extra_pixel_margin_to_others')
        process_attr(int, 'pixel_margin_tex_size')
        process_attr(bool, 'groups_together')
        process_attr(bool, 'group_compactness', 'grouping_compactness')
        process_attr(bool, 'pack_to_single_box')
        process_attr(PackStrategyParams, 'pack_strategy')

        stage = Stage()
        stage.params = stage_params
        stage.target = self.get_stage_target()
        stage.input_islands = [self.islands]
        stage.tdensity_cluster_id = self.tdensity_cluster
        return stage


class GroupingScheme:

    def __init__(self, in_g_scheme, group_iparam_desc):

        self.group_iparam_desc = group_iparam_desc
        self.groups_together = in_g_scheme['groups_together']
        self.group_compactness = in_g_scheme['group_compactness']
        self.pack_to_single_box = in_g_scheme['pack_to_single_box']
        self.groups = []
        self.groups_by_num = dict()

    def add_group(self, group):

        if self.groups_by_num.get(group.num) is not None:
            raise InputError('Duplicated group numbers in the grouping scheme')

        self.groups_by_num[group.num] = group
        self.groups.append(group)

    def assign_islands_to_groups(self, islands):

        islands_by_groups = islands.split_by_iparam(self.group_iparam_desc)

        for g_num, g_islands in islands_by_groups.items():

            group = self.groups_by_num.get(g_num)
            if group is None:
                raise InputError('Island assigned to an invalid group')

            group.islands = g_islands

    def validate_locking(self):

        for group in self.groups:
            if group.islands is None:
                continue

            for island in group.islands:
                if island.parent_count < 2:
                    continue

                parents = island.parents
                parent_groups = set()
                for parent in parents:
                    parent_groups.add(parent.get_iparam(self.group_iparam_desc))

                    if len(parent_groups) > 1:
                        packer.send_log(LogType.WARNING, 'Islands from two different groups were locked together!')
                        packer.send_log(LogType.WARNING, 'In result some islands will be processed as not belonging to the groups they were originally assigned to')
                        return


class ScenarioConfig:

    def __init__(self, params):
        self.skip_topology_parsing = params['__skip_topology_parsing']
        self.disable_immediate_uv_update = params['__disable_immediate_uv_update']
        self.disable_tips = params['__disable_tips']

class GenericScenario:

    GROUPING_SCHEME_PARAM_NAME = '__grouping_scheme'
    TIP_COLOR = 'green'
    TIP_HEADER = '<t color="{}">TIP:</t>'.format(TIP_COLOR)

    def __init__(self, cx):
        self.cx = cx
        self.iparams_manager = packer.std_iparams_manager()
        self.g_scheme = None
        self.config = ScenarioConfig(self.cx.params)


    def handle_invalid_islands(self, status_msg, error_msg, invalid_islands):
        flag_islands(self.cx.input_islands, invalid_islands)
        packer.send_log(LogType.STATUS, status_msg)

        if error_msg:
            packer.send_log(LogType.ERROR, "{} (check the selected islands)".format(error_msg))

        return RetCode.INVALID_ISLANDS

    def islands_for_topology_parsing(self):
        return self.cx.input_islands

    def parse_topology(self):

        islands_for_parsing = self.islands_for_topology_parsing()
        packer.parse_island_topology(islands_for_parsing)

    def send_tip(self, tip_msg):
        if self.config.disable_tips:
            return
        packer.send_log(LogType.INFO, "{} {}".format(self.TIP_HEADER, tip_msg), flags=LogFlags.PARSE)

    def init(self):

        if not self.config.skip_topology_parsing:
            self.parse_topology()

        in_g_scheme = self.cx.params[self.GROUPING_SCHEME_PARAM_NAME]

        if in_g_scheme is not None:
            group_iparam_desc = self.iparams_manager.iparam_desc(in_g_scheme['iparam_name'])
            if group_iparam_desc is None:
                raise InputError('Invalid island parameter passed in the grouping scheme')

            g_scheme = GroupingScheme(in_g_scheme, group_iparam_desc)

            for in_group in in_g_scheme['groups']:
                
                # group = GroupInfo(
                #     in_group['name'],
                #     in_group['num'],
                #     in_group['tdensity_cluster'],
                #     in_group['rotation_step'],
                #     in_group['pixel_margin'],
                #     target_boxes)

                group = GroupInfo(in_group)
                g_scheme.add_group(group)

            self.g_scheme = g_scheme

    def exec(self):

        ret_code = RetCode.NOT_SET
        try:
            self.init()
            self.pre_run()
            ret_code = self.run()
            ret_code = self.post_run(ret_code)

        except InputError as err:
            err_str = str(err)
            if err_str:
                packer.send_log(LogType.ERROR, err_str)
            packer.send_log(LogType.STATUS, 'Invalid operation input')
            return RetCode.INVALID_INPUT

        except InvalidTopologyExtendedError as err:
            return self.handle_invalid_islands(
                "Topology error",
                "Islands with invalid topology encountered",
                err.cause.invalid_islands)

        except InvalidIslandsExtendedError as err:
            return self.handle_invalid_islands(
                "Invalid islands",
                "Invalid islands encountered",
                err.cause.invalid_islands)

        except InvalidIslandsError as err:
            return self.handle_invalid_islands(
                "Invalid islands",
                None,
                err.cause.invalid_islands)

        except OpCancelledException:
            return RetCode.CANCELLED

        return ret_code

    def pre_run(self):
        pass
    
    def post_run(self, ret_code):
        return ret_code
