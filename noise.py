import numpy as np
class Noise:
  @staticmethod
  def add_awgn_noise(x, snr_db):
    """
    给输入信号添加加性高斯白噪声 (AWGN)
    参数:
        x : ndarray
            输入信号（一维向量，可为实数或复数）
        snr_db : float
            信噪比 (dB)
    返回:
        ndarray: 添加噪声后的信号
    """
    # SNR (dB → 线性)
    snr_linear = 10 ** (snr_db / 10.0)
    # 信号功率
    x_power = np.mean(np.abs(x) ** 2)
    # 噪声功率
    noise_power = x_power / snr_linear
    # 根据输入信号类型添加噪声
    if np.iscomplexobj(x):
        noise = (np.random.randn(len(x)) + 1j * np.random.randn(len(x))) * np.sqrt(noise_power / 2)
    else:
        noise = np.random.randn(len(x)) * np.sqrt(noise_power)

    return x + noise

  #脉冲噪声(椒盐噪声)
  @staticmethod
  def add_salt_pepper_noise(x, noise_prob):
    """
    添加椒盐噪声
    x: 输入信号
    noise_prob: 噪声概率 (0-1之间)
    """
    noisy_x = x.copy()
    # 随机选择位置添加噪声
    noise_pos = np.random.random(len(x)) < noise_prob
    # 随机将一半噪声设为最大值(盐噪声)，一半设为最小值(椒噪声)
    salt = noise_pos & (np.random.random(len(x)) < 0.5)
    pepper = noise_pos & ~salt
    
    noisy_x[salt] = np.max(x)
    noisy_x[pepper] = np.min(x)
    return noisy_x

  #均匀分布噪声
  @staticmethod
  def add_uniform_noise(x, amplitude):
    noise = np.random.uniform(-amplitude, amplitude, len(x))
    return x + noise