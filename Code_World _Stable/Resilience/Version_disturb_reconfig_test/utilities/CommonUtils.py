from math import *
import random
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cdist
import networkx as nx


# 生成0-1取值的6元素列表的遍历
def iterate_list(n):
    for i in range(2**n):
        binary = bin(i)[2:].zfill(n)
        list_ = [int(bit) for bit in binary]
        yield list_


# 计算两个坐标间的距离
def get_distance(co1, co2):
    d = np.sqrt(np.square(co1[0] - co2[0]) + np.square(co1[1] - co2[1]))
    return d


# 聚类算法，输入一堆节点的二维坐标，输出节点的分类
def cluster(X):
    # 定义k值的范围
    K = range(2, 10)

    # 定义不同k值对应的聚类模型
    models = [KMeans(n_clusters=k, random_state=42).fit(X) for k in K]

    # 计算每个聚类模型的轮廓系数
    scores = [silhouette_score(X, model.labels_) for model in models]

    # 计算每个聚类模型的畸变程度
    distortions = [
        sum(np.min(cdist(X, model.cluster_centers_, "euclidean"), axis=1)) / X.shape[0]
        for model in models
    ]

    # 选择最佳聚类模型
    best_k = np.argmax(scores) + 2  # 轮廓系数最大对应的k值
    best_model = models[best_k - 2]  # 对应的聚类模型

    return best_k, best_model


# 在由两个同心正方形组成的带状区域内随机生成目标坐标
def initial_enemy(x_min, y_min, x_max, y_max, a_size, b_size, num_points):
    # 生成正方形A和B
    x1 = [
        x_min + (x_max - a_size - x_min) / 2,
        x_min + (x_max - a_size - x_min) / 2,
        x_min + (x_max + a_size - x_min) / 2,
        x_min + (x_max + a_size - x_min) / 2,
        x_min + (x_max - a_size - x_min) / 2,
    ]
    y1 = [
        y_min + (y_max - a_size - y_min) / 2,
        y_min + (y_max + a_size - y_min) / 2,
        y_min + (y_max + a_size - y_min) / 2,
        y_min + (y_max - a_size - y_min) / 2,
        y_min + (y_max - a_size - y_min) / 2,
    ]
    x2 = [
        x_min + (x_max - b_size - x_min) / 2,
        x_min + (x_max - b_size - x_min) / 2,
        x_min + (x_max + b_size - x_min) / 2,
        x_min + (x_max + b_size - x_min) / 2,
        x_min + (x_max - b_size - x_min) / 2,
    ]
    y2 = [
        y_min + (y_max - b_size - y_min) / 2,
        y_min + (y_max + b_size - y_min) / 2,
        y_min + (y_max + b_size - y_min) / 2,
        y_min + (y_max - b_size - y_min) / 2,
        y_min + (y_max - b_size - y_min) / 2,
    ]

    # 生成随机点
    points = []
    for i in range(num_points):
        while True:
            x = random.uniform(x_min, x_max)
            y = random.uniform(y_min, y_max)
            if (
                x > x_min + (x_max - b_size - x_min) / 2
                and x < x_min + (x_max + b_size - x_min) / 2
                and y > y_min + (y_max - b_size - y_min) / 2
                and y < y_min + (y_max + b_size - y_min) / 2
                and (
                    x < x_min + (x_max - a_size - x_min) / 2
                    or x > x_min + (x_max + a_size - x_min) / 2
                    or y < y_min + (y_max - a_size - y_min) / 2
                    or y > y_min + (y_max + a_size - y_min) / 2
                )
            ):
                points.append((x, y))
                break
    return points


# 生成节点坐标用于绘图
def entity_scope(p_pos, scope):
    p1 = (p_pos[0] - scope, p_pos[1] - scope)
    p2 = (p_pos[0] - scope, p_pos[1] + scope)
    p3 = (p_pos[0] + scope, p_pos[1] + scope)
    p4 = (p_pos[0] + scope, p_pos[1] - scope)
    return [p1, p2, p3, p4, p1]


"""
输入圆点坐标(h,k) 以及半径r
返回圆周上的随机坐标点
theta1和theta2是角度范围的下界和上界, 在范围内生成随机速度方向
"""


def circle_rand_point(h, k, r, theta1, theta2):
    theta = theta1 + random.random() * (theta2 - theta1)
    return h + cos(theta) * r, k + sin(theta) * r


"""
生成带状区域
"""


def initial_enemy(x_min, y_min, x_max, y_max, a_size, b_size, num_points):
    # 生成正方形A和B
    x1 = [
        x_min + (x_max - a_size - x_min) / 2,
        x_min + (x_max - a_size - x_min) / 2,
        x_min + (x_max + a_size - x_min) / 2,
        x_min + (x_max + a_size - x_min) / 2,
        x_min + (x_max - a_size - x_min) / 2,
    ]
    y1 = [
        y_min + (y_max - a_size - y_min) / 2,
        y_min + (y_max + a_size - y_min) / 2,
        y_min + (y_max + a_size - y_min) / 2,
        y_min + (y_max - a_size - y_min) / 2,
        y_min + (y_max - a_size - y_min) / 2,
    ]
    x2 = [
        x_min + (x_max - b_size - x_min) / 2,
        x_min + (x_max - b_size - x_min) / 2,
        x_min + (x_max + b_size - x_min) / 2,
        x_min + (x_max + b_size - x_min) / 2,
        x_min + (x_max - b_size - x_min) / 2,
    ]
    y2 = [
        y_min + (y_max - b_size - y_min) / 2,
        y_min + (y_max + b_size - y_min) / 2,
        y_min + (y_max + b_size - y_min) / 2,
        y_min + (y_max - b_size - y_min) / 2,
        y_min + (y_max - b_size - y_min) / 2,
    ]

    # 生成随机点
    points = []
    for i in range(num_points):
        while True:
            x = random.uniform(x_min, x_max)
            y = random.uniform(y_min, y_max)
            if (
                x > x_min + (x_max - b_size - x_min) / 2
                and x < x_min + (x_max + b_size - x_min) / 2
                and y > y_min + (y_max - b_size - y_min) / 2
                and y < y_min + (y_max + b_size - y_min) / 2
                and (
                    x < x_min + (x_max - a_size - x_min) / 2
                    or x > x_min + (x_max + a_size - x_min) / 2
                    or y < y_min + (y_max - a_size - y_min) / 2
                    or y > y_min + (y_max + a_size - y_min) / 2
                )
            ):
                points.append((x, y))
                break
    return points


""" 
基于链路的节点序列给出一个个的路径
例如：
输入：路径的节点序列：[1, 2, 3]
输出：路径的链路序列：[(1, 2), (2, 3)]
输出的链路序列, 节点按小-大重新排序
"""


def path_exchange(node_array):
    path_list = []
    for i in range(len(node_array) - 1):
        link = (node_array[i], node_array[i + 1])
        path_list.append(tuple(sorted(link)))
    return path_list


"""
网络深度copy
"""


def net_copy(G):
    G1 = nx.Graph()
    for edge in G.edges(data=True):
        G1.add_edge(edge[0], edge[1], attr=edge[2])
    return G1


"""
计算两个列表的交集 
"""


def cross_item(a, b):
    return list(set(a).intersection(set(b)))
