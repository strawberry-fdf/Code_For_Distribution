"""
实体对象类定义，包括：
基本类Entity
"""


# EntityAgent
class Entity(object):
    def __init__(self):
        # 名称
        self.name = "None"
        # 类别
        self.type = ""
        # 可移动/固定
        self.movable = False
        # 位置
        self.p_pos = None
        # Z轴
        self.z = 0
        # 故障状态
        self.fault = False
        # 备份单元是否被使用
        self.used = False
