import numpy as np
from typing import Tuple

def lmsFunc(xn: np.ndarray, dn: np.ndarray, M: int, mu: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    LMS自适应滤波器
    参数:
        xn : np.ndarray
            输入信号（加噪信号）
        dn : np.ndarray
            期望信号（原始信号）
        M : int
            滤波器阶数
        mu : float
            步长因子（学习率）
    返回:
        yn : np.ndarray
            滤波输出信号
        W : np.ndarray
            滤波器权重矩阵 (M x len(xn))
        en : np.ndarray
            误差信号
    """
    N = len(xn)              
    en = np.zeros((N, 1))    
    W = np.zeros((M, N))     
    for k in range(M, N):
        if k == 20:
            x = xn[k-1::-1]
        else:
            x = xn[k-1:k-M-1:-1]
        try:
            y = np.dot(W[:, k - 2], x)
        except:
            y = 0
        en[k-1] = dn[k-1] - y
        W[:, k-1] = W[:, k - 2] + 2 * mu * en[k-1] * x
    yn = np.ones(xn.shape) * np.nan
    for k in range(M, len(xn)):
        if k == 20:
            x = xn[k - 1::-1]
        else:
            x = xn[k - 1:k - M - 1:-1]
        yn[k] = np.dot(W[:, -2], x)
    return yn, W, en
