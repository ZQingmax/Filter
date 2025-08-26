import numpy as np
from typing import Tuple

def exkrls(
    X: np.ndarray,
    D: np.ndarray,
    sigma: float = 1.0,
    delta: float = 1.0,
    lam: float = 0.99,
    ald_threshold: float = 1e-3,
    max_dict_size: int = 100
) -> Tuple[np.ndarray, np.ndarray, list, np.ndarray]:
    """
    Extended Kernel Recursive Least Squares (EX-KRLS)
    -------------------------------------------------
    参数:
        X : np.ndarray
            输入信号，形状 (N, d)，N 为样本数，d 为特征维度
        D : np.ndarray
            期望信号，形状 (N,)
        sigma : float
            RBF核参数
        delta : float
            初始正则化系数
        lam : float
            遗忘因子 (0 < lam <= 1)
        ald_threshold : float
            ALD (Approximate Linear Dependency) 阈值
        max_dict_size : int
            字典最大容量

    返回:
        Y : np.ndarray
            滤波输出 (N,)
        E : np.ndarray
            误差信号 (N,)
        dict_x : list
            最终字典中心
        alpha : np.ndarray
            系数向量
    """

    def kernel(x1, x2):
        return np.exp(-np.linalg.norm(x1 - x2) ** 2 / (2 * sigma ** 2))

    N = len(D)
    Y = np.zeros(N)
    E = np.zeros(N)
    dict_x = []
    alpha = np.array([])
    P = None

    for n in range(N):
        x_new = X[n].reshape(-1)

        # 初始化
        if len(dict_x) == 0:
            dict_x.append(x_new.copy())  # 修正：使用 .copy() 避免引用问题
            P = (1 / delta) * np.eye(1)
            alpha = np.array([D[n] / delta])
            Y[n] = D[n] / delta  # 修正：应该是预测值，不是期望值
            E[n] = D[n] - Y[n]   # 修正：计算正确的误差
            continue

        # 核向量
        k = np.array([kernel(x_new, c) for c in dict_x])
        y_pred = np.dot(alpha, k)
        e = D[n] - y_pred
        Y[n] = y_pred
        E[n] = e

        # ALD 判断 - 修正：需要先更新 P，再计算 delta_val
        # 对 P 进行遗忘因子更新
        P = P / lam
        
        # 计算 ALD 测试值
        Pk = P @ k
        delta_val = kernel(x_new, x_new) - k @ Pk
        
        if delta_val > ald_threshold and len(dict_x) < max_dict_size:
            # 新样本足够新颖，加入字典
            dict_x.append(x_new.copy())
            m = len(dict_x)

            # 使用 Woodbury 矩阵恒等式扩展 P
            # 新的 P 矩阵结构：
            # P_new = [[P + Pk*Pk'/delta_val, -Pk/delta_val],
            #          [-Pk'/delta_val,        1/delta_val]]
            P_new = np.zeros((m, m))
            P_new[:-1, :-1] = P + np.outer(Pk, Pk) / delta_val
            P_new[:-1, -1] = -Pk / delta_val
            P_new[-1, :-1] = -Pk / delta_val
            P_new[-1, -1] = 1 / delta_val
            P = P_new

            # 扩展 alpha
            alpha_new = np.zeros(m)
            alpha_new[:-1] = alpha
            alpha = alpha_new
            
            # 重新计算核向量（因为字典扩展了）
            k = np.array([kernel(x_new, c) for c in dict_x])

        # 计算增益向量 - 修正：使用更新后的 P 和 k
        Pk = P @ k
        denom = lam + k @ Pk
        if abs(denom) < 1e-12:  # 数值稳定性检查
            g = np.zeros_like(Pk)
        else:
            g = Pk / denom

        # 更新系数向量
        alpha += g * e

        # 更新逆协方差矩阵 P - 修正：标准 RLS 更新
        P = (P - np.outer(g, Pk)) / lam

        # 字典大小控制 - 在循环最后进行
        if len(dict_x) > max_dict_size:
            # 移除对应最小系数绝对值的样本
            idx_remove = np.argmin(np.abs(alpha))
            dict_x.pop(idx_remove)
            
            # 从 alpha 和 P 中移除对应的行/列
            alpha = np.delete(alpha, idx_remove)
            P = np.delete(np.delete(P, idx_remove, axis=0), idx_remove, axis=1)
            
            # 重新应用遗忘因子（因为删除操作可能影响矩阵性质）
            P = P * lam

    return Y, E, dict_x, alpha