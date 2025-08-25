import numpy as np
from typing import Tuple

def nlms(xn: np.ndarray, dn: np.ndarray, mu: float = 0.5, L: int = 4, delta: float = 1e-6) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    NLMS (Normalized Least Mean Squares) 算法实现

    参数:
        xn : np.ndarray
            输入信号 (N,)
        dn : np.ndarray
            期望信号 (N,)
        mu : float
            步长因子 (0 < mu < 2)
        L : int
            滤波器长度
        delta : float
            防止除零的小常数

    返回:
        yn : np.ndarray
            滤波器输出信号
        en : np.ndarray
            误差信号
        w_hist : np.ndarray
            每步滤波器权重 (N x L)
    """
    N = len(dn)
    yn = np.zeros(N)
    en = np.zeros(N)
    w = np.zeros(L)              # 初始化滤波器权重
    w_hist = np.zeros((N, L))    # 用于记录每步权重变化

    for n in range(L, N):
        x_vec = xn[n-L:n][::-1]              # 当前输入向量
        y = np.dot(w, x_vec)                 # 当前滤波器输出
        yn[n] = y
        e = dn[n] - y                        # 计算误差
        en[n] = e
        w = w + (mu / (np.dot(x_vec, x_vec) + delta)) * e * x_vec  # NLMS 更新
        w_hist[n, :] = w                     # 记录权重

    return yn, en, w_hist