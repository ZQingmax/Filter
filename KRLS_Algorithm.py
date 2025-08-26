import numpy as np
from typing import Callable, List, Tuple

def krls(
    X: np.ndarray,
    d: np.ndarray,
    sigma: float = 1.0,
    ald_threshold: float = 1e-4,
    delta: float = 1e-6,
    kernel: Callable[[np.ndarray, np.ndarray], float] | None = None,
) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray], np.ndarray]:
    """
    KRLS (Kernel Recursive Least-Squares) with ALD sparsification.
    
    参数:
        X : (N, d) 输入样本
        d : (N,)   期望输出
        sigma :    高斯核宽度（仅当使用默认核时）
        ald_threshold : ALD 新颖度阈值，越大字典越小
        delta :    对角正则，提升数值稳定性
        kernel :   自定义核函数 kernel(x, y) -> float；若 None 则使用 RBF
    
    返回:
        y : (N,)           逐时刻预测
        e : (N,)           逐时刻误差
        dict_x : list      字典（支持向量）列表
        alpha : (M,)       结束时对应字典的系数（M 为最终字典规模）
    """
    if kernel is None:
        # 修正：将 sigma 作为自由变量而不是默认参数
        def kernel_func(x: np.ndarray, y: np.ndarray) -> float:
            diff = x - y
            return float(np.exp(-np.dot(diff, diff) / (2.0 * sigma * sigma)))
        kernel = kernel_func

    N, d_dim = X.shape
    y = np.zeros(N)
    e = np.zeros(N)

    dict_x: List[np.ndarray] = []
    alpha = np.zeros(0)       # 系数向量，对应 dict_x
    P = np.zeros((0, 0))      # 逆核矩阵（K^{-1}），随字典增长递推维护

    for n in range(N):
        x_n = X[n]

        if len(dict_x) == 0:
            # 初始化：第一点直接加入字典
            kappa = kernel(x_n, x_n) + delta
            dict_x.append(x_n.copy())
            P = np.array([[1.0 / kappa]])          # (1x1)
            alpha = np.array([d[n] / kappa])       # 初始系数
            y[n] = 0.0                             # 第一时刻先验输出为 0
            e[n] = d[n] - y[n]
            continue

        # 计算与现有字典的核向量 k 以及当前预测
        k_vec = np.array([kernel(x_n, c) for c in dict_x])   # (M,)
        y_hat = float(k_vec @ alpha)
        y[n] = y_hat
        e[n] = d[n] - y_hat

        # ALD 新颖度检验：s = κ(x,x) + δ - k^T P k
        kappa = kernel(x_n, x_n) + delta
        q = P @ k_vec                  # (M,)
        s = float(kappa - k_vec @ q)   # 标量

        if s > ald_threshold:
            # ---- 新点足够新颖：扩展字典 ----
            # 扩展 P（块矩阵的 Woodbury/Schur 逆更新）
            M = len(dict_x)
            P_new = np.empty((M + 1, M + 1))
            P_new[:M, :M] = P + np.outer(q, q) / s
            P_new[:M, M]  = -q / s
            P_new[M, :M]  = -q / s  # 修正：去掉不必要的 .T
            P_new[M, M]   = 1.0 / s
            P = P_new

            # 扩展 alpha，并进行 RLS 增益更新
            # 增益向量 h = [q; -1] / s
            h = np.concatenate([q, np.array([-1.0])]) / s
            alpha = np.concatenate([alpha, np.array([0.0])]) + h * e[n]

            # 把新样本加入字典
            dict_x.append(x_n.copy())
        else:
            # ---- 不新颖：仅做系数与 P 的 RLS 更新（不扩展字典） ----
            # 修正：确保分母不为零
            k_T_q = float(k_vec @ q)
            denom = 1.0 + k_T_q
            
            if abs(denom) < 1e-12:  # 数值稳定性检查
                # 如果分母接近零，跳过更新或使用备选策略
                continue
                
            g = q / denom
            alpha = alpha + g * e[n]
            P = P - np.outer(g, q)

    return y, e, dict_x, alpha

