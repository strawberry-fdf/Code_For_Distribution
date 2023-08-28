from agents.Attack_Agent import *
from agents.Command_Agent import *
from agents.Commun_Agent import *
from agents.Scount_Agent import *
from agents.Weapon_Agent import *
from agents.Enemy_Agent import *
from agents.Cloud_Agent import *

from utilities.VisualizationUtils import *
from utilities.DataOutputUtils import *

from environment.Region import *

import matplotlib.animation as anime
import time
from tqdm import tqdm


class Scenario(object):
    def __init__(
        self,
        sc_name,
        s_path,
        op_mode="only_data",
        total_time=1000,
        d_time=0,
        d_mode=None,
        d_rate=0,
        reconfig=False,
        feature=0,
    ):
        # 想定名称
        self.name = sc_name
        # 想定模式是否生成GIF仿真动画
        # only_data 即仅数据生成, data_gif 即生成GIF仿真动画
        self.output_mode = op_mode
        # 想定战场区域
        self.region = Region()
        # 想定总时长
        self.T = total_time
        # 结果保存路径
        self.path = os.path.join(s_path, "result")
        # 扰动开始时间 d_time=None即代表无扰动，其他则在对应时间开始扰动
        self.disturb_time = d_time
        # 扰动模式
        # "random_commun_network_link_attack"
        # "deliberate_commun_network_link_attack"
        # "terminal_agent_random_destroyed"
        # "terminal_agent_random_damaged"
        self.disturb_mode = d_mode
        # 扰动强度
        self.disturb_rate = d_rate
        # 是否重构
        self.reconfig = reconfig
        # 输入的9维向量
        self.feature = feature

    """
    战场区域基本设定：
    1 战场4等分
    2 SA_NUM, CA_NUM, AA_NUM分别为侦察、指控和打击单元数量
    3 侦察单元、打击单元默认为4的倍数
    4 指控单元仅有一个在战场中央
    """

    def initial_BattleField(
        self, CA_NUM, SA_NUM, AA_NUM, TARGET_NUM, MA_STATE, ARCH_STATE
    ):
        # 初始化战场
        self.region = Region()
        # 战场区域名称
        self.region.name = "G_00"
        # 区域边界
        self.region.xy = [(0, 0), (0, 400.0), (400.0, 400.0), (400.0, 0)]
        # 区域海拔
        self.region.z = 0
        # 是否重构 即是否启用云中心
        self.region.reconfig = self.reconfig
        # 初始化6个智能体的状态
        self.region.MA_state = MA_STATE
        # 初始化想定元素
        self.initial_Config(CA_NUM, SA_NUM, AA_NUM, TARGET_NUM)
        # 初始化云、边、端的状态
        if ARCH_STATE[0] == 0:
            for cc_agent in self.region.CC_Agents:
                cc_agent.cc_t = 100

        if ARCH_STATE[1] == 0:
            for mc_agent in self.region.MC_Agents:
                mc_agent.cc_t = 20

        if ARCH_STATE[2] == 0:
            # 备份终端调整状态
            for cc_agent in self.region.CC_Agents:
                for bu_sa in cc_agent.backup_scout_agent:
                    bu_sa.velocity = 8
                for bu_aa in cc_agent.backup_attack_agent:
                    bu_aa.velocity = 8
            # 初始终端调整状态
            for t_agent in self.region.Terminal_Agents:
                t_agent.velocity = 8

    def initial_Config(self, CA_NUM, SA_NUM, AA_NUM, TARGET_NUM):
        # 初始化智能体
        # 初始化4个指控单元（体系边缘云），在4个等分战场区域的中心位置
        coord_list = [(100, 100), (100, 300), (300, 300), (300, 100)]

        # 初始化区域下的网格
        self.region.initial_turtles(1600)
        # 边缘区块处理
        margin_grids = []
        margin_grids.extend(self.region.get_turtles_by_range([0, 10], [0, 400]))
        margin_grids.extend(self.region.get_turtles_by_range([390, 400], [0, 400]))
        margin_grids.extend(self.region.get_turtles_by_range([0, 400], [0, 10]))
        margin_grids.extend(self.region.get_turtles_by_range([0, 400], [390, 400]))

        for grid in margin_grids:
            grid.always_observed = True
            grid.is_observed = True

        # 调整边界
        # 边界余量
        md = 30
        margin_modify = [
            [0, 0, md, md],
            [0, -1 * md, md, 0],
            [(-1) * md, (-1) * md, 0, 0],
            [(-1) * md, 0, 0, md],
        ]
        # 初始化中心云
        cc_agent = CC_Agent()
        cc_agent.name = "%s_%s_%d" % (
            self.region.name,
            cc_agent.type,
            len(self.region.CC_Agents) + 1,
        )
        cc_agent.p_pos = [200, 200]
        self.region.CC_Agents.append(cc_agent)
        # 备份智能体
        # 6个备份侦察单元
        obs_backup_num = 16
        obs_agents = [OBS_T_Agent() for _ in range(obs_backup_num)]
        for obs_agent in obs_agents:
            obs_agent.name = "%s_%s_%s_%d" % (
                self.region.name,
                obs_agent.type,
                "backup",
                len(cc_agent.backup_scout_agent) + 1,
            )
            obs_agent.p_pos = [200, 200]
            obs_agent.vx = circle_rand_point(0, 0, 20, 0, 2 * pi)[0]
            obs_agent.vy = circle_rand_point(0, 0, 20, 0, 2 * pi)[1]
            cc_agent.backup_scout_agent.append(obs_agent)
        # 6个备份打击单元
        att_backup_num = 24
        ATT_Agents = [ATT_T_Agent() for _ in range(att_backup_num)]
        for att_t_agent in ATT_Agents:
            att_t_agent.name = "%s_%s_%s_%d" % (
                self.region.name,
                att_t_agent.type,
                "backup",
                len(cc_agent.backup_attack_agent) + 1,
            )
            att_t_agent.p_pos = [200, 200]
            # 打击智能体载弹量，目前设置载弹量10000
            att_t_agent.weapon = [MISSLE_T_Agent() for i in range(100000)]
            for k, missile in enumerate(att_t_agent.weapon):
                missile.name = "%s_%s_%d" % (
                    self.region.name,
                    missile.type,
                    k + 1,
                )
            att_t_agent.target = []
            cc_agent.backup_attack_agent.append(att_t_agent)

        # 每个区域下的指控单元个数
        for i, coord in enumerate(coord_list):
            mc_agents = [MC_Agent() for i in range(CA_NUM)]
            for mc_agent in mc_agents:
                mc_agent.name = "%s_%s_%d" % (
                    self.region.name,
                    mc_agent.type,
                    len(self.region.MC_Agents) + 1,
                )
                mc_agent.p_pos = list(coord)
                mc_agent.margin = [
                    coord[0] - 100 + margin_modify[i][0],
                    coord[1] - 100 + margin_modify[i][1],
                    coord[0] + 100 + margin_modify[i][2],
                    coord[1] + 100 + margin_modify[i][3],
                ]
                mc_agent.turtle_margin = [
                    coord[0] - 100,
                    coord[1] - 100,
                    coord[0] + 100,
                    coord[1] + 100,
                ]
                self.region.MC_Agents.append(mc_agent)
                cc_agent.MC_Agents.append(mc_agent)
                # 该区域下感知单元初始化
                obs_agents = [OBS_T_Agent() for _ in range(SA_NUM)]
                for obs_agent in obs_agents:
                    obs_agent.name = "%s_%s_%d" % (
                        self.region.name,
                        obs_agent.type,
                        len(self.region.OBS_T_Agents) + 1,
                    )
                    obs_agent.p_pos = [
                        coord[0],
                        coord[1],
                    ]
                    # 随机生成初始速度方向
                    obs_agent.vx = circle_rand_point(0, 0, 20, 0, 2 * pi)[0]
                    obs_agent.vy = circle_rand_point(0, 0, 20, 0, 2 * pi)[1]
                    obs_agent.mc_agent = mc_agent
                    obs_agent.margin = mc_agent.margin
                    mc_agent.OBS_T_Agents.append(obs_agent)
                    self.region.OBS_T_Agents.append(obs_agent)
                    self.region.Terminal_Agents.append(obs_agent)
                    # 初始感知区域设置
                    # 更新初始化下turtles的可见区域信息(指控单元附近半径30的圆内)
                    obs_recon_turtles = obs_agent.get_ocupy_turtle(self.region)
                    for turtle in obs_recon_turtles:
                        if turtle.is_observed:
                            pass
                        else:
                            turtle.always_observed = True
                            turtle.is_observed = True
                            turtle.latest_ob_t = 0

                # 该区域下打击单元初始化
                ATT_Agents = [ATT_T_Agent() for _ in range(AA_NUM)]
                for att_t_agent in ATT_Agents:
                    att_t_agent.name = "%s_%s_%d" % (
                        self.region.name,
                        att_t_agent.type,
                        len(self.region.ATT_Agents) + 1,
                    )
                    att_t_agent.p_pos = [
                        coord[0],
                        coord[1],
                    ]
                    # 打击智能体载弹量，目前设置载弹量10000
                    att_t_agent.weapon = [MISSLE_T_Agent() for i in range(100000)]
                    for k, missile in enumerate(att_t_agent.weapon):
                        missile.name = "%s_%s_%d" % (
                            self.region.name,
                            missile.type,
                            k + 1,
                        )
                    att_t_agent.target = []
                    att_t_agent.mc_agent = mc_agent
                    att_t_agent.margin = mc_agent.margin
                    self.region.ATT_Agents.append(att_t_agent)
                    mc_agent.ATT_Agents.append(att_t_agent)
                    self.region.Terminal_Agents.append(att_t_agent)

        # 初始化目标
        num_enemies = TARGET_NUM
        # 选择未被侦察的区域
        unobserved_turtles = [
            grid for grid in self.region.turtles if grid.is_observed == False
        ]
        # 随机选择一个unobserved_turtle
        select_grid = random.sample(unobserved_turtles, 400)
        enemies_xy = [
            (random.uniform(grid.x[0], grid.x[1]), random.uniform(grid.y[0], grid.y[1]))
            for grid in select_grid
        ]
        self.region.Enemies = [Enemy() for i in range(num_enemies)]
        for i, enemy in enumerate(self.region.Enemies):
            enemy.name = "T_%d" % i
            enemy.p_pos = (enemies_xy[i][0], enemies_xy[i][1])
            enemy_turtle = self.region.get_turtles_by_node(
                enemies_xy[i][0], enemies_xy[i][1]
            )[0]
            enemy_turtle.targets.append(enemy)

        # 构建通信网络
        self.region.c_network = C_Network()
        self.region.c_network.create_commun_net(self.region)

        # 初始化扰动
        self.region.disturb_robot = DisturbRobot(
            d_time=self.disturb_time, d_mode=self.disturb_mode, d_rate=self.disturb_rate
        )

    """
    暂时不完善，先不用
    通信网络基本设定：
    1 战场4等分
    2 SA_NUM, CA_NUM, AA_NUM分别为侦察、指控和打击单元数量
    3 侦察单元、打击单元默认为4的倍数
    4 指控单元仅有一个在战场中央
    """

    def initial_CommunNetwork(self):
        self.region.C_Nodes = [WLC_Node() for _ in range(4)]

    """
    仿真函数Simulation    
    """

    def Simulation(self):
        # 仅数据
        if self.output_mode == "only_data":
            # 初始化数据可视化类
            IB = IndexBoard()
            IB.initial()
            for i in tqdm(range(self.T)):
                t = i + 1
                mean_attr, differ_attr = self.region.step(t)
                IB.IndexUpdate(t, mean_attr, differ_attr)
            # 数据保存和结果图绘制
            r_time = time.strftime("%Y-%m%d %H-%M-%S", time.localtime())
            IB.IndexSave(
                self.path,
                r_time,
                self.disturb_mode,
                self.disturb_rate,
                self.reconfig,
                self.feature,
            )
            IB.FigSave(
                self.path,
                r_time,
                self.disturb_mode,
                self.disturb_rate,
                self.reconfig,
                self.feature,
            )
        # 数据和仿真可视化
        if self.output_mode == "data_gif":
            # 初始化仿真可视化类
            db = DrawBoard()
            db.initial()
            # 初始化数据可视化类
            IB = IndexBoard()
            IB.initial()
            # 动图初始化
            metadata = dict(title="Movie", artist="sourabh")
            writer = anime.PillowWriter(fps=30, metadata=metadata)
            # 构建图目录
            r_time = time.strftime("%Y-%m%d %H-%M-%S", time.localtime())
            save_file_path = "%s/Index/%s_%s_%s_reconfig=%s" % (
                self.path,
                r_time,
                self.disturb_mode,
                str(self.disturb_rate),
                self.reconfig,
            )
            if os.path.exists(save_file_path):
                pass
            else:
                os.mkdir(save_file_path)
            # 动画绘制和仿真循环
            with writer.saving(
                db.fig,
                "%s/Index/%s_%s_%s_reconfig=%s/simulation_%s.gif"
                % (
                    self.path,
                    r_time,
                    self.disturb_mode,
                    str(self.disturb_rate),
                    self.reconfig,
                    self.name,
                ),
                400,
            ):
                for i in tqdm(range(self.T)):
                    t = i + 1
                    # 获取各个画板
                    ax1, ax2 = db.ax_list
                    # 更新仿真过程动态
                    db.draw_update(self.region, t)
                    mean_attr, differ_attr = self.region.step(t)
                    IB.IndexUpdate(t, mean_attr, differ_attr)
                    writer.grab_frame()
                    # 更新仿真数据
                    # print("time %d fig save" % t)
                    db.title.remove()
                    ax1.cla()
                    ax2.cla()
                    plt.cla()
            # 数据保存和结果图绘制
            IB.IndexSave(
                self.path, r_time, self.disturb_mode, self.disturb_rate, self.reconfig
            )
            IB.FigSave(
                self.path, r_time, self.disturb_mode, self.disturb_rate, self.reconfig
            )

    """
    绘图测试用接口
    """

    def plot_test(self):
        # 数据和仿真可视化
        # 初始化可视化类
        db = DrawBoard()
        db.initial()
        db.draw_update(self.region, 1)
        plt.savefig("%s/Visualization/plot_test.png" % self.path, dpi=400)
