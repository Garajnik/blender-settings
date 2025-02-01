# from scripted_pipeline import 
from pack_utils import PackScenario
from uvpm_core import (Stage,
                     PackTask,
                     StageParams,
                     StdStageTarget,
                     InputError)
from utils import eprint

from collections import defaultdict


class GroupCluster:

    def __init__(self):
        self.groups = []
        self.tdensity_cluster_ids = set()

    def add_group(self, group):
        self.groups.append(group)
        self.tdensity_cluster_ids.add(group.tdensity_cluster)
                
    def depends_on(self, other_group):
        if other_group.tdensity_cluster in self.tdensity_cluster_ids:
            return True

        for group in self.groups:
            if group.get_stage_target().intersects(other_group.get_stage_target()):
                return True
            
        return False
    
    def merge(self, other):
        self.groups += other.groups
        self.tdensity_cluster_ids = self.tdensity_cluster_ids.union(other.tdensity_cluster_ids)
                

class Scenario(PackScenario):

    GROUP_AREA_TOLERANCE = 1e-5

    def run(self):

        self.pack_params.groups_together = self.g_scheme.groups_together
        self.pack_params.grouping_compactness = self.g_scheme.group_compactness
        self.pack_params.pack_to_single_box = self.g_scheme.pack_to_single_box

        group_clusters = []

        for group in self.g_scheme.groups:

            if group.islands is None:
                continue

            target_indicies = []

            for idx, g_cluster in enumerate(group_clusters):
                if g_cluster.depends_on(group):
                    target_indicies.append(idx)
                    
            if len(target_indicies) == 0:
                target_indicies.append(len(group_clusters))
                group_clusters.append(GroupCluster())

            while len(target_indicies) > 1:
                group_clusters[target_indicies[0]].merge(group_clusters[target_indicies[-1]])
                del group_clusters[target_indicies[-1]]
                del target_indicies[-1]

            group_clusters[target_indicies[0]].add_group(group)

        # eprint('len(group_clusters): ' + str(len(group_clusters)))
        if len(group_clusters) == 0:
            raise InputError("No group found on input")
        
        tdensity_tip_sent = False
        order_tip_sent = False

        for g_cluster in group_clusters:

            if not tdensity_tip_sent and (len(g_cluster.tdensity_cluster_ids) > 1):
                first_group = g_cluster.groups[0]
                second_group = None
                for group in g_cluster.groups[1:]:
                    if group.tdensity_cluster != first_group.tdensity_cluster:
                        second_group = group
                        break

                assert second_group is not None

                self.send_tip('note that packing two groups into the same UV space with independent texel density may significantly increase packing time')
                self.send_tip('if the operation takes too long, consider packing with the same texel density')
                self.send_tip('groups packed with independent texel density: {}, {}'.format(first_group.name, second_group.name))
                tdensity_tip_sent = True

            task = PackTask(0, self.pack_params)

            sorted_groups = sorted(g_cluster.groups, key=lambda g: g.create_id)

            for idx, group in enumerate(sorted_groups):

                poly_array = group.get_stage_target().to_poly_array()
                if not order_tip_sent:
                    for other_group in sorted_groups[0:idx]:
                        other_poly_array = other_group.get_stage_target().to_poly_array()
                        if (poly_array.area() + self.GROUP_AREA_TOLERANCE) < other_poly_array.area() and poly_array.within(other_poly_array):
                            self.send_tip('packing coverage may not be optimal if a group with smaller target boxes is packed after a group with larger target boxes')
                            self.send_tip('consider changing the packing order - swap the following groups on the list: {}, {}'.format(other_group.name, group.name))
                            order_tip_sent = True
                            break

                stage = group.to_stage()
                stage.static_islands = self.static_islands
                self.add_stage_to_task(task, stage)

            self.pack_manager.add_task(task)

        return self.pack_manager.pack()
