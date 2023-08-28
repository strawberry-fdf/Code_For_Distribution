import networkx as nx
import pandas as pd
import numpy as np


"""
计算单个有向网络的规模、平均度、平均介数、平均最短路径、聚类系数
"""


def magnificent_network_attribute(path):
    df_edge = pd.read_csv(path)
    G = nx.from_pandas_edgelist(df_edge, "caller", "callee", create_using=nx.DiGraph())
    MG = max(nx.weakly_connected_component_subgraphs(G), key=len)
    # 网络规模
    node_num = nx.number_of_nodes(MG)
    edge_num = nx.number_of_edges(MG)
    print(node_num)
    print(edge_num)
    # 网络平均度
    D = list(MG.degree())
    df_node_D = pd.DataFrame(D)
    df_node_D.columns = ["node", "value"]
    mean_degree = df_node_D["value"].mean()
    df_node_D.to_csv("degree/" + path + "_degree.csv", index=False)
    print(mean_degree)

    # 计算网络的平均介数
    df_node_B = pd.DataFrame(columns=("node", "value"))  # 生成介数
    a = nx.betweenness_centrality(MG)
    df_node_B["node"] = a.keys()
    df_node_B["value"] = a.values()
    mean_betw = df_node_B["value"].mean()
    df_node_B.to_csv("betweenness/" + path + "_betweenness.csv", index=False)
    print(mean_betw)
    """
    #平均最短路径长度
    pathlengths=[]
    for v in MG.nodes():
        spl=nx.single_source_shortest_path_length(MG,v)
        #print('%s %s' % (v,spl))
        for p in spl.values():
            pathlengths.append(p)
    #取出每条路径，计算平均值。
    short_path1 = sum(pathlengths)/len(pathlengths)
    print(short_path1)
    """
    # short_path2 = nx.average_shortest_path_length(MG)
    # print(short_path2)
    # 聚类系数
    df_node_C = pd.DataFrame(columns=("node", "value"))  # 生成介数
    a = nx.clustering(MG)
    df_node_C["node"] = a.keys()
    df_node_C["value"] = a.values()
    mean_C = df_node_C["value"].mean()
    df_node_C.to_csv("clustering/" + path + "_clustering.csv", index=False)
    print(mean_C)
    # return node_num,edge_num,mean_degree,mean_betw,short_path,Clustering
    return node_num, edge_num, mean_degree, mean_betw, mean_C


"""
随机生成序列
"""


def random_order(G):
    MG = G.copy()
    df_node = pd.DataFrame(columns=("node", "value"))
    df_node["node"] = list(MG.nodes())
    df_node["value"] = np.random.rand(len(MG.nodes()))  # 存储了节点被删除随机数,并按照升序排列
    df_node = df_node.sort_values(by="value", axis=0, ascending=True).reset_index(
        drop=True
    )
    return df_node, MG


"""
按度大小生成序列
"""


def degree_order(G):
    MG = G.copy()
    df_node = pd.DataFrame(columns=("node", "value"))
    a = list(MG.degree())
    df_node = pd.DataFrame(a)
    df_node.columns = ["node", "value"]
    df_node = df_node.sort_values(by="value", axis=0, ascending=True).reset_index(
        drop=True
    )
    return df_node, MG


"""
按介数大小生成序列
"""


def betweenness_order(G, betweenness_file=False):
    MG = G.copy()
    df_node = pd.DataFrame(columns=("node", "value"))
    if betweenness_file:  # 若有介数记录文件
        df_node = pd.read_csv(betweenness_file)
        print(df_node)
        # 读取介数记录文件
    else:
        df_node = pd.DataFrame(columns=("node", "value"))  # 生成介数
        a = nx.betweenness_centrality(MG)
        df_node["node"] = a.keys()
        df_node["value"] = a.values()
    df_node = df_node.sort_values(by="value", axis=0, ascending=True).reset_index(
        drop=True
    )
    return df_node, MG


"""
单个渗流过程
"""


def new_f_percolation(MG, df_node, f):
    if f < len(df_node):
        df_drop = df_node.iloc[-f:, :]  # 将要删除的点
        df_node.drop(df_node.index[-f:], inplace=True)
    else:
        df_drop = df_node
    drop_node = list(df_drop["node"])
    MG.remove_nodes_from(drop_node)
    return MG


def f_percolation(MG, df_node, i, f):
    largest_cc = max(nx.connected_components(MG), key=len)
    largest_cc = MG.subgraph(largest_cc)
    efficiency = nx.global_efficiency(largest_cc)

    # aver_spl = nx.average_shortest_path_length(largest_cc)
    # aver_spl_latency = nx.average_shortest_path_length(largest_cc, weight="Total_Span")

    # 考虑每个子团
    aver_spl_list = []
    aver_shortest_total_span_list = []
    aver_max_load_list = []
    cc_d_list = []
    for cc in nx.connected_components(MG):
        cc_graph = MG.subgraph(cc)
        cc_scare = len(cc_graph)
        cc_d = nx.diameter(cc_graph)
        aver_spl = nx.average_shortest_path_length(cc_graph)
        aver_shortest_total_span = nx.average_shortest_path_length(
            largest_cc, weight="Total_Span"
        )
        aver_max_load = nx.average_shortest_path_length(
            largest_cc, weight="Mission_Load_Max"
        )
        max_load_num = len(nx.shortest_path(largest_cc, weight="Mission_Load_Max"))
        if cc_scare == 1:
            pass
        else:
            aver_spl_list.append(aver_spl)
            aver_shortest_total_span_list.append(aver_shortest_total_span)
            cc_d_list.append(cc_d)
            aver_max_load_list.append(aver_max_load * max_load_num)

    # 所有子团取均值
    if len(aver_spl_list) == 0:
        aver_aver_spl = 0
        aver_aver_shortest_total_span = 0
        aver_cc_d = 0
        aver_aver_load = 0
    else:
        aver_aver_spl = np.mean(aver_spl_list)
        aver_aver_shortest_total_span = np.mean(aver_shortest_total_span_list)
        aver_cc_d = np.mean(cc_d_list)
        aver_aver_load = np.mean(aver_max_load_list)

    # # 仅考虑最大连通子团
    # aver_aver_spl = nx.average_shortest_path_length(largest_cc)
    # aver_spl_span = nx.average_shortest_path_length(largest_cc, weight="Total_Span")
    # # 网络直径
    # d = nx.diameter(largest_cc)
    # if aver_spl_span == 0:
    #     aver_trans_cap = 0
    # else:
    #     # aver_trans_cap = len(largest_cc) / aver_spl_span
    #     aver_trans_cap = d / aver_spl_span

    cc = list(nx.connected_components(MG))
    if len(cc) > 0:
        lcc = len(sorted(cc, key=len, reverse=True)[0])
    else:
        lcc = 0
    print("第%d次删点的最大连通子图尺寸：" % i, lcc)
    if len(cc) > 1:
        scc = len(sorted(cc, key=len, reverse=True)[1])
    else:
        scc = 0
    print("第%d次删点的次大连通子图尺寸：" % i, scc)

    if f < len(df_node):
        df_drop = df_node.iloc[-f:, :]  # 将要删除的点
        df_node.drop(df_node.index[-f:], inplace=True)
    else:
        df_drop = df_node
    drop_node = list(df_drop["node"])
    MG.remove_nodes_from(drop_node)
    return (
        MG,
        df_node,
        lcc,
        efficiency,
        aver_aver_spl,
        aver_aver_shortest_total_span,
        aver_cc_d,
        aver_aver_load,
    )
