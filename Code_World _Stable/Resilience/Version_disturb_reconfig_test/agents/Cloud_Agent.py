from agents.Entity import Entity
from agents.Kill_Chain_Agent import *
from utilities.CommonUtils import *
from utilities.AuctionUtils import *
from agents.Quest_Agent import *

import math
from scipy.spatial import KDTree


# MC:Margin-Cloud Agent 中心云智能体
class CC_Agent(Entity):
    def __init__(self):
        super(CC_Agent, self).__init__()
        # 明确属性
        self.type = "cc"
        # 中心云管辖的边缘云
        self.MC_Agents = []
        # 决策间隙
        self.cc_t = 50
        # 备用侦察单元
        self.backup_scout_agent = []
        # 备用打击单元
        self.backup_attack_agent = []
        # 可临时构建的通信网络链路数量
        self.backup_link_num = 42
        # 重构阈值:区域侦察覆盖率
        self.reconfig_threshold_scout = 0.7
        # 重构阈值:感知目标响应率
        self.reconfig_threshold_alloc = 20
        # 重构阈值:通信需求处理率
        self.reconfig_threshold_commun = 0.6
        # 存储每类是否进行诊断的信息
        self.diagnosis_mark_list = {"scout": False, "alloc": False, "commun": False}
        # 诊断智能体是否开启的判定
        self.diagnosis_mark = False
        # 评估智能体能故障的概率
        self.eval_fault_rate = 0.8
        # 诊断智能体故障的概率
        self.diagn_fault_rate = 0.8

    def step(self, region, t):
        if t % self.cc_t == 0:
            # 评估智能体
            self.evaluation(region)
            # 更新诊断智能体开启判定
            for _, v in self.diagnosis_mark_list.items():
                if v:
                    self.diagnosis_mark = True
            # 如果评估智能体判定某一指标达到重构阈值，则进入诊断智能体
            if self.diagnosis_mark:
                # 诊断智能体
                self.diagnosis(region)
            # 结束后诊断判定重新设置为False等待下一轮
            self.diagnosis_mark = False

    def evaluation(self, region):
        # 设置评估智能体故障
        if region.MA_state[4] == 0:
            self.reconfig_threshold_scout = (
                self.reconfig_threshold_scout * self.eval_fault_rate
            )
            self.reconfig_threshold_alloc = int(
                self.reconfig_threshold_alloc * self.eval_fault_rate
            )
            self.reconfig_threshold_commun = (
                self.reconfig_threshold_commun * self.eval_fault_rate
            )
        # 收集杀伤网的感知效率：即得到整个体系目前区域侦察覆盖率
        # 如果区域侦察覆盖率低于阈值，则进入诊断阶段
        real_grid = [g for g in region.turtles if g.always_observed == False]
        locked_grid = [g for g in real_grid if g.is_observed == True]
        if len(locked_grid) / len(real_grid) < self.reconfig_threshold_scout:
            self.diagnosis_mark_list["scout"] = True

        # 收集杀伤网的决策效率：即得到整个体系目前感知目标的响应率
        # 如果感知目标响应率低于阈值，则进入诊断阶段
        local_unalloc_nums = [ag.unalloc_enemy_num for ag in self.MC_Agents]
        local_alloc_nums = [ag.alloc_enemy_num for ag in self.MC_Agents]
        decide_respond_rate = sum(local_alloc_nums)
        if decide_respond_rate < self.reconfig_threshold_alloc:
            self.diagnosis_mark_list["alloc"] = True

        # 收集通信网的需求处理效率：即正在处理的请求（state==1）/未完成请求规模（state<2）
        # 如果通信网的需求处理效率低于阈值，则进入诊断阶段
        unfinished_quest = [q for q in region.c_quests if q.state < 2]
        loading_quest = [q for q in region.c_quests if q.state == 1]
        if len(unfinished_quest) == 0:
            quest_load_rate = 0
        else:
            quest_load_rate = len(loading_quest) / len(unfinished_quest)
        if quest_load_rate < self.reconfig_threshold_commun:
            self.diagnosis_mark_list["commun"] = True
        return

    # 诊断智能体
    def diagnosis(self, region):
        # 设置诊断智能体故障
        if region.MA_state[5] == 0:
            if random.random() < self.diagn_fault_rate:
                if self.diagnosis_mark_list["commun"]:
                    self.commun_reconfig(region)
                    return
                else:
                    for type, mark in self.diagnosis_mark_list.items():
                        if mark:
                            if type == "scout":
                                self.scount_reconfig(region)
                            elif type == "alloc":
                                self.alloc_reconfig(region)
                            elif type == "commun":
                                self.commun_reconfig(region)
                            else:
                                pass
                    return

    def scount_reconfig(self, region):
        scount_sorted_mc_agent = sorted(self.MC_Agents, key=lambda obj: obj.scout_rate)
        # 获取此刻最需要感知单元补充的区域的边缘云
        re_scout_mc_agent = scount_sorted_mc_agent[0]
        # 获取此时未使用的备份感知单元数量
        unused_backup_scout_agent = [
            agent for agent in self.backup_scout_agent if agent.used == False
        ]
        # 判断有无剩余备份感知单元，无则pass，有则派遣一个单元加入
        if len(unused_backup_scout_agent) == 0:
            pass
        else:
            unused_backup_scout_agent[0].margin = re_scout_mc_agent.margin
            unused_backup_scout_agent[0].mc_agent = re_scout_mc_agent
            unused_backup_scout_agent[0].used = True
            region.OBS_T_Agents.append(unused_backup_scout_agent[0])
            re_scout_mc_agent.OBS_T_Agents.append(unused_backup_scout_agent[0])

    def alloc_reconfig(self, region):
        alloc_sorted_mc_agent = sorted(self.MC_Agents, key=lambda obj: obj.alloc_rate)
        # 获取此刻最需要打击单元补充的区域的边缘云
        rec_alloc_mc_agent = alloc_sorted_mc_agent[0]
        # 获取此时未使用的备份打击单元数量
        unused_backup_attack_agent = [
            agent for agent in self.backup_attack_agent if agent.used == False
        ]
        # 判断有无剩余备份打击单元，无则pass，有则派遣一个单元加入
        if len(unused_backup_attack_agent) == 0:
            pass
        else:
            unused_backup_attack_agent[0].margin = rec_alloc_mc_agent.margin
            unused_backup_attack_agent[0].mc_agent = rec_alloc_mc_agent
            unused_backup_attack_agent[0].used = True
            region.ATT_Agents.append(unused_backup_attack_agent[0])
            rec_alloc_mc_agent.ATT_Agents.append(unused_backup_attack_agent[0])

    def commun_reconfig(self, region):
        # 计算当前通信网络的最大负载量为权重的加权度，加权度最小的节点优先与离他最近的节点建立连边
        # 总共可维护的临时通信连边数量为20, 每次可临时构建2条链路
        if self.backup_link_num <= 0:
            return
        for mc_agent in self.MC_Agents:
            # 计算加权度 字典形式存储
            weighted_degree_dict = dict(
                region.c_network.G.degree(weight="Mission_Load_Max")
            )
            sorted_mc_cnodes = sorted(
                region.C_Nodes, key=lambda obj: get_distance(obj.p_pos, mc_agent.p_pos)
            )
            # 总共每个区域下恢复1条
            relink_max = 0
            num = 0
            while True:
                if (
                    relink_max == 2
                    or num == len(sorted_mc_cnodes)
                    or self.backup_link_num <= 0
                ):
                    break
                c_node = sorted_mc_cnodes[num]
                # 获取邻近节点
                near_c_nodes = [
                    c
                    for c in region.C_Nodes
                    if get_distance(c.p_pos, c_node.p_pos) > 0
                    and get_distance(c.p_pos, c_node.p_pos) < 55
                ]
                # 获取存在连边邻近节点集合不存在连边邻近节点集
                link_c_nodes = []
                unlink_c_nodes = []
                for near_node in near_c_nodes:
                    if region.c_network.G.has_edge(c_node.name, near_node.name):
                        link_c_nodes.append(near_node)
                    else:
                        unlink_c_nodes.append(near_node)
                # 判断该节点到邻近节点是否不存在连边，优先给无连边且邻近节点加权度不为0的节点建立连边
                if unlink_c_nodes:
                    # 排序优先找加权度大的（傍大款）
                    sorted_unlink_nodes = sorted(
                        unlink_c_nodes,
                        key=lambda obj: weighted_degree_dict[obj.name],
                        reverse=True,
                    )
                    select_node = sorted_unlink_nodes[0]
                    # 建立连边
                    rec_edge = (c_node.name, select_node.name)
                    region.c_network.G.add_edges_from([rec_edge])
                    # 添加链路属性
                    region.c_network.G.edges[rec_edge]["Total_Span"] = 1
                    region.c_network.G.edges[rec_edge]["Mission_Load_Max"] = 5
                    region.c_network.G.edges[rec_edge]["Mission_Load_Real"] = 0
                    region.c_network.G.edges[rec_edge]["Mission_Load_Rest"] = 5
                    region.c_network.G.edges[rec_edge]["Fault"] = False
                    region.c_network.G.edges[rec_edge]["Reconfig"] = True
                    # 更新
                    relink_max += 1
                    self.backup_link_num -= 1
                else:
                    # 如果到所有邻近节点都存在连边，则下一位
                    num += 1
                    continue
