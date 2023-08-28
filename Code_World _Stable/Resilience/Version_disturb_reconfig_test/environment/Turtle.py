import numpy as np
import random


# turtle
class Turtle(object):
    def __init__(self):
        # 名称
        self.name = ""
        # x区间
        self.x = []
        # y区间
        self.y = []
        # z坐标
        self.z = 0
        # ceter x,y coord
        self.center = (0, 0)
        # point coord
        self.point = None
        # 被侦察状态
        self.is_observed = False
        # 被侦察的时刻
        self.latest_ob_t = 0
        # 时效性更新时间
        self.interval = random.randint(200, 250)
        # turtle内是否存在target
        self.has_target = False
        # turtle内target列表
        self.targets = []
        # turtle是否被侦察单元你锁定
        self.obs_lock = False
        # turtle被锁定
        self.always_observed = False

    # 生成用于平面绘制的参数
    def turtle_plot_slide(self):
        x_list = []
        y_list = []
        for xy in self.point:
            x = list(xy)[0]
            y = list(xy)[1]
            x_list.append(x)
            y_list.append(y)
        xx, yy = np.meshgrid([max(x_list), min(x_list)], [max(y_list), min(y_list)])
        zz = np.zeros(xx.shape) + self.z

        return xx, yy, zz

    # 判断智能体是否在该turtle内
    def is_agent_in_turtle(self, x, y):
        x_bool = (x >= self.x[0]) & (x <= self.x[1])
        y_bool = (y >= self.y[0]) & (y <= self.y[1])
        return x_bool & y_bool

    # 更新turtle
    def update_observe(self, region, t):
        # 更新turtle被侦察的时效性
        if self.always_observed:
            return
        if self.is_observed:
            if self.latest_ob_t + self.interval <= t:
                self.is_observed = False
        else:
            pass
        # 更新turtle下是否有目标
        locked_enemies = [
            enemy
            for enemy in self.targets
            if (enemy.locked == True) and (enemy.alive == True)
        ]
        if locked_enemies:
            self.has_target = True
        else:
            self.has_target = False
