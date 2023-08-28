from scipy.spatial import KDTree

"""
通信请求类别：
感知——>指控（边缘云）
scount, enemy_info: 指控单元更新目标态势
scount, mobile_quest: 指控单元反馈未侦察区域给感知单元
指控（边缘云）——>感知
mc, mobile_info: 感知单元获得机动坐标
指控（边缘云）——>打击
mc, attack_info: 打击单元更新待打击目标列表
指控（边缘云）——>中心云
mc, area_info: 中心云更新全局态势
中心云——>指控（边缘云）
cc, reconfig_info: 对应的边缘云调整单元
"""


# 通信请求类
class C_Quest(object):
    def __init__(
        self, id="", type=None, info=None, send=None, receive=None, start_time=0
    ):
        # 通信请求唯一标识符
        self.id = id
        # 通信请求发送方连接的通信节点
        self.source = send.c_node_connected_to.name
        # 通信请求接收方连接的通信节点
        self.target = receive.c_node_connected_to.name
        # 实际od路径
        self.od_path = []
        # 预测od路径
        self.od_path_predict = []
        # quest状态 0未配流 1通信中 2通信完成 3通信后置任务完成
        self.state = 0
        # 通信请求发起时间
        self.start_time = start_time
        # 实际通信到达所需时间
        self.real_span = 99999999999999
        # 预计通信到达所需时间
        self.predict_span = 99999999999999
        # 暂时弃用
        # 通信请求类别
        self.type = type
        # 通信请求信息
        self.info = info
        # 通信请求发送方（O）
        self.send = send
        # 通信请求接收方（D）
        self.receive = receive
        # 维护通信内容
        self.data = None
        # 非卫星通信时间
        self.special_ctime = 3

    def update_quest(self, region, t):
        # 对于一直保持state=0状态的通信,更新通信两端的通信节点
        if self.state == 0:
            if self.send.is_commu and self.receive.is_commu:
                self.source = self.send.c_node_connected_to.name
                self.target = self.receive.c_node_connected_to.name

        # 如果和边缘云接入一个节点, 需要4个仿真步长完成通信
        if (self.state != 3) and (self.source == self.target):
            if self.special_ctime != 0:
                self.special_ctime -= 1
            else:
                self.special_ctime = 0
                self.state = 2
        # 表示当前通信请求未完成
        if self.state == 2:
            # 在通信请求完成的情况下，判断距离是哪类请求完成前置动作
            if self.type == "scout":
                if self.info == "mobile_quest":
                    self.quest_scount_mobile_quest(region, t)
                elif self.info == "enemy_info":
                    self.quest_scount_enemy_info(region)
                else:
                    pass
            elif self.type == "attack":
                if self.info == "force_info":
                    self.quest_attack_force_info()
                else:
                    pass
            elif self.type == "mc":
                if self.info == "mobile_info":
                    self.quest_mc_mobile_info(region)
                elif self.info == "attack_info":
                    self.quest_mc_attack_info()
                elif self.info == "area_info":
                    self.quest_mc_area_info(self, region, t)
                else:
                    pass
            elif self.type == "cc":
                if self.info == "reconfig_info":
                    self.quest_cc_reconfig_info(self, region, t)
                else:
                    pass
            # 通信后置任务已完成
            self.state = 3

    # 感知——>指控（边缘云）
    # scount, enemy_info: 指控单元更新目标态势
    def quest_scount_enemy_info(self, region):
        self.receive.locked_enemies.extend(self.data)
        for enemy in self.data:
            enemy.quest_success = True
        # 侦察单元回传目标信息，对应杀伤链转换为 stage=2 指挥控制
        for enemy in self.data:
            switch_kill_chain = [
                kc for kc in region.kill_chains if kc.name == enemy.name
            ][0]
            switch_kill_chain.stage = 2
        return

    # scount, mobile_quest: 指控单元反馈未侦察区域给感知单元
    def quest_scount_mobile_quest(self, region, t):
        receive_agent = self.receive
        mobile_info_quest = C_Quest(
            id=len(region.c_quests),
            type=receive_agent.type,
            info="mobile_info",
            send=self.receive,
            receive=self.send,
            start_time=t,
        )
        # 如果连的是同一个通信节点则通信请求直接完成
        region.c_quests.append(mobile_info_quest)
        return

    # 指控（边缘云）——>感知
    # mc, mobile_info: 感知单元获得机动坐标
    def quest_mc_mobile_info(self, region):
        x_range = [self.send.margin[0], self.send.margin[2]]
        y_range = [self.send.margin[1], self.send.margin[3]]
        # 构建当前未探测且未被锁定的mc_agent管辖下所有turtle的坐标集合
        mc_turtles = region.get_turtles_by_range(x_range, y_range)
        # print(self.send.name, len(mc_turtles), x_range, y_range)
        all_unobs_turtles_xy = [
            turtle.center
            for turtle in mc_turtles
            if (turtle.is_observed == False) and (turtle.obs_lock == False)
        ]
        if self.receive.commun_waiting:
            # 如果所有turtle均被探测，则原地待命
            if len(all_unobs_turtles_xy) == 0:
                self.receive.t_area = 0
            else:
                # 构建kd-tree 实现快速检索
                tree = KDTree(all_unobs_turtles_xy)
                # 查询最近点的索引
                _, min_index = tree.query(
                    [(self.receive.p_pos[0], self.receive.p_pos[1])]
                )
                # 计算朝向的方向
                tx, ty = (
                    all_unobs_turtles_xy[min_index[0]][0],
                    all_unobs_turtles_xy[min_index[0]][1],
                )
                # 设置目标区域turtle
                self.receive.t_area = region.get_turtles_by_node(tx, ty)[0]
        else:
            pass
        return

    # 打击——>指控（边缘云）
    def quest_attack_force_info(self):
        self.receive.connected_att_agents.append(self.send)
        return

    # 指控（边缘云）——>打击
    # mc, attack_info: 打击单元更新待打击目标列表
    def quest_mc_attack_info(self):
        self.receive.target = self.receive.pre_target.copy()
        self.receive.pre_target = []
        return

    # 指控（边缘云）——>中心云
    # mc, area_info: 中心云更新全局态势
    def quest_mc_area_info(self, region, t):
        return

    # 中心云——>指控（边缘云）
    # cc, reconfig_info: 对应的边缘云调整单元
    def quest_cc_reconfig_info(self, region, t):
        return
