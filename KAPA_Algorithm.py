import numpy as np

def kapa(xn: np.ndarray, dn: np.ndarray, eta: float = 0.005, K: int = 3, sigma: float = 1.0):
    """
    KAPA (Kernel Affine Projection Algorithm) 实现

    参数:
        xn : np.ndarray
            输入信号 (N, d)
        dn : np.ndarray
            期望信号 (N,)
        eta : float
            步长
        K : int
            投影阶数
        sigma : float
            高斯核参数

    返回:
        yn : np.ndarray
            输出信号
        en : np.ndarray
            误差信号
        dict_x : list
            字典（支持向量集合）
        alpha : np.ndarray
            系数向量
    """
    def kernel(x, y, sigma):
        return np.exp(-np.linalg.norm(x - y) ** 2 / (2 * sigma**2))

    N, d = xn.shape
    yn = np.zeros(N)
    en = np.zeros(N)
    dict_x = []
    alpha = []

    for i in range(N):
        if len(dict_x) == 0:
            y = 0
        else:
            # 核回归输出
            k_vec = np.array([kernel(xn[i], xj, sigma) for xj in dict_x])
            y = np.dot(alpha, k_vec)

        yn[i] = y
        e = dn[i] - y
        en[i] = e

        # 更新最近 K 个系数 (投影更新)
        if len(alpha) < K:
            dict_x.append(xn[i].copy())
            alpha.append(eta * e)
        else:
            # 更新最近 K 个样本的 alpha
            for k in range(-K, 0):
                alpha[k] += eta * e
            dict_x.append(xn[i].copy())
            alpha.append(eta * e)

    return yn, en, dict_x, np.array(alpha)
