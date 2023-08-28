from agents.Entity import Entity
from agents.Kill_Chain_Agent import *
from agents.Quest_Agent import *
from agents.Commun_Agent import *
from utilities.CommonUtils import *

import math
import random
from math import *


# T:Terminal Agent 终端智能体
class T_Agent(Entity):
    def __init__(self):
        super(T_Agent, self).__init__()
        # 可移动
        self.movable = True
        # 可通信
        self.communicative = True
        # 通信范围
        self.commun_scope = 50
        # 速度
        self.vx = None
        self.vy = None
        # 加速度【暂时不用】
        self.ax = 0
        self.ay = 0
        # 物理故障状态（主要强调故障时的速度减缓）
        self.p_fault_state = False
        # 物理故障程度（与速度之间呈反比）
        self.p_fault_degree = 0


class ATT_T_Agent(T_Agent):
    def __init__(self):
        super(ATT_T_Agent, self).__init__()
        # 明确属性
        self.type = "attack"
        # 速率
        self.velocity = 15
        # 打击范围
        self.scope = 40
        # 单元隶属的决策单元
        self.mc_agent = None
        # 单元活动范围
        self.margin = []
        # 是否携带武器
        self.weapon_is_loaded = False
        # 携带武器
        self.weapon = []
        # 未传输到的待打击目标
        self.pre_target = []
        # 待打击目标
        self.target = []
        # 当前路径目标点
        self.destination = None
        # 最大携带任务数量
        self.max_target_load = 3
        # 工作模式
        # 模式0：初始模式
        # 模式1：在通信基站覆盖范围内活动
        # 模式2：在通信基站覆盖范围外活动
        self.workingmode = 0
        # 打击模式:
        # 模式1：选择待打击目标中最近的目标进行打击
        # 模式2：随机选择待打击目标清单中的目标
        self.attackmode = 1
        # 通信基站
        self.c_node = None
        # 是否与基站建立连接
        self.is_commu = False
        # 正在通信的基站
        self.c_node_connected_to = WLC_Node()
        # 即将通信的基站
        self.nearest_c_node = WLC_Node()
        # 打击智能体故障的概率
        self.attack_fault_rate = 0.8

    # 步进功能。
    def step(self, region, t):
        # 设置感知智能体故障
        if region.MA_state[3] == 0:
            self.scope = int(self.attack_fault_rate * 40)
        # 检查打击智能体与通信基站的通信
        self.commun_check(region)
        # 检查是否有可打击目标
        self.self_check()
        # 针对目前整理的目标集合进行决策。如果已经通过决策指定了目标，在发射导弹之前不会再次决策
        if self.destination == None:
            if self.workingmode == 1:
                self.decision_making(region)
            else:
                if self.is_commu:
                    # 向通信网络请求连接并生成通信请求, force_info
                    force_info_quest = C_Quest(
                        id=len(region.c_quests),
                        type=self.type,
                        info="force_info",
                        send=self,
                        receive=self.mc_agent,
                        start_time=t,
                    )
                    # 如果连的是同一个通信节点则通信请求直接完成
                    region.c_quests.append(force_info_quest)
        # 在对既定目标发射导弹，清空self.destination，为重新决策做准备
        else:
            self.missile_launch(region)
            if self.destination.is_locked_by_missile == True:
                self.destination = None
        # 对打击智能体进行导航
        self.navigation(region)

    # 判定是否发射武器
    def missile_launch(self, region):
        # 判定武器
        if (
            sqrt(
                pow(self.p_pos[0] - self.destination.p_pos[0], 2)
                + pow(self.p_pos[1] - self.destination.p_pos[1], 2)
            )
            < self.scope
            and self.destination.is_locked_by_missile == False
            and self.destination.is_assigned_to_attacker == True
            and self.destination.attackeraimat == self
        ):
            ###将目标派单给一个打击智能体。实施打击的判定条件为：
            # （1）目标被派给某一打击智能体,即enemy.attackeraimat = attacker, 并且enemy.is_assigned_to_attacker = True（两者意义相同，在多数情况下可以表示相同的情况，但暂时不做简并）
            # （2）目标尚未被导弹锁定，即enemy.is_locked_by_missile = False
            # （3）目标进入打击智能体的打击范围，即distance < attacker.scope
            # ps:当目标的状态is_locked_by_missile为True时，状态is_assigned_to_attacker必定为True
            for missile in self.weapon:
                if missile.target == None:
                    missile.p_pos = (self.p_pos[0], self.p_pos[1])
                    missile.target = self.destination
                    missile.lockon()
                    region.missile_launched.append(missile)
                    self.destination.is_locked_by_missile = True
                    break

    # 输入：region类别
    # 输出：该agent能连接到通信网络的通信节点
    def get_commun_node(self, region):
        commun_node = [
            c_node
            for c_node in region.C_Nodes
            if get_distance(self.p_pos, c_node.p_pos) < c_node.commun_scope
        ]
        well_commun_node = [
            cn
            for cn in commun_node
            if nx.has_path(
                region.c_network.G, cn.name, self.mc_agent.c_node_connected_to.name
            )
        ]
        return well_commun_node

    # 检查目前是否有可打击目标，即任务清单中是否有尚未被派单的目标。
    def self_check(self):
        # 更新target列表
        self.target = [
            target for target in self.target if target.is_locked_by_missile == False
        ]
        if len(self.target) == 0:
            self.workingmode = 0
        else:
            for target in self.target:
                if target.is_assigned_to_attacker == False:
                    self.workingmode = 1
                    return
                else:
                    self.workingmode = 0

    # 与通信基站的通信检查。
    def commun_check(self, region):
        # 通信范围内是否有通信节点
        if self.get_commun_node(region):
            self.is_commu = True
            self.c_node = self.get_commun_node(region)
            sorted_c_node = sorted(
                self.c_node, key=lambda obj: get_distance(self.p_pos, obj.p_pos)
            )
            self.c_node_connected_to = sorted_c_node[0]
            self.nearest_c_node = WLC_Node()
        # 如果无法连入通信网络，则更新距离最近的通信节点
        else:
            self.is_commu = False
            self.c_node = None
            # 获取所有存在能接入指控中心的通信节点
            mc_c_nodes = [
                cn
                for cn in region.C_Nodes
                if (cn.p_pos[0] >= self.mc_agent.margin[0])
                and (cn.p_pos[1] >= self.mc_agent.margin[1])
                and (cn.p_pos[0] <= self.mc_agent.margin[2])
                and (cn.p_pos[1] <= self.mc_agent.margin[3])
                and (cn.name != self.mc_agent.c_node_connected_to.name)
            ]
            well_c_nodes = [
                cn
                for cn in mc_c_nodes
                if nx.has_path(
                    region.c_network.G, cn.name, self.mc_agent.c_node_connected_to.name
                )
            ]
            # 判定通信节点的情况
            if well_c_nodes:
                # 构建所有C_node的坐标集合
                all_C_Node_xy = [
                    (c_node.p_pos[0], c_node.p_pos[1]) for c_node in well_c_nodes
                ]
                # 构建kd-tree 实现快速检索
                tree = KDTree(all_C_Node_xy)
                # 查询最近点的索引
                _, min_index = tree.query([(self.p_pos[0], self.p_pos[1])])
                self.nearest_c_node = well_c_nodes[min_index[0]]
            else:
                self.nearest_c_node = WLC_Node()
            self.c_node_connected_to = WLC_Node()

    # 决策功能
    def decision_making(self, region):
        if self.attackmode == 1:
            distance_list = [
                (
                    target.name,
                    math.sqrt(
                        (target.p_pos[0] - self.p_pos[0]) ** 2
                        + (target.p_pos[1] - self.p_pos[1]) ** 2
                    ),
                )
                for target in self.target
                if target.is_assigned_to_attacker == False
            ]
            sorted_distance = sorted(distance_list, key=lambda x: x[1])
            for target in self.target:
                if sorted_distance[0][0] == target.name:
                    self.destination = target
                    self.destination.is_assigned_to_attacker = True
                    self.destination.attackeraimat = self
                    # 分派后的目标阶段变为stage=3 火力打击
                    switch_kill_chain = [
                        kc for kc in region.kill_chains if kc.name == target.name
                    ][0]
                    switch_kill_chain.stage = 3
        elif self.attackmode == 2:
            random_list = [
                target
                for target in self.target
                if target.is_assigned_to_attacker == False
            ]
            self.destination = random.choice(random_list)
            self.destination.is_assigned_to_attacker = True
            self.destination.attackeraimat = self

    # 导航功能。其主要逻辑如下
    # （1）确定当前打击目标后，目标具有最高优先级，导航会令打击智能体朝目标移动，直至目标进入打击智能体的射程覆盖范围；
    # （2）如未确定打击目标，判定打击智能体是否在通信基站的通信范围内：
    #     1）若打击智能体在通信基站的通信范围内，打击智能体停止，等待新的打击任务
    #     2）若打击智能体不在通信基站的通信范围内，打击智能体朝最近的打击智能体移动
    def navigation(self, region):
        # 地图边缘
        # 单元活动边界
        xmin, ymin, xmax, ymax = self.margin
        if self.destination:
            # 如果此时目标已在射程范围内，则原地不动
            # 若不在射程范围内，则设置移动速度
            d = get_distance(self.destination.p_pos, self.p_pos)
            if d < self.scope:
                self.vx = 0
                self.vy = 0
            else:
                theta = math.atan2(
                    self.destination.p_pos[1] - self.p_pos[1],
                    self.destination.p_pos[0] - self.p_pos[0],
                )
                self.vx = self.velocity * math.cos(theta)
                self.vy = self.velocity * math.sin(theta)
                # print(self.destination.p_pos[0], self.destination.p_pos[1])
        else:
            if self.is_commu:
                self.vx = 0
                self.vy = 0
            else:
                if self.nearest_c_node.name == "None":
                    self.vx = 0
                    self.vy = 0
                else:
                    theta = math.atan2(
                        self.nearest_c_node.p_pos[1] - self.p_pos[1],
                        self.nearest_c_node.p_pos[0] - self.p_pos[0],
                    )
                    self.vx = self.velocity * math.cos(theta)
                    self.vy = self.velocity * math.sin(theta)

        # 计算打击智能体的新位置
        update_x = self.p_pos[0] + self.vx * region.dt
        update_y = self.p_pos[1] + self.vy * region.dt
        self.p_pos = [update_x, update_y]
        # 靠近地图边缘的边界处理
        if self.p_pos[0] < xmin:
            self.p_pos[0] = xmin
            self.vx = -self.vx
        elif self.p_pos[0] > xmax:
            self.p_pos[0] = xmax
            self.vx = -self.vx
        if self.p_pos[1] < ymin:
            self.p_pos[1] = ymin
            self.vy = -self.vy
        elif self.p_pos[1] > ymax:
            self.p_pos[1] = ymax
            self.vy = -self.vy
