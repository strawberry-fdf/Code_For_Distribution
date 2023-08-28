from environment.Scenario import *

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 用来正常显示中文标签
plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号


if __name__ == "__main__":
    # 获取当前脚本所在文件夹的路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取当前工作目录的相对路径
    relative_path = os.path.relpath(current_dir)

    # 设置想定参数
    scen_name = "test"
    # 输出模式，output_mode = "data_gif"
    output_mode = "data_gif"
    # 仿真单位时间
    total_time = 1000
    # 扰动开始时间 d_time=None即代表无扰动，其他则在对应时间开始扰动
    d_time = 500
    # 扰动模式
    # "random_commun_network_link_attack"      随机通信链路攻击
    # "deliberate_commun_network_link_attack"  蓄意通信链路攻击
    # "terminal_agent_random_destroyed"        随机实体单元摧毁
    # "terminal_agent_random_damaged"          随机实体单元损伤（性能降级）
    """
    "random_commun_network_link_attack",
    "deliberate_commun_network_link_attack",
    "terminal_agent_random_destroyed",
    "terminal_agent_random_damaged",
    """
    d_mode_list = [
        "random_commun_network_link_attack",
        "deliberate_commun_network_link_attack",
    ]
    # 扰动强度
    d_rate_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    # 是否重构
    reconfig = True

    # 批量处理
    for d_mode in d_mode_list:
        for d_rate in d_rate_list:
            # 新建想定
            scen = Scenario(
                sc_name=scen_name,
                s_path=relative_path,
                op_mode=output_mode,
                total_time=total_time,
                d_time=d_time,
                d_mode=d_mode,
                d_rate=d_rate,
                reconfig=reconfig,
            )
            # 初始化想定，CA AA SA 是 1:4:4的关系
            scen.initial_BattleField(CA_NUM=1, SA_NUM=6, AA_NUM=8, TARGET_NUM=400)
            # 启动想定仿真
            scen.Simulation()

            print("扰动模式:%s,扰动强度:%s,仿真已完成！" % (d_mode, str(d_rate)))

    # 可视化调试
    # scen.plot_test()
