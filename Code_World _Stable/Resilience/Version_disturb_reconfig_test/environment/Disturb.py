import random


# turtle
class DisturbRobot(object):
    def __init__(self, d_time=0, d_mode=None, d_rate=0):
        # 名称
        self.name = ""
        # x区间
        # 扰动开始时间 d_time=None即代表无扰动，其他则在对应时间开始扰动
        self.disturb_time = d_time
        # 扰动模式
        # "random_commun_network_link_attack"
        # "deliberate_commun_network_link_attack"
        # "terminal_agent_random_destroyed"
        # "terminal_agent_random_damaged"
        self.disturb_mode = d_mode
        # 扰动强度
        self.disturb_rate = d_rate
        # 是否已扰动过
        self.disturb_already = False

    def disturb_generate(self, region, t):
        # 无扰动强度，则直接退出扰动施加
        if self.disturb_rate == 0:
            return
        # 如果已经施加过扰动，同样退出
        if self.disturb_already:
            return
        # 判断是否到达扰动开始时间
        if t < self.disturb_time:
            return
        else:
            if self.disturb_mode == "random_commun_network_link_attack":
                # 计算要随机删除边的数量,向下取整
                d_num = int(self.disturb_rate * len(region.c_network.G.edges()))
                # 随机删除C_Network的边
                # 获取图的所有边
                edges = list(region.c_network.G.edges())
                # 随机移除边
                random.shuffle(edges)
                removed_edges = edges[:d_num]
                region.c_network.G.remove_edges_from(removed_edges)
            elif self.disturb_mode == "deliberate_commun_network_link_attack":
                # 计算要蓄意删除边的数量
                d_num = int(self.disturb_rate * len(region.c_network.G.edges()))
                # 按照实时负载量从大到小给C_Network的边排序
                edges = [
                    (u, v, w["Mission_Load_Real"])
                    for u, v, w in region.c_network.G.edges(data=True)
                ]
                # 按边权重的降序排序
                edges.sort(key=lambda x: x[2], reverse=True)
                # 从大到小排序删除边
                removed_edges = edges[:d_num]
                region.c_network.G.remove_edges_from(
                    [(u, v) for u, v, _ in removed_edges]
                )
            elif self.disturb_mode == "terminal_agent_random_destroyed":
                # 计算要毁伤的终端单元数量
                d_num = int(self.disturb_rate * len(region.Terminal_Agents))
                # 随机选取终端单元设置fault = True
                random.shuffle(region.Terminal_Agents)
                destroyed_agents = region.Terminal_Agents[:d_num]
                for agent in destroyed_agents:
                    agent.fault = True
            elif self.disturb_mode == "terminal_agent_random_damaged":
                # 计算要损伤/性能降级的终端单元数量
                d_num = int(self.disturb_rate * len(region.Terminal_Agents))
                # 选取终端单元，判定如果是感知单元则感知范围降低，打击单元则射程降低
                random.shuffle(region.Terminal_Agents)
                damaged_agents = region.Terminal_Agents[:d_num]
                for agent in damaged_agents:
                    if agent.type == "scout":
                        agent.obs_scope = agent.obs_scope * 0.5
                    elif agent.type == "attack":
                        agent.scope = agent.scope * 0.5
            else:
                pass
            # 更新扰动施加状态
            self.disturb_already = True
