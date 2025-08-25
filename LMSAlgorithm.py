import numpy as np
from typing import Tuple

def lmsFunc(xn: np.ndarray, dn: np.ndarray, M: int, mu: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    LMS 自适应滤波器（一个循环完成权重更新和输出计算）

    参数:
        xn : np.ndarray
            输入信号（加噪信号）
        dn : np.ndarray
            期望信号（原始信号）
        M : int
            滤波器阶数
        mu : float
            步长（学习率）

    返回:
        yn : np.ndarray
            滤波输出信号
        W : np.ndarray
            权重矩阵 (M x len(xn))
        en : np.ndarray
            误差信号
    """
    N = len(xn)
    en = np.zeros(N)
    W = np.zeros((M, N))
    yn = np.zeros(N)

    for k in range(N):
        # 构造输入向量（倒序最近 M 个样本，不够时补 0）
        if k >= M:
         x_vec = xn[k-M:k][::-1]
        else:
            x_vec = np.pad(xn[:k][::-1], (0, M-k), 'constant')

        # 取上一时刻权重
        prev_w = W[:, k-1] if k > 0 else np.zeros(M)

        # 滤波输出
        y = np.dot(prev_w, x_vec)
        yn[k] = y

        # 误差
        en[k] = dn[k] - y

        # 权重更新
        W[:, k] = prev_w + 2 * mu * en[k] * x_vec

    return yn, W, en