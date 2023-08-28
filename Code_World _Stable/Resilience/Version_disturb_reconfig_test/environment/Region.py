from utilities.CommonUtils import *
from utilities.PartitionUtils import *
from environment.Turtle import *
from environment.Disturb import *
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
        # 区域内的中心云CC_Agent
        self.CC_Agents = []
        # 区域内的边缘云MC_Agent
        self.MC_Agents = []
        # 区域内的侦察终端T_Agent
        self.OBS_T_Agents = []
        # 区域内的打击智能体
        self.ATT_Agents = []
        # 区域内的终端智能体
        self.Terminal_Agents = []
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
        # 扰动控制智能体
        self.disturb_robot = None
        # 是否重构
        self.reconfig = False
        # 六个智能体是否开启
        self.MA_state = [1, 1, 1, 1, 1, 1]

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

    # 建立装备网络
    def equip_network_create(self):
        # 构建网络
        EQ_G = nx.Graph()
        # 添加无线链路
        for quest in self.c_quests:
            if quest.state == 1:
                source = quest.send.name
                target = quest.receive.name
                EQ_G.add_edge(source, target)
        # 添加有线链路
        for cc_agent in self.CC_Agents:
            for mc_agent in cc_agent.MC_Agents:
                source = cc_agent.name
                target = mc_agent.name
                EQ_G.add_edge(source, target)
        # print(EQ_G.nodes())
        # print(EQ_G.edges())
        # print("装备网络节点数：%d, 连边数：%d" % (len(EQ_G.nodes), len(EQ_G.edges)))
        # 装备网络平均度
        # weighted_degree = EQ_G.degree()
        # w_D = list(weighted_degree)
        # df_node_D = pd.DataFrame(w_D)
        # df_node_D.columns = ["node", "value"]
        # mean_degree = df_node_D["value"].mean()

        nodes = len(EQ_G.nodes())
        edges = len(EQ_G.edges())
        mean_degree = 2 * edges / nodes

        # 装备网络平均介数
        a = nx.betweenness_centrality(EQ_G)
        df_node_B = pd.DataFrame(columns=["node", "value"])
        df_node_B["node"] = a.keys()
        df_node_B["value"] = a.values()
        mean_betw = df_node_B["value"].mean()

        # 装备网络平均最短路径长度
        mean_spl = nx.average_shortest_path_length(EQ_G)

        # 装备网络最大连通子团大小
        max_connect_num = len(max(nx.connected_components(EQ_G), key=len))

        return mean_degree, mean_betw, mean_spl, max_connect_num

    # 生成计算指标数据
    def data_generation(self):
        # 杀伤链闭合规模(没有侦察单元的收尾)
        close_kill_chains = [kc for kc in self.kill_chains if kc.close == True]
        close_kc_num = len(close_kill_chains)

        # 杀伤链闭合时间
        if len(close_kill_chains) == 0:
            close_total_time = 0
        else:
            close_times = [kc.close_time for kc in close_kill_chains]
            close_total_time = 0.1 * sum(close_times)

        # 区域侦察覆盖率
        real_grid = [g for g in self.turtles if g.always_observed == False]
        locked_grid = [g for g in real_grid if g.is_observed == True]
        grid_cover_rate = len(locked_grid) / len(real_grid)

        # 体系目标感知效率
        totoal_locked_enemies = [e for e in self.Enemies if e.locked == True]
        locked_num = len(totoal_locked_enemies)

        # 识别率（暂无）

        # 体系决策响应率
        local_unalloc_nums = [ag.unalloc_enemy_num for ag in self.MC_Agents]
        local_alloc_nums = [ag.alloc_enemy_num for ag in self.MC_Agents]
        decide_respond_rate = sum(local_alloc_nums)
        # if sum(local_unalloc_nums) == 0:
        #     decide_respond_rate = 0
        # else:
        #     decide_respond_rate = sum(local_alloc_nums) / sum(local_unalloc_nums)

        # 体系锁敌效率
        assigned_enemies = [
            e for e in self.Enemies if e.is_assigned_to_attacker == True
        ]
        assigned_num = len(assigned_enemies)

        # 建立装备网络
        # 装备网络平均度
        # 装备网络平均介数
        # 装备网络平均最短路径长度
        # 装备网络最大连通子团大小
        (
            eqg_mean_degree,
            eqg_mean_betw,
            eqg_mean_spl,
            eqg_max_connect_num,
        ) = self.equip_network_create()

        # 通信网络平均加权度
        weighted_degree = list(self.c_network.G.degree(weight="Mission_Load_Real"))
        wd_list = [data[1] for data in weighted_degree]
        mean_weighted_degree = sum(wd_list) / len(wd_list)

        # 通信网络最大连通子团
        PG = net_copy(self.c_network.G)
        del_edge = []
        for link in PG.edges(data=True):
            if link[2]["attr"]["Mission_Load_Rest"] == 0:
                del_edge.append((link[0], link[1]))
        PG.remove_edges_from(del_edge)
        max_connect_num = len(max(nx.connected_components(PG), key=len))

        # 通信完成效率
        finish_quests = [q for q in self.c_quests if q.state == 3]
        finish_quest_num = len(finish_quests)

        # 通信链路负载规模
        load_link = [
            (n1, n2)
            for n1, n2, data in self.c_network.G.edges(data=True)
            if data["Mission_Load_Real"] > 0
        ]
        load_link_num = len(load_link)

        # 通信链路过载规模
        load_max_link = [
            (n1, n2)
            for n1, n2, data in self.c_network.G.edges(data=True)
            if data["Mission_Load_Real"] == 5
        ]
        load_max_link_num = len(load_max_link)

        # 通信需求处理效率
        unfinished_quest = [q for q in self.c_quests if q.state < 2]
        loading_quest = [q for q in self.c_quests if q.state == 1]
        if len(unfinished_quest) == 0:
            quest_load_rate = 0
        else:
            quest_load_rate = len(loading_quest) / len(unfinished_quest)

        mean_attr = [
            close_kc_num,
            close_total_time,
            grid_cover_rate,
            decide_respond_rate,
            locked_num,
            assigned_num,
            finish_quest_num,
            eqg_mean_degree,
            eqg_mean_betw,
            eqg_mean_spl,
            eqg_max_connect_num,
            mean_weighted_degree,
            max_connect_num,
            load_link_num,
            load_max_link_num,
            quest_load_rate,
        ]

        differ_attr = [
            close_kc_num,
            close_total_time,
            locked_num,
            assigned_num,
            finish_quest_num,
        ]
        return mean_attr, differ_attr

    # 新增目标
    def add_enemy(self):
        # 新增单元
        # 当前个数
        old_alive_enemy = [e for e in self.Enemies if e.alive == True]
        old_enemy_num = len(old_alive_enemy)
        if old_enemy_num < 400:
            # 补充目标
            num_enemies = 400 - old_enemy_num
            # 选择未被侦察的区域
            unobserved_turtles = [
                grid for grid in self.turtles if grid.always_observed == False
            ]
            # 随机选择一个unobserved_turtle
            select_grid = random.sample(unobserved_turtles, num_enemies)
            enemies_xy = [
                (
                    random.uniform(grid.x[0], grid.x[1]),
                    random.uniform(grid.y[0], grid.y[1]),
                )
                for grid in select_grid
            ]

            enemies_xy = initial_enemy(0, 0, 400, 400, 30, 370, num_enemies)
            add_enemies = [Enemy() for i in range(num_enemies)]
            for i, enemy in enumerate(add_enemies):
                enemy.name = "T_%d" % (len(self.Enemies) + i)
                enemy.p_pos = (enemies_xy[i][0], enemies_xy[i][1])
                enemy_turtle = self.get_turtles_by_node(
                    enemies_xy[i][0], enemies_xy[i][1]
                )[0]
                enemy_turtle.targets.append(enemy)
            self.Enemies.extend(add_enemies)

    # 每一步下的所有智能体动作更新
    def step(self, t):
        # 扰动注入
        self.disturb_robot.disturb_generate(self, t)

        # turtle 更新turtle的被侦察状态
        for turtle in self.turtles:
            turtle.update_observe(self, t)

        # 每个指控单元更新
        for mc_agent in self.MC_Agents:
            mc_agent.step(self, t)
            # 清空通信层信息，准备迎接更新
            mc_agent.connected_att_agents = []

        # 判断是否重构，重构则中心云启动, 且t大于200仿真时间步长
        if self.reconfig and t > 500:
            for cc_agent in self.CC_Agents:
                cc_agent.step(self, t)

        # 每个侦察单元更新
        work_obs_agents = [agent for agent in self.OBS_T_Agents if agent.fault == False]
        for t_agent in work_obs_agents:
            t_agent.step(self, t)

        # 每个打击单元更新
        work_att_agents = [agent for agent in self.ATT_Agents if agent.fault == False]
        for attacker in work_att_agents:
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
        self.add_enemy()

        # 生成数据
        mean_attr, differ_attr = self.data_generation()

        return mean_attr, differ_attr
