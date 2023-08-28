import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from queue import PriorityQueue  # 优先级队列，优先级高的先输出


def auction(value):
    # 注意，目前限制了代理不能选择没价值的商品，并且最终是给出当前总回报最大的组合，可能导致代理虽然有可选择的商品，但还是没得到分配
    agent_n = value.shape[0]  # 代理数
    assignment_n = value.shape[1]  # 商品数
    # 初始化价格和分配
    prices = np.zeros(assignment_n)  # 各商品价格
    allocations = np.zeros(agent_n, dtype=int) - 1  # -1表示未分配
    unallocated = set(range(assignment_n))  # 还未分配的商品
    e = round(1 / max(agent_n, assignment_n), 8)  # 报价公式里的小常数

    while unallocated:
        h_p = {}
        sy_flag = 0  # 用于标记是否有代理报价，只要有一个代理报价就为1
        for a in range(agent_n):
            if allocations[a] != -1:  # 已经有分配过的就不看了
                continue
            max_v = -np.inf  # 最优商品收益
            max_a = None  # 最优商品
            second_max_v = -np.inf  # 次优商品收益
            second_max_a = None  # 次优商品
            v_list = PriorityQueue()  # 各商品对代理的价值
            for b in range(assignment_n):
                if value[a, b] != 0:  # 不看无价值的商品
                    if value[a, b] - prices[b] > 0:  # 不看收益小于等于0的商品
                        v_list.put((-(value[a, b] - prices[b]), b))
            if v_list.empty():
                continue
            max1 = v_list.get()
            max_v = -max1[0]
            max_a = max1[1]
            if not (v_list.empty()):  # 是否有第二个商品还没分配
                second_max = v_list.get()
                second_max_v = -second_max[0]
                second_max_a = second_max[1]

            if second_max_a != None:  # 计算报价
                if prices[max_a] < (
                    prices[max_a] + (max_v - second_max_v) + e
                ):  # 报价要是能比现在的高 则获得该商品
                    sy_flag = 1
                    # 意味着(max_v-second_max_v)+e大于0，其中(max_v-second_max_v)收益差一定大于-e
                    # 说明任务max_a对于a还是有利可图，但是这里还要具体比较，在这个价格下谁的利润最大
                    prices[max_a] = prices[max_a] + (max_v - second_max_v) + e
                    allocations[a] = max_a  # 第a个代理暂时分配到收益最大的任务
                    winner = np.where(allocations == max_a)[
                        0
                    ]  # 之前获得该商品的代理失去该商品，需要重新拍别的
                    if winner.size > 1:
                        for i in winner:
                            if i != a and allocations[a] != -1:
                                allocations[i] = -1
                    # if winner.size > 1:
                    #     #计算这个出价下 以选择这个任务的代理的利润
                    #     #如果大于0，意味着这个价下还有利润，那就选都可以出的起这个价的中，利润最大的
                    #     scores = []
                    #     for i in range(winner.size):
                    #         v2=value[winner[i],:].copy()
                    #         for i1 in range(len(v2)):
                    #             if i1 in allocations and i1!=max_a:
                    #                 v2[i1]=0
                    #         v2=np.sort(v2)[::-1]
                    #         if len(v2)>1:
                    #             scores.append(v2[0]-v2[1]+e)
                    #         else:
                    #             scores.append(v2[0]+e)

                    #     # scores = [value[winner[i], max_a] - prices[max_a] for i in range(winner.size)]
                    #     max_idx = np.argmax(scores)
                    #     for i in range(winner.size):
                    #         if i != max_idx and allocations[winner[i]] != -1:
                    #             allocations[winner[i]] = -1
                    #     allocations[winner[max_idx]] = max_a
            else:
                if prices[max_a] < (prices[max_a] + (max_v) + e):
                    sy_flag = 1
                    prices[max_a] = prices[max_a] + (max_v) + e
                    allocations[a] = max_a  # 第a个代理暂时分配到收益最大的任务
                    winner = np.where(allocations == max_a)[0]
                    if winner.size > 1:
                        for i in winner:
                            if i != a and allocations[a] != -1:
                                allocations[i] = -1
                    # if winner.size > 1:
                    #     scores = []
                    #     for i in range(winner.size):
                    #         v2=value[winner[i],:].copy()
                    #         for i1 in range(len(v2)):
                    #             if i1 in allocations and i1!=max_a:
                    #                 v2[i1]=0
                    #         v2=np.sort(v2)[::-1]
                    #         if len(v2)>1:
                    #             scores.append(v2[0]-v2[1]+e)
                    #         else:
                    #             scores.append(v2[0]+e)
                    #     # scores = [value[winner[i], max_a] - prices[max_a] for i in range(winner.size)]
                    #     max_idx = np.argmax(scores)
                    #     for i in range(winner.size):
                    #         if i != max_idx and allocations[winner[i]] != -1:
                    #             allocations[winner[i]] = -1
                    #     allocations[winner[max_idx]] = max_a
        if sy_flag == 0:  # 一个代理都不报价就退出
            break
        # 更新未分配的商品
        unallocated = set(range(assignment_n)) - set(allocations)
        if agent_n < assignment_n:
            if not (-1 in allocations):
                break

    # 返回分配结果和价格
    return allocations, prices


if __name__ == "__main__":
    print(
        auction(np.array([[6.567, 12, 0], [10, 10, 12.487], [10, 10, 12], [10, 1, 2]]))
    )  # 输入价值矩阵，xij表示商品j对代理i的价值
