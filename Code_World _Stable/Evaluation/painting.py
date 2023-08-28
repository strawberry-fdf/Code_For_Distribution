import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 用来正常显示中文标签
plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号
# 创建数据
data = {
    "准确率": [0.55, 0.80, 0.85, 0.65, 0.85, 0.85, 0.70],
    "召回率": [0.55, 0.80, 0.85, 0.65, 0.85, 0.85, 0.70],
    "精准率": [0.535, 0.80, 0.85375, 0.653333, 0.85375, 0.85375, 0.73],
    "F1值": [0.539542, 0.80, 0.848366, 0.649595, 0.848366, 0.848366, 0.681979],
    "Suanfa": ["逻辑回归", "决策树", "SVM", "KNN", "随机森林", "梯度提升决策树", "朴素贝叶斯"],
}

df = pd.DataFrame(data)

# 设置柱形图颜色
colors = ["#C43302", "#EDAA25", "#B7BF99", "#0A7373"]

# 设置图例标签
legend_labels = ["准确率", "召回率", "精准率", "F1值"]

# 创建画布和坐标轴
fig, ax = plt.subplots(figsize=(10, 6))

# 设置柱形图宽度
bar_width = 0.2

# 循环绘制柱形图
for i, label in enumerate(legend_labels):
    x = np.arange(len(df["Suanfa"]))  # 生成x轴位置
    x_offset = (i - 1.5) * bar_width  # 计算偏移量
    ax.bar(x + x_offset, df[label], width=bar_width, color=colors[i], label=label)

    # 在每个柱形图上方标注具体数值
    if i == 0:
        for j, value in enumerate(df[label]):
            ax.text(
                x[j] + x_offset + 0.1,
                value + 0.01,
                "准确率=%s" % str(value),
                ha="center",
                weight="bold",
            )

# 设置图例
ax.legend()

# 设置坐标轴标签
ax.set_xlabel("模型类别", fontsize=15, weight="bold")
ax.set_ylabel("指标值", fontsize=15, weight="bold")

# 设置标题
ax.set_title("基于集成学习的体系韧性评估模型性能指标", fontsize=15, weight="bold")

# 设置x轴刻度
ax.set_ylim(0, 1)
ax.set_xticks(np.arange(len(df["Suanfa"])))
ax.set_xticklabels(df["Suanfa"])

# 自动调整横坐标的位置，避免重叠
# plt.xticks(rotation=30, ha="right")

# 显示图形
plt.show()
