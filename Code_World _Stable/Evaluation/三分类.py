# -*- coding: utf-8 -*-

import numpy as np
import networkx as nx
import pandas as pd
from decimal import Decimal
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import chain
from sklearn.preprocessing import StandardScaler, Normalizer
import copy
import keras
import matplotlib.pyplot as plt
from keras.datasets import mnist
import numpy as np
import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import math
import random
import xlrd
import numpy as np
import sys
from sklearn.model_selection import train_test_split
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import copy
from sklearn import preprocessing
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn import metrics
import time
from sklearn.feature_selection import SelectKBest
import matplotlib.pylab as plt
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.feature_selection import f_classif, chi2, f_regression, mutual_info_classif
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn import tree
from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.cluster import SpectralClustering
from sklearn.cluster import DBSCAN
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import copy
import time
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import BayesianRidge
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    precision_recall_curve,
)
from sklearn.metrics import auc, roc_curve
import seaborn as sn
from sklearn.preprocessing import label_binarize
from sklearn.naive_bayes import GaussianNB
from imblearn.over_sampling import SMOTE


plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 用来正常显示中文标签
plt.rcParams["axes.unicode_minus"] = False  # 用来正常显示负号
#####################################进行监督学习#############################


############################定义指标函数##############################
def evaluation_index(y_true, y_predict):
    accuracy = accuracy_score(y_true, y_predict)
    recall = recall_score(y_true, y_predict, average="weighted")
    precision = precision_score(y_true, y_predict, average="weighted")
    f1 = f1_score(y_true, y_predict, average="weighted")
    df1 = pd.DataFrame([[accuracy, recall, precision, f1]])
    df1.columns = ["准确率", "召回率", "精准率", "F1值"]
    return df1


#####################定于ROC曲线函数#######################
def painting_roc(y_test, y_score, y_predict, label_name, number):
    # 二分类　ＲＯＣ曲线
    # roc_curve:真正率（True Positive Rate , TPR）或灵敏度（sensitivity）
    # 横坐标：假正率（False Positive Rate , FPR）
    fpr, tpr, thresholds_SVM = roc_curve(y_test, y_score)
    auc1 = auc(fpr, tpr)
    print("AUC : ", auc1)
    plt.figure()
    plt.plot([0, 1], [0, 1], "k--")
    plt.plot(fpr, tpr, label="%s (AUC = {:.3f})".format(auc1) % label_name)  #
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curve")
    plt.legend(loc="best")
    plt.show()
    # plt.savefig('H:\CSR科研\硕士毕业设计\交通拥堵数量预测\网中网识别预测\变化阈值_特征综合\图片/roc_%d.png'%number)


def painting_matrix(y_test, y_predict, number):
    plt.figure()
    sn.heatmap(confusion_matrix(y_test, y_predict), annot=True)
    plt.ylabel("True_value")
    plt.xlabel("Predict_value")
    plt.show()
    # plt.savefig('H:\CSR科研\硕士毕业设计\交通拥堵数量预测\网中网识别预测\变化阈值_特征综合\图片/matrix_%d.png'%number)


def jianduxuexi_fenlei(name, Feature_normalized, label_true_y, number):
    x_train, x_test, y_train, y_test = train_test_split(
        Feature_normalized,
        label_true_y,
        train_size=0.7,
        test_size=0.3,
        random_state=1,
        shuffle=True,
    )
    print("y_train.tolist().count(0)", y_train.tolist().count(0))
    print("y_train.tolist().count(1)", y_train.tolist().count(1))
    print("y_test.tolist().count(0)", y_test.tolist().count(0))
    print("y_test.tolist().count(1)", y_test.tolist().count(1))
    print("y_test.tolist().count(2)", y_test.tolist().count(2))

    if name == "Cluster_LR":
        # 逻辑回归分类
        # logisticRegression model
        Cluster_LR = linear_model.LogisticRegression()
        Cluster_LR.fit(x_train, y_train)
        y_predict = Cluster_LR.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_LR", df1)
        y_score = Cluster_LR.decision_function(x_test)
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'LR',number)

    elif name == "Cluster_DT":
        # 决策树分类(不需要数据缩放）
        Cluster_DT = DecisionTreeClassifier()
        Cluster_DT.fit(x_train, y_train)
        y_predict = Cluster_DT.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_DT", df1)
        y_score = Cluster_DT.predict_proba(x_test)[:, 1]
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'DT',number)

    elif name == "Cluster_SVM":
        # SVM分类
        Cluster_SVM = SVC(probability=True)
        Cluster_SVM.fit(x_train, y_train)
        y_predict = Cluster_SVM.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_SVM", df1)
        y_score = Cluster_SVM.predict_proba(x_test)[:, 1]
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'SVM',number)

    elif name == "Cluster_KNN":
        # KNN分类
        Cluster_KNN = KNeighborsClassifier()
        Cluster_KNN.fit(x_train, y_train)
        y_predict = Cluster_KNN.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_KNN", df1)
        target_names = ["class 0", "class 1", "class 2"]
        y_score = Cluster_KNN.predict_proba(x_test)[:, 1]
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'KNN',number)

    elif name == "Cluster_RF":
        # 随机森林分类（不需要数据缩放）
        Cluster_RF = RandomForestClassifier(random_state=1)
        Cluster_RF.fit(x_train, y_train)
        y_predict = Cluster_RF.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_RF", df1)
        y_score = Cluster_RF.predict_proba(x_test)[:, 1]
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'RF',number)

    elif name == "Cluster_GB":
        # 梯度提升决策树分类（不需要特征缩放）
        Cluster_GB = RandomForestClassifier()
        Cluster_GB.fit(x_train, y_train)
        y_predict = Cluster_GB.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_GB", df1)
        y_score = Cluster_GB.predict_proba(x_test)[:, 1]
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'GB',number)

    elif name == "Cluster_GNB":
        # 朴素贝叶斯分类
        Cluster_GNB = GaussianNB()
        Cluster_GNB.fit(x_train, y_train)
        y_predict = Cluster_GNB.predict(x_test)
        df1 = evaluation_index(y_test, y_predict)
        print("Cluster_GNB", df1)
        y_score = Cluster_GNB.predict_proba(x_test)[:, 1]
        print(
            "confusion_matrix(y_test1, y_predict1)", confusion_matrix(y_test, y_predict)
        )
        # painting_roc(y_test, y_score, y_predict, 'GNB',number)

    return df1, y_predict, y_score


####加载数
# f1 = open("Evaluation\\eval_data.csv", encoding="gbk")  # __after
df_1 = pd.read_csv("Evaluation\\eval_data.csv")
X1 = df_1.iloc[:, :6].values  # df_1.iloc[:,[0,1,2,3]].values
Y1 = np.array(list(df_1["韧性等级"]))
df1, y_predict1, y_score1 = jianduxuexi_fenlei("Cluster_LR", X1, Y1, 1)
print("===============================================================")
df2, y_predict11, y_score11 = jianduxuexi_fenlei("Cluster_DT", X1, Y1, 1)
print("===============================================================")
df3, y_predict, y_score = jianduxuexi_fenlei("Cluster_SVM", X1, Y1, 1)
print("===============================================================")
df4, y_predict122, y_score122 = jianduxuexi_fenlei("Cluster_KNN", X1, Y1, 1)
print("===============================================================")
df5, y_predict12, y_score12 = jianduxuexi_fenlei("Cluster_RF", X1, Y1, 1)
print("===============================================================")
df6, y_predict111, y_score111 = jianduxuexi_fenlei("Cluster_GB", X1, Y1, 1)
print("===============================================================")
df7, y_predict1111, y_score1111 = jianduxuexi_fenlei("Cluster_GNB", X1, Y1, 1)


##########汇总
df_zong = pd.DataFrame()
df_zong = df_zong.append(df1)
df_zong = df_zong.append(df2)
df_zong = df_zong.append(df3)
df_zong = df_zong.append(df4)
df_zong = df_zong.append(df5)
df_zong = df_zong.append(df6)
df_zong = df_zong.append(df7)
df_zong["Suanfa"] = ["逻辑回归", "决策树", "SVM", "KNN", "随机森林", "梯度提升决策树", "朴素贝叶斯"]
print("df_zong", df_zong)

######嵌入式SelectFromModel
model = SelectFromModel(estimator=ExtraTreesClassifier(random_state=1)).fit(X1, Y1)
# print('selector.estimator_.coef_',model.estimator_.feature_importances_)
print(list(model.estimator_.feature_importances_))

# 创建画布和坐标轴
fig, ax = plt.subplots()
# plt.scatter(
#     df_1.columns[:6], list(model.estimator_.feature_importances_), c="RED", marker="."
# )
ax.bar(df_1.columns[:6], list(model.estimator_.feature_importances_), color="blue")
# 设置坐标轴标签
ax.set_xlabel("关键要素", fontsize=12, weight="bold")
ax.set_ylabel("关键要素对体系韧性的贡献率", fontsize=12, weight="bold")

# 设置标题
ax.set_title("关键要素对体系韧性的影响程度", fontsize=15, weight="bold")
# plt.plot(list(range(1, 9)), list(model.estimator_.feature_importances_), c='RED')
plt.show()
