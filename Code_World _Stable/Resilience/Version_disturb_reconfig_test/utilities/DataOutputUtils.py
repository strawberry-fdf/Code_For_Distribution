import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np


# 数据滤波
def moving_average(data, window_size=5):
    window = np.ones(window_size) / window_size
    smoothed_data = np.convolve(data, window, mode="same")
    return smoothed_data


# 数据可视化类
class IndexBoard(object):
    def __init__(self, fault_label="无扰动注入"):
        # 名称
        self.name = ""
        # 类别
        self.type = ""
        # 数据库 dataframe格式
        self.dataframe = None
        # 字典-指标映射关系
        self.index_dict = {}
        # 初始需要作差的数据
        self.origin_dif_attr = []
        # 每固定间隔更新的数据初始化
        self.interval_dataframe_empty = None
        # 每固定间隔更新的数据
        self.interval_dataframe = None
        # 扰动注入情况
        self.fault_label = fault_label

    # 初始化
    def initial(self):
        self.dataframe = pd.DataFrame(
            columns=[
                "t",
                "grid_cover_rate",
                "decide_respond_rate",
                "eqg_mean_degree",
                "eqg_mean_betw",
                "eqg_mean_spl",
                "eqg_max_connect_num",
                "mean_weighted_degree",
                "max_connect_num",
                "load_link_num",
                "load_max_link_num",
                "quest_load_rate",
                "close_kc_num",
                "close_mean_time",
                "observe_efficiency",
                "decide_efficiency",
                "commun_efficiency",
            ]
        )

        # 任务层指标
        self.index_dict["close_kc_num"] = "杀伤链闭合速率"  # 单位时间内闭合的杀伤链数量
        self.index_dict["close_mean_time"] = "杀伤链平均闭合时间"  # 单位时间内闭合杀伤链的平均闭合时间
        # 协同层指标
        self.index_dict["grid_cover_rate"] = "区域侦察覆盖率"
        self.index_dict["observe_efficiency"] = "体系感知效率"
        self.index_dict["decide_respond_rate"] = "目标被响应率"
        self.index_dict["decide_efficiency"] = "体系锁敌效率"
        # 物理层指标
        self.index_dict["eqg_mean_degree"] = "装备网络平均度"
        self.index_dict["eqg_mean_betw"] = "装备网络平均介数"
        self.index_dict["eqg_mean_spl"] = "装备网络平均最短路径长度"
        self.index_dict["eqg_max_connect_num"] = "装备网络最大连通子团"

        self.index_dict["mean_weighted_degree"] = "通信网络平均加权度"
        self.index_dict["max_connect_num"] = "通信网络平均最大连通子团"
        self.index_dict["commun_efficiency"] = "通信效率"
        self.index_dict["load_link_num"] = "通信链路负载比例"
        self.index_dict["load_max_link_num"] = "通信链路满载比例"
        self.index_dict["quest_load_rate"] = "通信请求处理比例"

        self.origin_dif_attr = [0, 0, 0, 0, 0]

        self.interval_dataframe_empty = pd.DataFrame(
            columns=[
                "close_kc_num",
                "close_mean_time",
                "grid_cover_rate",
                "decide_respond_rate",
                "locked_num",
                "assigned_num",
                "finish_quest_num",
                "eqg_mean_degree",
                "eqg_mean_betw",
                "eqg_mean_spl",
                "eqg_max_connect_num",
                "mean_weighted_degree",
                "max_connect_num",
                "load_link_num",
                "load_max_link_num",
                "quest_load_rate",
            ]
        )

    # 更新字典
    def IndexUpdate(self, t, mean_attr, differ_attr):
        self.interval_dataframe = self.interval_dataframe_empty.copy()
        self.interval_dataframe.loc[len(self.interval_dataframe)] = mean_attr
        if t % 10 == 0:
            # 平均指标处理
            mean_result = [
                int(t) * 0.1,
                self.interval_dataframe["grid_cover_rate"].mean(),
                self.interval_dataframe["decide_respond_rate"].mean(),
                self.interval_dataframe["eqg_mean_degree"].mean(),
                self.interval_dataframe["eqg_mean_betw"].mean(),
                self.interval_dataframe["eqg_mean_spl"].mean(),
                self.interval_dataframe["eqg_max_connect_num"].mean(),
                self.interval_dataframe["mean_weighted_degree"].mean(),
                self.interval_dataframe["max_connect_num"].mean(),
                self.interval_dataframe["load_link_num"].mean(),
                self.interval_dataframe["load_max_link_num"].mean(),
                self.interval_dataframe["quest_load_rate"].mean(),
                # 分割需要处理的部分
                self.interval_dataframe["close_kc_num"].mean(),
                self.interval_dataframe["close_mean_time"].mean(),
                self.interval_dataframe["locked_num"].mean(),
                self.interval_dataframe["assigned_num"].mean(),
                self.interval_dataframe["finish_quest_num"].mean(),
            ]
            differ_mean_attr = mean_result[12:]
            # 作差指标
            differ_result = [
                differ_mean_attr[i] - self.origin_dif_attr[i]
                for i in range(len(self.origin_dif_attr))
            ]
            self.origin_dif_attr = differ_mean_attr
            # 全部指标汇总list
            all_result = mean_result[:12] + differ_result
            # 更新dataframe
            self.dataframe.loc[len(self.dataframe)] = all_result

    # 保存数据
    def IndexSave(self, save_path, r_time, d_mode, d_rate, reconfig, feature):
        # 处理一下数据
        self.dataframe["close_mean_time"] = (
            self.dataframe["close_mean_time"] / self.dataframe["close_kc_num"]
        )
        self.dataframe.to_csv(
            "%s/Data/IndexResult %s_%s_%s_%s_reconfig=%s.csv"
            % (save_path, feature, r_time, d_mode, str(d_rate), reconfig)
        )

    # 生成图
    def FigSave(self, save_path, r_time, d_mode, d_rate, reconfig, feature):
        # 构建图目录
        save_file_path = "%s/Index/%s_%s_%s_%s_reconfig=%s" % (
            save_path,
            feature,
            r_time,
            d_mode,
            str(d_rate),
            reconfig,
        )
        if os.path.exists(save_file_path):
            pass
        else:
            os.mkdir(save_file_path)
        # 保存图
        for k, v in self.index_dict.items():
            self.return_fig(self.fault_label, self.dataframe, k, v, save_file_path)

    # 单条数据结果图绘制
    def return_fig(self, attack_type, use_df, index, label, save_file_path):
        # 负载比例演化
        fig, ax1 = plt.subplots()

        x = list(use_df["t"])
        # 进行移动平均滤波
        smoothed_data = moving_average(list(use_df[index]))
        # 开头和尾部数据处理
        smoothed_data[0] = smoothed_data[1]
        smoothed_data[-1] = smoothed_data[-2]
        lns = ax1.plot(x, smoothed_data, "-o", color="blue", markersize=1, label=label)

        ax1.set_xlabel("体系仿真时间")
        ax1.set_ylabel(label)
        plt.legend()
        plt.savefig(
            "%s/%s-体系%s-体系仿真时间演化.png" % (save_file_path, attack_type, label),
            dpi=600,
        )
        plt.close()
