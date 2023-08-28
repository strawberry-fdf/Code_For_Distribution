from utilities.CommonUtils import *

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle
import matplotlib.cm as cm
import networkx as nx


class DrawBoard(object):
    def __init__(self):
        # 名称
        self.name = ""
        # 类别
        self.type = ""
        # 画板列表
        self.ax_list = []
        # fig保存
        self.fig = None
        # title保存
        self.title = None
        # cbar
        self.cbar = None

    # 初始化
    def initial(self):
        # 创建一个宽为10英寸，高为6英寸的画布
        fig = plt.figure(figsize=(12, 5))
        self.fig = fig
        # 创建包含4个子图位置的网格
        gs = GridSpec(1, 2, width_ratios=[1, 1])

        # 为左边子图指定位置
        gs_left = gs[:1, :1]
        ax1 = plt.subplot(gs_left)

        # 为右边子图指定位置
        gs_right = gs[:1, 1:]
        ax2 = plt.subplot(gs_right)
        # 添加colorbar
        load_cmap = cm.get_cmap("Greens")  # 通信负载量的颜色映射
        sm = cm.ScalarMappable(cmap=load_cmap, norm=plt.Normalize(vmin=0, vmax=5))
        sm.set_array([])  # 设置一个空数组
        self.cbar = plt.colorbar(sm, ax=ax2, label="Communication Load")

        # 调整子图间距
        # plt.subplots_adjust(wspace=0.4, hspace=0.4)
        self.ax_list = [ax1, ax2]

    # 绘图更新
    def draw_update(self, region, t):
        # 调整战场可视化格式
        ax1 = self.ax_list[0]
        ax2 = self.ax_list[1]

        self.title = self.fig.text(
            0.5,
            0.94,
            "仿真时间 t = %.1f" % (int(t) * 0.1),
            ha="center",
            va="center",
            fontweight="bold",
            fontsize=12,
        )

        # ax1 绘制网格
        self.draw_turtles(region, ax1)

        # ax1 绘制通信链接
        self.draw_quest(region, ax1)

        # ax1 绘制agent
        self.draw_local_agent(region, ax1)

        # ax1 绘制目标
        self.draw_enemy(region, ax1)

        # ax2 绘制通信网络
        self.draw_network(region, ax2)

        # 调整子图间距
        # plt.subplots_adjust(wspace=0.4, hspace=1)
        plt.axis("equal")
        plt.axis("on")

    # 绘制网格grid
    def draw_turtles(self, region, ax):
        # plot turtles
        for n, grid in enumerate(region.turtles):
            x, y = zip(*grid.point)
            x1 = grid.x[0]
            y1 = grid.y[0]
            width1 = grid.x[1] - grid.x[0]
            height1 = grid.y[1] - grid.y[0]
            if grid.has_target:
                rect = Rectangle(
                    (x1, y1),
                    width1,
                    height1,
                    color="#BF7E78",
                    edgecolor=None,
                    linewidth=0,
                    alpha=0.5,
                )
            else:
                # 如果True即代表该gird已经被侦察过
                if grid.is_observed:
                    rect = Rectangle(
                        (x1, y1),
                        width1,
                        height1,
                        color="white",
                        edgecolor=None,
                        linewidth=0,
                    )
                # 如果False即未被侦察
                else:
                    rect = Rectangle(
                        (x1, y1),
                        width1,
                        height1,
                        color="gray",
                        edgecolor=None,
                        linewidth=0,
                        alpha=0.2,
                    )
            ax.add_patch(rect)

    # 绘制通信链接quest
    def draw_quest(self, region, ax):
        # 绘制通信效果
        # 卫星通信
        for _, quest in enumerate(region.c_quests):
            # 绘制接入通信网络的连边
            if quest.state == 1:
                send_pos = quest.send.p_pos
                receive_pos = quest.receive.p_pos
                ax.plot(
                    [send_pos[0], receive_pos[0]],
                    [send_pos[1], receive_pos[1]],
                    marker="",
                    color="green",
                    markersize=1,
                    linewidth=1,
                    linestyle="dashed",
                )
        # 地面有线通信
        for cc_agent in region.CC_Agents:
            for mc_agent in cc_agent.MC_Agents:
                ax.plot(
                    [cc_agent.p_pos[0], mc_agent.p_pos[0]],
                    [cc_agent.p_pos[1], mc_agent.p_pos[1]],
                    marker="",
                    color="green",
                    markersize=1,
                    linewidth=1,
                    linestyle="solid",
                )
        # 目标锁定链路
        for att_agent in region.ATT_Agents:
            if att_agent.destination:
                ax.plot(
                    [att_agent.p_pos[0], att_agent.destination.p_pos[0]],
                    [att_agent.p_pos[1], att_agent.destination.p_pos[1]],
                    marker="",
                    color="red",
                    markersize=1,
                    linewidth=1,
                    linestyle="dashed",
                )

    # 绘制单元agent（一个mc_agent对应一个区域）
    def draw_local_agent(self, region, ax):
        # 各区域下指控单元
        for cc_agent in region.CC_Agents:
            ax.plot(
                cc_agent.p_pos[0],
                cc_agent.p_pos[1],
                marker="D",
                color="#72F2EB",
                markersize=8,
                mec="black",
                mew=0.5,
                zorder=2,
            )
            ax.text(
                cc_agent.p_pos[0],
                cc_agent.p_pos[1],
                "CC",
                color="black",
                fontsize=3,
                ha="center",
                va="center",
                weight="bold",
                zorder=2,
            )

        for i, mc_agent in enumerate(region.MC_Agents):
            ax.plot(
                mc_agent.p_pos[0],
                mc_agent.p_pos[1],
                marker="h",
                color="#00CCBF",
                markersize=8,
                mec="black",
                mew=0.5,
                zorder=2,
            )
            ax.text(
                mc_agent.p_pos[0],
                mc_agent.p_pos[1],
                "MC",
                color="black",
                fontsize=3,
                ha="center",
                va="center",
                weight="bold",
                zorder=2,
            )
            ax.text(
                mc_agent.p_pos[0],
                mc_agent.p_pos[1] + 10,
                "%s" % (mc_agent.c_node_connected_to.name),
                color="black",
                fontsize=3,
                ha="center",
                va="center",
                zorder=1,
            )
            # 各区域下感知单元
            for i, obs_t_agent in enumerate(mc_agent.OBS_T_Agents):
                ax.plot(
                    obs_t_agent.p_pos[0],
                    obs_t_agent.p_pos[1],
                    marker="h",
                    color="blue",
                    markersize=5,
                    mec="black",
                    mew=0.5,
                    zorder=1,
                )
                ax.text(
                    obs_t_agent.p_pos[0],
                    obs_t_agent.p_pos[1],
                    "O",
                    color="white",
                    fontsize=3,
                    ha="center",
                    va="center",
                    zorder=1,
                )
                ax.text(
                    obs_t_agent.p_pos[0],
                    obs_t_agent.p_pos[1] + 5,
                    "%s %s %s %s"
                    % (
                        obs_t_agent.mode,
                        obs_t_agent.is_commu,
                        obs_t_agent.c_node_connected_to.name,
                        obs_t_agent.nearest_c_node.name,
                    ),
                    color="black",
                    fontsize=3,
                    ha="center",
                    va="center",
                    zorder=1,
                )
                circle = Circle(
                    (obs_t_agent.p_pos[0], obs_t_agent.p_pos[1]),
                    obs_t_agent.obs_scope,
                    alpha=0.1,
                )  # 创建半透明圆形
                circle.set_facecolor("blue")
                ax.add_patch(circle)  # 添加到图上

            # 绘制打击智能体
            for i, att_t_agent in enumerate(mc_agent.ATT_Agents):
                ax.plot(
                    att_t_agent.p_pos[0],
                    att_t_agent.p_pos[1],
                    marker="h",
                    color="yellow",
                    markersize=5,
                    mec="black",
                    mew=0.5,
                    zorder=1,
                )  # 绘制中心点
                ax.text(
                    att_t_agent.p_pos[0],
                    att_t_agent.p_pos[1],
                    "A",
                    color="black",
                    fontsize=3,
                    ha="center",
                    va="center",
                    zorder=1,
                )
                # 绘制打击单元状态信息
                assigned_target = [
                    t for t in att_t_agent.target if t.is_assigned_to_attacker == False
                ]
                ax.text(
                    att_t_agent.p_pos[0],
                    att_t_agent.p_pos[1] + 5,
                    "%d %d/3 %d/3 %d/3"
                    % (
                        att_t_agent.workingmode,
                        len(att_t_agent.pre_target),
                        len(att_t_agent.target),
                        len(assigned_target),
                    ),
                    color="black",
                    fontsize=3,
                    ha="center",
                    va="center",
                    zorder=1,
                )
                # 绘制打击单元通信讯息
                if att_t_agent.c_node_connected_to:
                    ax.text(
                        att_t_agent.p_pos[0],
                        att_t_agent.p_pos[1] + 10,
                        "%s %s %s"
                        % (
                            att_t_agent.c_node_connected_to.name,
                            att_t_agent.is_commu,
                            att_t_agent.nearest_c_node.name,
                        ),
                        color="black",
                        fontsize=3,
                        ha="center",
                        va="center",
                        zorder=1,
                    )
                else:
                    ax.text(
                        att_t_agent.p_pos[0],
                        att_t_agent.p_pos[1] + 10,
                        "None",
                        color="black",
                        fontsize=3,
                        ha="center",
                        va="center",
                        zorder=1,
                    )
        # 绘制我方导弹
        for i, missile in enumerate(region.missile_launched):
            if missile.detonate == False:
                ax.plot(
                    missile.p_pos[0],
                    missile.p_pos[1],
                    marker="o",
                    color="orange",
                    markersize=2,
                )  # 绘制中心点
            else:
                if missile.used == False:
                    # 绘制击杀效果
                    ax.plot(
                        missile.target.p_pos[0],
                        missile.target.p_pos[1],
                        marker="o",
                        color="red",
                        markersize=10,
                        alpha=0.5,
                    )

    # 绘制目标
    def draw_enemy(self, region, ax):
        # plot enemy
        for i, enemy in enumerate(region.Enemies):
            # 如果存活，则可视化
            if enemy.alive:
                ax.plot(
                    enemy.p_pos[0],
                    enemy.p_pos[1],
                    marker="v",
                    color="black",
                    markersize=1,
                )
                if enemy.is_allocated:
                    ax.text(
                        enemy.p_pos[0],
                        enemy.p_pos[1] + 3,
                        "alloc",
                        color="black",
                        fontsize=3,
                        ha="center",
                        va="center",
                    )
                if enemy.locked:
                    ax.plot(
                        enemy.p_pos[0],
                        enemy.p_pos[1],
                        marker="v",
                        color="blue",
                        markersize=1,
                    )
                if enemy.quest_success:
                    ax.plot(
                        enemy.p_pos[0],
                        enemy.p_pos[1],
                        marker="v",
                        color="red",
                        markersize=1,
                    )

    # 绘制通信网络
    def draw_network(self, region, ax):
        # 绘制每个通信节点的通信范围
        # for c_node in region.C_Nodes:
        #     circle = Circle(
        #         (c_node.p_pos[0], c_node.p_pos[1]), c_node.commun_scope, alpha=0.2
        #     )  # 创建半透明圆形
        #     circle.set_facecolor("green")
        #     ax.add_patch(circle)  # 添加到图上
        # 基于nx绘制网络
        active_colors = {True: "green", False: "black"}  # 激活节点的颜色映射
        node_colors = [
            active_colors[data["active"]]
            for _, data in region.c_network.G.nodes(data=True)
        ]
        load_cmap = cm.get_cmap("Greens")  # 通信负载量的颜色映射
        # 绘制底图节点和连边
        nx.draw(
            region.c_network.G,
            region.c_network.pos,
            ax=ax,
            with_labels=True,
            node_color="white",
            edgecolors=node_colors,
            linewidths=4,
            node_size=200,
            font_size=5,
            edge_color="black",
            width=4,
        )
        # 绘制连边
        # 绘制连边，并使用colorbar显示通信负载量
        edge_loads = [
            data["Mission_Load_Real"]
            for _, _, data in region.c_network.G.edges(data=True)
        ]
        edge_colors = [load_cmap(load / 5) for load in edge_loads]
        nx.draw_networkx_edges(
            region.c_network.G,
            region.c_network.pos,
            ax=ax,
            edge_color=edge_colors,
            width=2,
        )
