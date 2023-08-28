from agents.Entity import Entity
from agents.Kill_Chain_Agent import *
from agents.Commun_Agent import *
from agents.Quest_Agent import *
from utilities.CommonUtils import *

import random
from scipy.spatial import KDTree
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


# T:Terminal Agent 侦察终端智能体
class OBS_T_Agent(T_Agent):
    def __init__(self):
        super(OBS_T_Agent, self).__init__()
        # 明确属性
        self.type = "scout"
        # 侦察功能是否正常
        self.visible = True
        # 速度
        self.velocity = 15
        # 侦察探测范围
        self.obs_scope = 30
        # 单元隶属的决策单元
        self.mc_agent = None
        # 单元活动范围
        self.margin = []
        # 侦察目标 获取目标的名称（待定）以及位置坐标
        self.Enemies = []
        # 上传目标
        self.quest_Enemies = []
        # 侦察模式 3种模式：1=自由探索，2=指定位置机动，3=目标信息回传
        self.mode = 1
        # 自由探索模式下的探索次数 设置为5
        self.free_time = 5
        # 是否处在通信节点通信范围内
        self.is_commu = False
        # 所处通信范围内的通信节点
        self.c_node = None
        # 在通信范围内，最近的连入通信节点
        self.c_node_connected_to = WLC_Node()
        # 若不在通信范围内，最近他通信节点的坐标
        self.nearest_c_node_xy = (0, 0)
        # 若不在通信范围内，最近的通信节点
        self.nearest_c_node = WLC_Node()
        # 是否处于通信等待状态
        self.commun_waiting = False
        # 等待时间
        self.commun_waiting_time = 0
        # 指控单元反馈的机动turtle
        self.t_area = None
        # 感知智能体故障的概率
        self.perception_fault_rate = 0.8

    # 侦察终端智能体整体更新：
    def step(self, region, t):
        # 设置感知智能体故障
        if region.MA_state[0] == 0:
            self.obs_scope = int(self.perception_fault_rate * 30)
        # 更新
        if self.commun_waiting:
            # 代表指控单元回传的通信消息到达，结束通信等待状态
            if self.t_area != None:
                if self.t_area != 0:
                    self.mode = 2
                    self.commun_waiting = False
                    # 目标区块的坐标
                    tx, ty = list(self.t_area.center)
                    # 更新速度
                    self.update_v(tx, ty)
                    self.t_area.obs_lock = True
                else:
                    self.mode = 1
                    self.commun_waiting = False
                    # 原地待命
                    self.vx = 0
                    self.vy = 0
                    self.t_area = None
            # 代表指控单元回传的通信消息未到达，继续等待
            # 后续设置等待截断时间
            else:
                if self.commun_waiting_time == 10:
                    self.mode = 1
                    self.commun_waiting = False
                    self.commun_waiting_time = 0
                else:
                    self.commun_waiting_time += 1
        else:
            # 更新agent是否连入通信网络
            self.update_communication(region)
            # 更新视野范围内的目标
            self.update_enemy(region, t)
            # 根据不同模式更新agent的速度方向
            if self.mode == 1:
                self.update_mode_1(region, t)
            elif self.mode == 2:
                self.update_mode_2(region)
            else:
                self.update_mode_3()
            # 判断是否连入通信网络，且是否存储有目标信息，且对应指控单元是否能通信，若满足条件，上传给指控单元
            # 向通信网络请求连接并生成通信请求, mobile_quest
            if self.is_commu:
                if self.Enemies:
                    if self.mc_agent.is_commu:
                        enemy_info_quest = C_Quest(
                            id=len(region.c_quests),
                            type=self.type,
                            info="enemy_info",
                            send=self,
                            receive=self.mc_agent,
                            start_time=t,
                        )
                        enemy_info_quest.data = self.Enemies.copy()
                        self.Enemies = []
                        # 如果连的是同一个通信节点则通信请求直接完成
                        region.c_quests.append(enemy_info_quest)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            # 更新位置和turtles信息
            self.update_pos_and_turtles(region, t)

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

    # 输入：region类别
    # 输出：感知单元通信范围内的目标
    def get_ocupy_enemy(self, region):
        ocupy_enemies = [
            enemy
            for enemy in region.Enemies
            if get_distance(self.p_pos, enemy.p_pos) < self.obs_scope
        ]
        return ocupy_enemies

    # 输入：region类别
    # 输出：按照网格中心覆盖turtle的原则
    def get_ocupy_turtle(self, region):
        ocupy_turtles = [
            turtle
            for turtle in region.turtles
            if get_distance(self.p_pos, turtle.center) < self.obs_scope
        ]
        return ocupy_turtles

    # 输入：region类别
    # 输出：按照网格中心覆盖turtle的原则
    def get_ocupy_turtle_by_edge_node(self, region):
        ocupy_turtles = [
            turtle
            for turtle in region.turtles
            if (get_distance(self.p_pos, turtle.point[0]) < self.obs_scope)
            & (get_distance(self.p_pos, turtle.point[1]) < self.obs_scope)
            & (get_distance(self.p_pos, turtle.point[2]) < self.obs_scope)
            & (get_distance(self.p_pos, turtle.point[3]) < self.obs_scope)
        ]
        return ocupy_turtles

    # 获取实时侦察终端智能体的侦察范围
    def get_cur_range(self):
        ob_x_range = [
            self.p_pos[0] - self.obs_scope,
            self.p_pos[0] + self.obs_scope,
        ]
        ob_y_range = [
            self.p_pos[1] - self.obs_scope,
            self.p_pos[1] + self.obs_scope,
        ]
        return ob_x_range, ob_y_range

    # 更新节点速度vx,vy
    def update_v(self, tx, ty):
        # 计算朝向的方向
        sx, sy = self.p_pos[0], self.p_pos[1]
        theta = atan2(ty - sy, tx - sx)
        # 更新速度【需调整】
        self.vx = cos(theta) * self.velocity
        self.vy = sin(theta) * self.velocity

    # 更新是否在通信节点通信范围内
    def update_communication(self, region):
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

    # 更新智能体位置和范围内turtles
    def update_pos_and_turtles(self, region, t):
        # 单位时间
        dt = region.dt
        # 单元活动边界
        xmin, ymin, xmax, ymax = self.margin
        # 更新位置
        update_x = self.p_pos[0] + self.vx * dt
        update_y = self.p_pos[1] + self.vy * dt
        self.p_pos = [update_x, update_y]
        # 靠近地图边缘的边界处理
        if self.p_pos[0] < xmin + self.obs_scope:
            self.p_pos[0] = xmin + self.obs_scope
            self.vx = -self.vx
        elif self.p_pos[0] > xmax - self.obs_scope:
            self.p_pos[0] = xmax - self.obs_scope
            self.vx = -self.vx
        if self.p_pos[1] < ymin + self.obs_scope:
            self.p_pos[1] = ymin + self.obs_scope
            self.vy = -self.vy
        elif self.p_pos[1] > ymax - self.obs_scope:
            self.p_pos[1] = ymax - self.obs_scope
            self.vy = -self.vy
        # 更新turtles是否被侦察的信息
        obs_recon_turtles = self.get_ocupy_turtle(region)
        for turtle in obs_recon_turtles:
            if turtle.is_observed:
                pass
            else:
                turtle.is_observed = True
                turtle.latest_ob_t = t

    def update_enemy(self, region, t):
        obs_ocup_enemies = self.get_ocupy_enemy(region)
        unlock_enemies = [enemy for enemy in obs_ocup_enemies if enemy.locked == False]
        if len(unlock_enemies) == 0:
            pass
        else:
            # 将target添加到侦察agent的存储里
            self.Enemies.extend(unlock_enemies)
            # 更新target被锁定状态，对每个目标初始化一个杀伤链
            for enemy in unlock_enemies:
                enemy.locked = True
                kill_chain = Kill_Chain()
                kill_chain.name = enemy.name
                kill_chain.enemy = enemy
                kill_chain.stage = 1
                kill_chain.s_time = t
                region.kill_chains.append(kill_chain)

    # mode=1 即自由探索的逻辑
    def update_mode_1(self, region, t):
        # 侦察范围内的turtles
        obs_ocup_turtles = self.get_ocupy_turtle_by_edge_node(region)
        # 侦察范围内未侦察到的turtle带来的Force
        # 返回侦察范围内未被侦察的turtle
        unrecon_turtles = [
            turtle for turtle in obs_ocup_turtles if turtle.is_observed == False
        ]
        # 如果unrecon_turtles不为空
        if len(unrecon_turtles) != 0:
            self.free_time = 5
            # 1.3 随机选取一个未被侦察的turtle
            luckey_turtle = random.choice(unrecon_turtles)
            tx, ty = luckey_turtle.center[0], luckey_turtle.center[1]
            # 更新速度
            self.update_v(tx, ty)
            return
        # 如果unrecon_turtles为空
        else:
            # 5次自由探索失败，则寻求联络
            if (self.mode == 1) & (self.free_time != 0):
                self.free_time -= 1
            else:
                # 单元能接入通信网络
                if self.is_commu:
                    if self.mc_agent.is_commu:
                        # 重置目标区块
                        self.t_area = None
                        # 向通信网络请求连接并生成通信请求, mobile_quest
                        mobile_quest = C_Quest(
                            id=len(region.c_quests),
                            type=self.type,
                            info="mobile_quest",
                            send=self,
                            receive=self.mc_agent,
                            start_time=t,
                        )
                        # 如果连的是同一个通信节点则通信请求直接完成
                        region.c_quests.append(mobile_quest)
                        self.commun_waiting = True
                        # 原地待命
                        self.vx = 0
                        self.vy = 0
                        return
                    else:
                        # 原地待命
                        self.vx = 0
                        self.vy = 0
                else:
                    if self.nearest_c_node.name == "None":
                        self.vx = 0
                        self.vy = 0
                    else:
                        tx, ty = (
                            self.nearest_c_node.p_pos[0],
                            self.nearest_c_node.p_pos[1],
                        )
                        self.update_v(tx, ty)
                    self.mode = 3
                    return

    # mode=2, 即接收到机动区块后机动过程
    def update_mode_2(self, region):
        # 实时侦察区域
        obs_recon_turtles = self.get_ocupy_turtle(region)
        # 判断是否到达目标区块，或者中途目标区块已被侦察
        if self.t_area in obs_recon_turtles:
            self.t_area.obs_lock = False
            self.mode = 1
            self.free_time = 5
        elif self.t_area.is_observed:
            self.t_area.obs_lock = False
            self.mode = 1
            self.free_time = 5
        else:
            pass

    # mode=3, 即接入通信网络的过程
    def update_mode_3(self):
        # 判断是否进入通信网络
        if self.is_commu:
            self.mode = 1
        else:
            pass
