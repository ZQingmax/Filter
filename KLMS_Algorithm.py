import numpy as np
from typing import Tuple, Callable

def gaussian_kernel(x: np.ndarray, y: np.ndarray, sigma: float) -> float:
    """高斯核函数"""
    diff = x - y
    return np.exp(-np.dot(diff, diff) / (2 * sigma ** 2))

def klms(xn: np.ndarray, dn: np.ndarray, mu: float = 0.5, sigma: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Kernel LMS (KLMS) 算法实现
    
    参数:
        xn : np.ndarray
            输入信号 (N x d)
        dn : np.ndarray
            期望信号 (N,)
        mu : float
            步长
        sigma : float
            高斯核带宽
    
    返回:
        yn : np.ndarray
            滤波输出信号
        en : np.ndarray
            误差信号
    """
    N = len(dn)
    yn = np.zeros(N)
    en = np.zeros(N)

    # 存储历史输入和误差
    dict_x = []
    dict_e = []

    for n in range(N):
        # 计算当前输出
        y = 0
        for xi, ei in zip(dict_x, dict_e):
            y += mu * ei * gaussian_kernel(xi, xn[n], sigma)
        yn[n] = y

        # 计算误差
        en[n] = dn[n] - y

        # 存储当前样本
        dict_x.append(xn[n])
        dict_e.append(en[n])

    return yn, en
