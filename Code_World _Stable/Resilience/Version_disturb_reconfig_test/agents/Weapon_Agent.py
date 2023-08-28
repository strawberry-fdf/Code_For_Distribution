from agents.Entity import Entity
from agents.Kill_Chain_Agent import *

import math
from math import *


# T:Terminal Agent 终端智能体
class T_Agent(Entity):
    def __init__(self):
        super(T_Agent, self).__init__()
        # 可移动
        self.movable = True
        # 可通信
        self.communicative = True
        # 通信范围
        self.commun_scope = 50
        # 速度
        self.vx = None
        self.vy = None
        # 加速度【暂时不用】
        self.ax = 0
        self.ay = 0
        # 物理故障状态（主要强调故障时的速度减缓）
        self.p_fault_state = False
        # 物理故障程度（与速度之间呈反比）
        self.p_fault_degree = 0


class MISSLE_T_Agent(T_Agent):
    def __init__(self):
        super(MISSLE_T_Agent, self).__init__()
        # 明确属性
        self.type = "missle"
        # 弹药射程
        self.scope = None
        # 速度
        self.velocity = 80
        # 待攻击目标
        self.target = None
        # 是否命中目标
        self.detonate = False
        # 是否消耗
        self.used = False

    def lockon(self):
        theta = math.atan2(
            self.target.p_pos[1] - self.p_pos[1], self.target.p_pos[0] - self.p_pos[0]
        )
        self.vx = self.velocity * math.cos(theta)
        self.vy = self.velocity * math.sin(theta)

    def step(self, region, t):
        # 判定武器是否被消耗
        if self.detonate and not self.used:
            self.used = True
        # 击杀
        if (
            sqrt(
                pow(self.target.p_pos[0] - self.p_pos[0], 2)
                + pow(self.target.p_pos[1] - self.p_pos[1], 2)
            )
            < 5
            and self.detonate == False
        ):
            self.detonate = True
            self.target.alive = False
            switch_kill_chain = [
                kc for kc in region.kill_chains if kc.name == self.target.name
            ][0]
            switch_kill_chain.stage = 4
            switch_kill_chain.close = True
            switch_kill_chain.e_time = t
            switch_kill_chain.close_time = (
                switch_kill_chain.e_time - switch_kill_chain.s_time
            )
        # 移动
        update_x = self.p_pos[0] + self.vx * region.dt
        update_y = self.p_pos[1] + self.vy * region.dt
        self.p_pos = [update_x, update_y]
