import networkx as nx
from utilities.CommonUtils import *

"""
OD配流函数(*核心)
功能: 给定Nr个OD, 将OD分配在网络路径上
输入: OD的dict, 网络graph
输出: 更新网络graph的连边权重:实际任务负载量、剩余任务负载量

配流算法流程：

1) 开始新建当前剩余通信网络, 即剩余任务负载量=0的连边删除的网络
2) 若未配流OD规模=0 或 未配流OD在剩余通信网络中不连通/不存在, 则配流结束, 退出算法
3) 计算每个未完成配流的OD在网络中的最短传输时间以及对应的最短路径
4) 计算任意两个OD间的交叉部分, 构建OD耦合网络, 节点权重: OD最短传输时间; 连边权重: OD交叉部分
5) 更新通信网络每条连边的预计任务负载量, 即考虑每条OD均走最短路径下, 网络每条连接的预计任务负载量, 统计预计任务负载量>剩余任务负载量的超负载链路
6) 判断OD耦合网络中包含超负载链路的的连边, 去除不包含超负载链路的连边
7) OD相关性网络的孤立节点, 直接作为配流OD, 更新OD对应的路径
8) 遍历OD相关性网络连通团
    1) 遍历OD相关性网络连通团中的连边, 以连边上所有超负载链路中剩余任务负载量最小的作为连边权重
    2) 遍历此时OD相关性网络连边中存在的所有超负载链路, 筛选每个超负载链路对应的OD网络, 以OD最短传输时间降序排列OD, 选择排名靠前 超负载链路剩余任务负载量的OD, 给OD节点pick权重+1
    3) 该OD相关性网络连通团中, pick权重大于0的即为配流OD, 更新OD对应的路径
    4) 存储pick权重等于0, 即第一轮未完成配流的OD
9) 遍历本轮所有配流OD, 对路径上的每个链路对应到通信网络中的链路, 更新通信网络中的剩余任务负载量, 剩余任务负载量-1
"""


def allocate_od(MG, od_list, t):
    unplaned_od = [od for od in od_list if od.state == 0]
    if len(unplaned_od) == 0:
        pass
    else:
        while True:
            mission_load_rest = nx.get_edge_attributes(MG, "Mission_Load_Rest")
            fault_state = nx.get_edge_attributes(MG, "Fault")
            MG_rest = net_copy(MG)
            # 找出所有剩余负载为0的边删掉
            remove_zero = []
            for edge in MG_rest.edges(data=True):
                try:
                    mlr_edge = mission_load_rest[(edge[0], edge[1])]
                    f_edge = fault_state[(edge[0], edge[1])]
                except:
                    mlr_edge = mission_load_rest[(edge[1], edge[0])]
                    f_edge = fault_state[(edge[1], edge[0])]
                if (mlr_edge == 0) | (f_edge != False):
                    remove_zero.append(edge)
            MG_rest.remove_edges_from(remove_zero)
            # step 1: 筛选出能够进行od配流的，即存在路径的od，计算其在网络中的最短传输时间以及对应的最短路径，进入下一步
            enable_plan_od = []
            # 字典形式存放od class, 键是od的id为索引
            enalbe_plan_od_dict = {}
            for od in unplaned_od:
                try:
                    od_shortest_span_path = nx.shortest_path(
                        MG_rest, od.source, od.target, weight="Total_Span"
                    )
                    od.predict_span = nx.shortest_path_length(
                        MG_rest, od.source, od.target, weight="Total_Span"
                    )
                    od.od_path_predict = path_exchange(od_shortest_span_path)
                    enable_plan_od.append(od)
                    enalbe_plan_od_dict[od.id] = od
                except:
                    # 代表od在网络内不连通/不存在
                    pass
            # 如果有未被配流的od，但是未配流OD在剩余通信网络中不连通/不存在，则退出循环
            # print(len(unplaned_od), len(enable_plan_od))
            if len(enable_plan_od) == 0:
                break
            # 按从小到达排列时间
            enable_plan_od.sort(key=lambda x: x.predict_span)
            for od in enable_plan_od:
                # 更新mission_load_rest
                mission_load_rest = nx.get_edge_attributes(MG, "Mission_Load_Rest")
                # 存放od路径上所有mission_load_rest
                od_path_rest_load_list = []
                for link in od.od_path_predict:
                    try:
                        od_path_rest_load_list.append(mission_load_rest[link])
                    except:
                        od_path_rest_load_list.append(
                            mission_load_rest[(link[1], link[0])]
                        )
                # 如果路径上有一条链路已经无剩余负载量，则跳过，执行下一条
                if 0 in od_path_rest_load_list:
                    pass
                else:
                    unplaned_od.remove(od)
                    for link in od.od_path_predict:
                        try:
                            mission_load_rest[link]
                            MG[link[0]][link[1]]["Mission_Load_Rest"] += -1
                            MG[link[0]][link[1]]["Mission_Load_Real"] += 1
                        except:
                            MG[link[1]][link[0]]["Mission_Load_Rest"] += -1
                            MG[link[1]][link[0]]["Mission_Load_Real"] += 1
                    # 配流完成后od状态变化
                    od.state = 1
                    od.od_path = od.od_path_predict
                    od.real_span = od.predict_span
                    od.start_time = t

            if len(unplaned_od) == 0:
                break

    return MG, od_list
