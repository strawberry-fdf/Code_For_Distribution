from agents.Entity import Entity
from agents.Kill_Chain_Agent import *
from agents.Commun_Agent import *
from utilities.CommonUtils import *
from utilities.AuctionUtils import *
from agents.Quest_Agent import *

import math
from scipy.spatial import KDTree


# 订单Agent，一个订单里包含多个聚类后分为一类的enemy_agent
class Order_Agent(object):
    def __init__(self):
        # 名称
        self.name = ""
        # 类别
        self.type = "Order"
        # 订单下包含的enemy_agent列表
        self.enemies = []
        # 订单下包含的enemy的几何中心
        self.p_pos = None


# MC:Margin-Cloud Agent 边缘云智能体
class MC_Agent(Entity):
    def __init__(self):
        super(MC_Agent, self).__init__()
        # 明确属性
        self.type = "mc"
        # 管辖区域范围
        self.margin = []
        # 管辖区域范围
        self.turtle_margin = []
        # 边缘云管辖的侦察端智能体
        self.OBS_T_Agents = []
        # 边缘云管辖的打击智能体
        self.ATT_Agents = []
        # 边缘云实时能通信的打击智能体
        self.connected_att_agents = []
        # 侦察终端返回的数据存储
        self.locked_enemies = []
        # 订单智能体管理，每次target_alloc时候更新
        self.order_agents = []
        # 管理状态/模式：常态 normal；应激 emergent
        self.operate_pattern = "normal"
        # 决策间隙
        self.cc_t = 10
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
        # 管辖区域的区域侦察覆盖率
        self.scout_rate = 0
        # 管辖区域的感知目标分配率
        self.alloc_rate = 0
        # 管辖区域的决策前未分配的目标
        self.unalloc_enemy_num = 0
        # 管辖区域的决策后分配的目标
        self.alloc_enemy_num = 0
        # 识别智能体能故障的概率
        self.recog_fault_rate = 0.8
        # 决策智能体故障的概率
        self.decide_fault_rate = 0.8

    def step(self, region, t):
        self.update_communication(region)
        # 更新mc_agent下的锁定目标，将已经被打击的目标去除
        # 这里在后续加上对打击目标的打击效果评估后根据上传信息更新
        self.locked_enemies = [
            enemy for enemy in self.locked_enemies if enemy.alive == True
        ]
        # 设置识别智能体故障
        if region.MA_state[1] == 0:
            random.shuffle(self.locked_enemies)
            mid_enemies = self.locked_enemies.copy()
            s_num = int(len(self.locked_enemies) * self.recog_fault_rate)
            self.locked_enemies = mid_enemies[:s_num]
            back_enemies = mid_enemies[s_num:]
            for enemy in back_enemies:
                enemy.locked = False
        # 更新管辖区域的区域侦察覆盖率
        # 获取管辖区域下的所有区域
        x_margin_range = [self.turtle_margin[0], self.turtle_margin[2]]
        y_margin_range = [self.turtle_margin[1], self.turtle_margin[3]]
        local_grids = region.get_turtles_by_range(x_margin_range, y_margin_range)
        # 管辖区块中非永久可见区域
        real_grid = [g for g in local_grids if g.always_observed == False]
        # 管辖区块非永久可见区域中的被探测区域
        locked_grid = [g for g in real_grid if g.is_observed == True]
        self.scout_rate = len(locked_grid) / len(real_grid)

        # 边缘云目标分配, 按照固定时间间隔进行一次决策
        if t % self.cc_t == 0:
            before_unalloc_enemies = [
                enemy for enemy in self.locked_enemies if enemy.is_allocated == False
            ]
            if before_unalloc_enemies:
                self.unalloc_enemy_num = len(before_unalloc_enemies)
                self.target_auction(region, t)
                # 更新感知目标分配比率
                after_unalloc_enemies = [
                    e for e in self.locked_enemies if e.is_allocated == False
                ]
                self.alloc_enemy_num = len(before_unalloc_enemies) - len(
                    after_unalloc_enemies
                )
                self.alloc_rate = self.alloc_enemy_num / self.unalloc_enemy_num
            else:
                self.alloc_rate = 0

    # 输入：region类别
    # 输出：该agent能连接到通信网络的通信节点
    def get_commun_node(self, region):
        commun_node = [
            c_node
            for c_node in region.C_Nodes
            if get_distance(self.p_pos, c_node.p_pos) < c_node.commun_scope
        ]
        return commun_node

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
        # 如果无法连入通信网络，则更新距离最近的通信节点
        else:
            self.is_commu = False
            self.c_node = None
            # 构建所有C_node的坐标集合
            all_C_Node_xy = [
                (c_node.p_pos[0], c_node.p_pos[1]) for c_node in region.C_Nodes
            ]
            # 构建kd-tree 实现快速检索
            tree = KDTree(all_C_Node_xy)
            # 查询最近的通信节点的索引
            _, min_index = tree.query([(self.p_pos[0], self.p_pos[1])])
            self.nearest_c_node = region.C_Nodes[min_index[0]]
            # 计算最近通信节点的坐标
            self.nearest_c_node_xy = (
                all_C_Node_xy[min_index[0]][0],
                all_C_Node_xy[min_index[0]][1],
            )

    """
    基于聚类的订单分配
    以一定频率进行目标重新派单
    主要输入: locked_enemies 被锁定的敌人, 所有的c_node
    1) 先对所有locked_enemies聚类, 对每一类构建一个订单order_agent
    2) 把订单更新到距离订单最近的两个c_node处 c_node.enemy_list
    """

    def target_alloc(self, region):
        # 清空c_node下的所有enemy_list
        for c_node in region.C_Nodes:
            c_node.enemy_list = []
        # 获取所有locked_enemies的坐标
        un_assigned_enemies = [
            enemy
            for enemy in self.locked_enemies
            if enemy.is_assigned_to_attacker == False
        ]
        locked_enemies_pos = [
            enemy.p_pos
            for enemy in self.locked_enemies
            if enemy.is_assigned_to_attacker == False
        ]
        # 分为三种情况
        # 1）无enemy 2)enemy数量<=2 3)enemy数量>2
        if len(locked_enemies_pos) == 0:
            return
        elif (len(locked_enemies_pos) <= 2) and (len(locked_enemies_pos) > 0):
            # 仅建立一个order_agent
            self.order_agents = [Order_Agent() for i in range(1)]
            for i, enemy in enumerate(self.locked_enemies):
                self.order_agents[0].enemies.append(enemy)
            # 更新订单智能体的中心位置
            for order_agent in self.order_agents:
                xs = [enemy.p_pos[0] for enemy in order_agent.enemies]
                ys = [enemy.p_pos[1] for enemy in order_agent.enemies]
                xc, yc = sum(xs) / len(xs), sum(ys) / len(ys)
                dist_to_cnode = [
                    (
                        c_node,
                        math.sqrt(
                            (c_node.p_pos[0] - xc) ** 2 + (c_node.p_pos[1] - yc) ** 2
                        ),
                    )
                    for c_node in region.C_Nodes
                ]
                sorted_dist_cnode = sorted(dist_to_cnode, key=lambda x: x[1])
                # 距离最近的c_node拿到订单
                sorted_dist_cnode[0][0].enemy_list.extend(order_agent.enemies)
                sorted_dist_cnode[1][0].enemy_list.extend(order_agent.enemies)
            return
        else:
            X = np.array(locked_enemies_pos)
            # 定义不同k值对应的聚类模型
            K = range(2, len(locked_enemies_pos))
            models = [KMeans(n_clusters=k, random_state=42).fit(X) for k in K]
            # 计算每个聚类模型的轮廓系数
            scores = [silhouette_score(X, model.labels_) for model in models]
            # 选择最佳聚类模型
            best_k = np.argmax(scores) + 2  # 轮廓系数最大对应的k值
            best_model = models[best_k - 2]  # 对应的聚类模型
            # 构建订单智能体
            self.order_agents = [Order_Agent() for i in range(best_k)]
            # print(best_k)
            # print(self.locked_enemies)
            # print(best_model.labels_)
            for i, enemy in enumerate(un_assigned_enemies):
                order_class = best_model.labels_[i]
                self.order_agents[order_class].enemies.append(enemy)
            # 更新订单智能体的中心位置
            for order_agent in self.order_agents:
                xs = [enemy.p_pos[0] for enemy in order_agent.enemies]
                ys = [enemy.p_pos[1] for enemy in order_agent.enemies]
                xc, yc = sum(xs) / len(xs), sum(ys) / len(ys)
                dist_to_cnode = [
                    (
                        c_node,
                        math.sqrt(
                            (c_node.p_pos[0] - xc) ** 2 + (c_node.p_pos[1] - yc) ** 2
                        ),
                    )
                    for c_node in region.C_Nodes
                ]
                sorted_dist_cnode = sorted(dist_to_cnode, key=lambda x: x[1])
                # 距离前2的c_node拿到订单
                sorted_dist_cnode[0][0].enemy_list.extend(order_agent.enemies)
                sorted_dist_cnode[1][0].enemy_list.extend(order_agent.enemies)

    """
    基于拍卖算法的订单分配
    1 更新所有打击单元的通信状态
    2 获取所有c_node_is_connected=True的打击单元connected_att_agents
    3 拍品即为self.locked_enemies, 竞拍者为connected_att_agents
    4 计算每个竞拍者对每个拍品的价值, 100/距离
    5 形成np.array,即竞拍者-拍品价值矩阵, 输入Auction_Self生成拍卖结果allocations, prices
    6 只取allocations中不为-1的, 即为最后目标分配结果
    """

    def target_auction(self, region, t):
        # 直到所有打击单元都已达到最大负载任务上限或所有目标都被分配完才结束
        i = 0
        while True:
            # 打击单元：能通信且未被分配目标；目标：存活且未被打击单元锁定
            pre_att_agents = [
                agent
                for agent in self.connected_att_agents
                if (agent.is_commu == True)
                and (len(agent.pre_target) < agent.max_target_load)
            ]
            locked_unallocated_enemies = [
                enemy for enemy in self.locked_enemies if enemy.is_allocated == False
            ]
            # 拍品即为self.locked_enemies, 竞拍者为connected_att_agents
            items = locked_unallocated_enemies
            bidders = pre_att_agents
            # 任意一个为0，竞拍取消
            i += 1
            # print("第 %d 竞拍开始!，剩余 %d 个打击单元竞拍 %d 个目标!" % (i, len(bidders), len(items)))
            if not items or not bidders:
                break
            # 计算每个竞拍者对每个拍品的价值
            # 如果bidder.target是空列表，则价值为：最大距离(600)-agent实际到目标的距离
            # 如果bidder.target非空，则选取最后一个元素到当前目标的距离
            bidder_offers = {}
            for bidder in bidders:
                if not bidder.pre_target:
                    val_list = []
                    for item in items:
                        d = get_distance(bidder.p_pos, item.p_pos)
                        val = 600 - d
                        val_list.append(val)
                    bidder_offers[len(bidder_offers)] = val_list
                else:
                    val_list = []
                    for item in items:
                        d = get_distance(bidder.pre_target[-1].p_pos, item.p_pos)
                        val = 600 - d
                        val_list.append(val)
                    bidder_offers[len(bidder_offers)] = val_list
            # 形成np.array,即竞拍者-拍品价值矩阵, 输入Auction_Self生成拍卖结果allocations, prices
            matrix = np.vstack(
                [bidder_offers[key] for key in sorted(bidder_offers.keys())]
            )
            allocations, _ = auction(matrix)
            allocations = list(allocations)
            # 设置决策智能体故障
            if region.MA_state[2] == 0:
                if random.random() < self.decide_fault_rate:
                    random.shuffle(allocations)
            # 只取allocations中不为-1的, 即为最后目标分配结果
            for ib, it in enumerate(allocations):
                if it == -1:
                    pass
                else:
                    s_bidder = bidders[ib]
                    s_item = items[it]
                    s_bidder.pre_target.append(s_item)
                    s_item.is_allocated = True
        # 实际要分配的打击单元
        alloc_att_agents = [
            agent
            for agent in self.connected_att_agents
            if (agent.is_commu == True) and (len(agent.target) < agent.max_target_load)
        ]
        # print("拍卖结束!，分配目标给%d个打击单元" % (len(alloc_att_agents)))
        # 对每个打击单元进行分配
        for agent in alloc_att_agents:
            if len(agent.pre_target) == 0:
                pass
            else:
                # 向通信网络请求连接并生成通信请求, attack_info
                attack_info_quest = C_Quest(
                    id=len(region.c_quests),
                    type=self.type,
                    info="attack_info",
                    send=self,
                    receive=agent,
                    start_time=t,
                )
                # 如果连的是同一个通信节点则通信请求直接完成
                region.c_quests.append(attack_info_quest)
