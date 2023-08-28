from agents.Entity import Entity
from agents.Kill_Chain_Agent import *
from utilities.CommonUtils import *
from utilities.DistributionUtils import *

from math import *
import networkx as nx


# C:Communitcation Node 通信节点（起到接入通信的作用）
class C_Node(Entity):
    def __init__(self):
        super(C_Node, self).__init__()
        # 通信节点是否可用
        self.fault_state = False


# WLC:WireLess Communitcation Node 无线通信节点（起到接入通信的作用）
class WLC_Node(C_Node):
    def __init__(self):
        super(WLC_Node, self).__init__()
        # 明确属性 基站
        self.type = "bts"
        # 通信范围
        self.commun_scope = 40
        # 通信节点故障状态
        self.fault_state = False
        # 通信节点的恢复时间(单位：0.1s)
        self.recov_time = 15
        # 敌情态势汇总
        self.enemy_list = []
        # 通信节点是否激活
        self.active = False

    def is_agent_in_commun_scope(self, x, y):
        x_bool = (x >= self.p_pos[0] - self.commun_scope) & (
            x <= self.p_pos[0] + self.commun_scope
        )
        y_bool = (y >= self.p_pos[1] - self.commun_scope) & (
            y <= self.p_pos[1] + self.commun_scope
        )
        return x_bool & y_bool

    # 终端智能体从通信节点处下载云上数据，若该智能体在边缘云管辖范围内则返回云上数据，若不在则返回0
    def info_download(self, region, t_agent, info):
        for mc_agent in region.MC_Agents:
            if t_agent in mc_agent.OBS_T_Agents:
                return mc_agent.obs_data
            else:
                return 0

    # 终端智能体从通信节点处上传云上数据，若该智能体在边缘云管辖范围内则返回云上数据，成功则返回1，若不在则返回0
    def info_upload(self, region, t_agent, info):
        for mc_agent in region.MC_Agents:
            if t_agent in mc_agent.OBS_T_Agents:
                mc_agent.obs_data = info
                return 1
            else:
                return 0


class WLC_Link(object):
    def __init__(self):
        # 通信链路名称
        self.name = ""
        # 通信链路两端通信节点
        self.end_nodes = []
        # 通信链路的传输速率(Mbps)
        self.trans_v = 137
        # 通信链路的丢包率
        self.packet_loss = 0.95
        # 通信链路的误码率
        self.error_rate = 0.95
        # 通信链路的最大通信请求负载(待优化)
        self.max_trans_num = 10
        # 通信链路故障状态
        self.fault_state = False
        # 通信链路的恢复时间(单位：0.1s)
        self.recov_time = 15


# C:Communication Network 通信网络（整个通信网的维护）
class C_Network(object):
    def __init__(self):
        # 通信网络节点信息维护 dataframe
        # 节点信息中包括
        self.node_info = None
        # 通信网络连边信息维护 dataframe
        self.link_info = None
        # 网络实体 G
        self.G = None
        # 网络的坐标信息
        self.pos = {}
        # 网络节点的索引
        self.c_nodes = {}

    # 创建通信网络(该部分同样也可以基于数据输入创建网络)
    def create_commun_net(self, region):
        # 创建一个横平竖直排列的晶格网络
        # 一共5*5=25个通信节点
        rows = 7
        columns = 7
        G = nx.grid_2d_graph(rows, columns)

        # 计算节点位置映射到 [50, 350] 范围内
        scale_x = 300 / (columns - 1)
        scale_y = 300 / (rows - 1)
        pos = {
            (i, j): (j * scale_x + 50, i * scale_y + 50)
            for i in range(rows)
            for j in range(columns)
        }
        # 映射到新的graph
        map_G = nx.Graph()
        node_map = {}
        pos_map = {}
        # 初始化通信单元实体
        for i, (node, coord) in enumerate(pos.items()):
            c_node = WLC_Node()
            c_node.name = "C%d" % (i + 1)
            c_node.p_pos = coord
            self.pos[c_node.name] = coord
            node_map[node] = c_node.name
            pos_map[c_node.name] = coord
            map_G.add_node(c_node.name)
            map_G.nodes[c_node.name]["active"] = c_node.active
            self.c_nodes[c_node.name] = c_node
            # c_node存储到region里
            region.C_Nodes.append(c_node)

        # 初始化通信链路实体
        for edge in G.edges():
            map_edge = (node_map[edge[0]], node_map[edge[1]])
            map_G.add_edges_from([map_edge])
            # 两端节点
            cn1 = self.c_nodes[map_edge[0]]
            cn2 = self.c_nodes[map_edge[1]]
            # 实体化链路
            c_link = WLC_Link()
            c_link.name = "Link_%s_%s" % (cn1.name, cn2.name)
            c_link.end_nodes = [cn1, cn2]
            # 添加链路属性
            map_G.edges[map_edge]["Total_Span"] = 1
            map_G.edges[map_edge]["Mission_Load_Max"] = c_link.max_trans_num
            map_G.edges[map_edge]["Mission_Load_Real"] = 0
            map_G.edges[map_edge]["Mission_Load_Rest"] = c_link.max_trans_num
            map_G.edges[map_edge]["Fault"] = False
            map_G.edges[map_edge]["Reconfig"] = False
        # 将映射后的通信网络的graph存储
        self.G = map_G

    # 更新通信网络连通状态、负载状态
    def unpdate_network(self, region, t):
        # 获取所有通信请求列表,更新链接状态
        od_list = [quest for quest in region.c_quests if quest.state != 3]
        # 更新节点激活状态
        sources = [quest.source for quest in od_list]
        targets = [quest.target for quest in od_list]
        for c_node in region.C_Nodes:
            if (c_node.name in sources) or (c_node.name in targets):
                c_node.active = True
                self.G.nodes[c_node.name]["active"] = True
            else:
                c_node.active = False
                self.G.nodes[c_node.name]["active"] = False
        # 判断每个od是否到达完成时间，到达则释放相应链路
        for working_od in [od for od in od_list if od.state == 1]:
            if (working_od.start_time + working_od.real_span) < t:
                working_od.state = 2
                for link in working_od.od_path:
                    if self.G.has_edge(link[0], link[1]):
                        self.G[link[0]][link[1]]["Mission_Load_Rest"] += 1
                        self.G[link[0]][link[1]]["Mission_Load_Real"] += -1
                    else:
                        pass
        # OD配流
        self.G, od_list = allocate_od(self.G, od_list, t)
