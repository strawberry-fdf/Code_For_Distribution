# 定义杀伤链类，用于管理目标的杀伤进程
class Kill_Chain(object):
    def __init__(self):
        # 名称
        self.name = ""
        # 类别
        self.type = "Kill_Chain"
        # 杀伤链开始的目标
        self.enemy = None
        # 杀伤链开始时间
        self.s_time = 0
        # 杀伤链结束时间
        self.e_time = 0
        # 杀伤链所处状态 1=态势感知 2=指挥控制 3=火力打击 4=闭合
        self.stage = 0
        # 杀伤链闭合状态
        self.close = False
        # 杀伤链闭合时间
        self.close_time = 0
