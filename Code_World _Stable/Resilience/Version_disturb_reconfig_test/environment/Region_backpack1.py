from utilities.CommonUtils import *
from utilities.PartitionUtils import *
from environment.Turtle import *
from agents.Enemy_Agent import *

from math import *
import numpy as np
import pandas as pd
import networkx as nx


"""
场景对象类定义，包括：
基本单元块:turtle
运行区域块:Region
运行区域块需要通过初始化生成基本单元块，通过划分的方式
"""


# RegionAgent
class Region(object):
    def __init__(self):
        # 名称
        self.name = ""
        # 类别
        self.type = ""
        # simulation timestep
        self.dt = 0.1
        # 区域xy平面信息（存放四个定点）
        self.xy = None
        # 区域z轴（高度）
        self.z = None
        # 区域内划分的turtles
        self.turtles = []
        # 区域内的通信节点C_Node
        self.C_Nodes = []
        # 区域内的侦察终端T_Agent
        self.OBS_T_Agents = []
        # 区域内的边缘云MC_Agent
        self.MC_Agents = []
        # 区域内的打击智能体
        self.ATT_Agents = []
        # 区域内的敌方目标
        self.Enemies = []
        # 区域内的敌方携带导弹
        self.enemy_missile_standby = []
        # 区域内的敌方发射导弹
        self.enemy_missile_launched = []
        # 区域内的我方携带导弹
        self.missile_standby = []
        # 区域内的我方发射导弹
        self.missile_launched = []
        # 杀伤链
        self.kill_chains = []
        # 区域内的通信网络
        self.c_network = None
        # 区域内所有通信请求
        self.c_quests = []

    # 生成用于平面绘制的参数（暂时弃用）
    def region_plot_slide(self):
        x_list = []
        y_list = []
        for xy in self.xy:
            x = list(xy)[0]
            y = list(xy)[1]
            x_list.append(x)
            y_list.append(y)
        xx, yy = np.meshgrid([max(x_list), min(x_list)], [max(y_list), min(y_list)])
        zz = np.zeros(xx.shape) + self.z

        return xx, yy, zz

    # 初始化网格，num为所需初始化网格的数量
    def initial_turtles(self, num):
        QP = QuadPartitioner_by_coord()
        partitions = QP.get_partitions(num, self.xy)
        for i, rows in enumerate(partitions):
            for j, cell in enumerate(rows):
                turtle = Turtle()
                turtle.name = "grid_%d%d" % (i, j)
                turtle.x = [cell[0][0], cell[2][0]]
                turtle.y = [cell[0][1], cell[1][1]]
                turtle.center = (
                    0.5 * (cell[2][0] + cell[0][0]),
                    0.5 * (cell[1][1] + cell[0][1]),
                )
                self.turtles.append(turtle)
                turtle.point = cell
                turtle.z = self.z

    # 通过范围调取grid列表 center为判定
    def get_turtles_by_range(self, x_range, y_range):
        return [
            grid
            for grid in self.turtles
            if (
                (x_range[0] <= grid.center[0])
                and (x_range[1] >= grid.center[0])
                and (y_range[0] <= grid.center[1])
                and (y_range[1] >= grid.center[1])
            )
        ]

    # 通过范围调取target列表
    def get_enemies_by_range(self, x_range, y_range):
        return [
            enemy
            for enemy in self.Enemies
            if (
                (x_range[0] <= enemy.p_pos[0])
                and (x_range[1] >= enemy.p_pos[0])
                and (y_range[0] <= enemy.p_pos[1])
                and (y_range[1] >= enemy.p_pos[1])
            )
        ]

    # 通过范围调取grid列表 边缘节点为判定
    def get_turtles_by_range_edge_node(self, x_range, y_range):
        return [
            grid
            for grid in self.turtles
            if (
                (x_range[0] <= grid.x[0])
                and (x_range[1] >= grid.x[0])
                and (y_range[0] <= grid.y[0])
                and (y_range[1] >= grid.y[0])
            )
            or (
                (x_range[0] <= grid.x[1])
                and (x_range[1] >= grid.x[1])
                and (y_range[0] <= grid.y[0])
                and (y_range[1] >= grid.y[0])
            )
            or (
                (x_range[0] <= grid.x[0])
                and (x_range[1] >= grid.x[0])
                and (y_range[0] <= grid.y[1])
                and (y_range[1] >= grid.y[1])
            )
            or (
                (x_range[0] <= grid.x[1])
                and (x_range[1] >= grid.x[1])
                and (y_range[0] <= grid.y[1])
                and (y_range[1] >= grid.y[1])
            )
        ]

    # 通过坐标调取单个grid
    def get_turtles_by_node(self, x, y):
        return [
            grid
            for grid in self.turtles
            if (grid.x[0] <= x)
            and (grid.x[1] >= x)
            and (grid.y[0] <= y)
            and (grid.y[1] >= y)
        ]

    # 生成计算指标数据
    def data_generation(self):
        # 杀伤链闭合规模(没有侦察单元的收尾)
        close_kill_chains = [kc for kc in self.kill_chains if kc.close == True]
        close_kc_num = len(close_kill_chains)

        # 杀伤链闭合时间
        if len(close_kill_chains) == 0:
            close_mean_time = 0
        else:
            close_times = [kc.close_time for kc in close_kill_chains]
            close_mean_time = 0.1 * sum(close_times) / len(close_times)

        # 目标感知效率
        totoal_locked_enemies = [e for e in self.Enemies if e.locked == True]
        locked_num = len(totoal_locked_enemies)

        # 存活目标感知率
        alive_locked_enemies = [
            e for e in self.Enemies if e.locked == True and e.alive == True
        ]
        alive_enemies = [e for e in self.Enemies if e.alive == True]
        target_cover_rate = len(alive_locked_enemies) / len(alive_enemies)

        # 区域侦察覆盖率
        locked_grid = [g for g in self.turtles if g.is_observed == True]
        grid_cover_rate = len(locked_grid) / len(self.turtles)

        # 识别率（暂无）

        # 感知目标分配率
        alive_alloc_enemies = [
            e
            for e in self.Enemies
            if e.is_allocated == True and e.locked == True and e.alive == True
        ]
        target_respond_rate = len(alive_alloc_enemies) / len(alive_locked_enemies)

        # 决策响应效率(单位时间内响应数量)
        assigned_enemies = [
            e for e in self.Enemies if e.is_assigned_to_attacker == True
        ]
        assigned_num = len(assigned_enemies)

        # 目标打击效率
        destroyed_enemies = [enemy for enemy in self.Enemies if enemy.alive == False]
        destroyed_num = len(destroyed_enemies)

        # 通信完成效率
        finish_quests = [q for q in self.c_quests if q.state == 3]
        finish_quest_num = len(finish_quests)

        # 通信链路使用比例
        load_link = [
            (n1, n2)
            for n1, n2, data in self.c_network.G.edges(data=True)
            if data["Mission_Load_Real"] > 0
        ]
        load_link_rate = len(load_link) / len(self.c_network.G.edges)

        # 通信过载比例
        load_max_link = [
            (n1, n2)
            for n1, n2, data in self.c_network.G.edges(data=True)
            if data["Mission_Load_Real"] == 5
        ]
        if len(load_link) == 0:
            load_max_link_rate = 0
        else:
            load_max_link_rate = len(load_max_link) / len(load_link)

        mean_attr = [
            close_kc_num,
            close_mean_time,
            target_cover_rate,
            grid_cover_rate,
            target_respond_rate,
            load_link_rate,
            load_max_link_rate,
        ]
        differ_attr = [locked_num, assigned_num, destroyed_num, finish_quest_num]
        return mean_attr, differ_attr

    # 新增目标
    def add_enemy(self, add_num):
        # 新增单元
        # 补充目标, 每0.1s补充2个目标
        for i in range(add_num):
            dice = random.random()
            if dice < 0.5:
                pass
            else:
                # 当前个数
                old_enemy_num = len(self.Enemies)
                # 选择边界外围除出去后，未被侦察的区域
                sg = self.get_turtles_by_range([30, 370], [30, 370])
                unobserved_turtles = [grid for grid in sg if grid.is_observed == False]
                if unobserved_turtles == 0:
                    pass
                else:
                    # 随机选择一个unobserved_turtle

                    select_gird = random.choice(unobserved_turtles)
                    enemies_xy = [
                        random.uniform(select_gird.x[0], select_gird.x[1]),
                        random.uniform(select_gird.y[0], select_gird.y[1]),
                    ]
                    # 补充目标
                    num_enemies = 1
                    add_enemies = [Enemy() for i in range(num_enemies)]
                    for i, enemy in enumerate(add_enemies):
                        enemy.name = "T_%d" % (old_enemy_num + i)
                        enemy.p_pos = (enemies_xy[0], enemies_xy[1])
                        select_gird.targets.append(enemy)
                    self.Enemies.extend(add_enemies)

    # 每一步下的所有智能体动作更新
    def step(self, t):
        # turtle 更新turtle的被侦察状态
        for turtle in self.turtles:
            turtle.update_observe(self, t)

        # 每个指控单元更新
        for mc_agent in self.MC_Agents:
            mc_agent.step(self, t)
            # 清空通信层信息，准备迎接更新
            mc_agent.connected_att_agents = []

        # 每个侦察单元更新
        for t_agent in self.OBS_T_Agents:
            t_agent.step(self, t)

        # 每个打击单元更新
        for attacker in self.ATT_Agents:
            attacker.step(self, t)

        # 每个打击单元挂载武器更新
        for missile in self.missile_launched:
            missile.step(self, t)

        # 更新C_Network
        self.c_network.unpdate_network(self, t)

        # 每个通信请求更新
        for quest in self.c_quests:
            if quest.state == 3:
                pass
            else:
                quest.update_quest(self, t)

        # 随机生成2个目标
        self.add_enemy(2)

        # 生成数据
        mean_attr, differ_attr = self.data_generation()

        return mean_attr, differ_attr
