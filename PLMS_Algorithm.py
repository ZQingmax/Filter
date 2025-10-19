import numpy as np
from typing import Tuple

def probabilistic_lms(xn: np.ndarray, dn: np.ndarray, M: int, sigma_n_sq: float, sigma_d_sq: float = 0.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    概率LMS自适应滤波器（基于论文的各向同性高斯后验近似）

    参数:
        xn : np.ndarray
            输入信号（加噪信号）
        dn : np.ndarray
            期望信号（原始信号）
        M : int
            滤波器阶数
        sigma_n_sq : float
            观测噪声方差 σ_n²
        sigma_d_sq : float, optional
            参数动态方差 σ_d² (默认0，用于平稳场景)

    返回:
        yn : np.ndarray
            滤波输出信号
        W : np.ndarray
            权重矩阵 (M x len(xn))
        en : np.ndarray
            误差信号
        sigma_sq : np.ndarray
            后验不确定性估计 ˆσ_k² (len(xn))
    """
    N = len(xn)
    en = np.zeros(N)
    W = np.zeros((M, N))
    yn = np.zeros(N)
    sigma_sq = np.zeros(N)  # ˆσ_k²

    # 初始后验: ˆμ_0 = 0, ˆσ_0² = σ_d² (from prior p(w0) = N(0, σ_d² I))
    sigma_sq_prev = sigma_d_sq

    for k in range(N):
        # 构造输入向量（倒序最近 M 个样本，不够时补 0）
        if k >= M:
            x_vec = xn[k-M:k][::-1]
        else:
            x_vec = np.pad(xn[:k][::-1], (0, M-k), 'constant')

        # 取上一时刻权重 (初始为0)
        prev_w = W[:, k-1] if k > 0 else np.zeros(M)

        # 滤波输出
        y = np.dot(prev_w, x_vec)
        yn[k] = y

        # 误差
        en[k] = dn[k] - y

        # 自适应步长 η_k
        denom = (sigma_sq_prev + sigma_d_sq) * np.dot(x_vec, x_vec) + sigma_n_sq  # ||x_k||² = x_vec^T x_vec
        eta_k = (sigma_sq_prev + sigma_d_sq) / denom

        # 权重更新 (注意: 论文中为 η_k e_k x_k，与标准LMS一致; 原代码有2*mu，这里移除2以匹配论文)
        W[:, k] = prev_w + eta_k * en[k] * x_vec

        # 更新后验不确定性 ˆσ_k² = [1 - η_k ||x_k||² / M] (ˆσ_{k-1}² + σ_d²)
        x_norm_sq = np.dot(x_vec, x_vec)
        sigma_sq[k] = (1 - eta_k * x_norm_sq / M) * (sigma_sq_prev + sigma_d_sq)
        sigma_sq_prev = sigma_sq[k]

    return yn, W, en, sigma_sq