from agents.Entity import Entity
from agents.Kill_Chain_Agent import *

import math
import numpy as np


# EntityAgent
class Enemy(Entity):
    def __init__(self):
        super(Enemy, self).__init__()
        # 名称
        self.name = ""
        # 类别
        self.type = ""
        # 可移动/固定
        self.movable = False
        # Z轴
        self.z = 0
        # 是否已被感知单元锁定
        self.locked = False
        # 是否存活
        self.alive = True
        # 速率
        self.velocity = None
        # 初始速度方向角
        self.velocity_angle = None
        # x方向速度
        self.vx = None
        # y方向速度
        self.vy = None
        # x方向加速度
        self.ax = None
        # y方向加速度
        self.ay = None
        # 是否携带武器
        self.weapon_is_loaded = False
        # 携带武器
        self.weapon = None
        # 待攻击目标
        self.target = None
        # 最小转弯半径
        self.r = None
        # 是否已被分配
        self.is_allocated = False
        # 是否已被执行
        self.is_assigned_to_attacker = False
        # 派给谁了
        self.attackeraimat = None
        # 是否已被导弹锁定
        self.is_locked_by_missile = False
        # 是否成功通信送至指控单元
        self.quest_success = False

    def lockon(self):
        theta = math.atan2(
            self.target.p_pos[1] - self.p_pos[1],
            self.target.p_pos[0] - self.p_pos[0],
        )
        self.vx = self.velocity * math.cos(theta)
        self.vy = self.velocity * math.sin(theta)

    def step(self, dt, xmin, ymin, xmax, ymax):
        # 计算敌人的新位置
        update_x = self.p_pos[0] + self.vx * dt
        update_y = self.p_pos[1] + self.vy * dt
        self.p_pos = [update_x, update_y]
        # 靠近地图边缘的边界处理
        if self.p_pos[0] < xmin:
            self.p_pos[0] = xmin
            self.vx = -self.vx
        elif self.p_pos[0] > xmax:
            self.p_pos[0] = xmax
            self.vx = -self.vx
        if self.p_pos[1] < ymin:
            self.p_pos[1] = ymin
            self.vy = -self.vy
        elif self.p_pos[1] > ymax:
            self.p_pos[1] = ymax
            self.vy = -self.vy


class Enemy_missle(Entity):
    def __init__(self):
        super(Enemy_missle, self).__init__()
        # 名称
        self.name = ""
        # 类别
        self.type = "enemy-missle"
        # 射程
        self.scope = None
        # 速度
        self.velocity = None
        # x方向速度
        self.vx = None
        # y方向速度
        self.vy = None
        # 待攻击目标
        self.target = None
        # 是否命中目标
        self.target_is_destroyed = False

    def lockon(self):
        theta = math.atan2(
            self.target.p_pos[1] - self.p_pos[1], self.target.p_pos[0] - self.p_pos[0]
        )
        self.vx = self.velocity * math.cos(theta)
        self.vy = self.velocity * math.sin(theta)

    def step(self, dt):
        update_x = self.p_pos[0] + self.vx * dt
        update_y = self.p_pos[1] + self.vy * dt
        self.p_pos = [update_x, update_y]
