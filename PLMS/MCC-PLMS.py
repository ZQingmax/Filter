import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体支持
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

class MCC_PLMS:
    """
    MCC-based Probabilistic LMS (MCC-PLMS)
    Using pseudo-likelihood + curvature-based adaptive step-size

    基于最大相关熵准则 (Maximum Correntropy Criterion, MCC) 的概率LMS算法
    结合伪似然MAP与曲率自适应步长，增强非高斯噪声下的鲁棒性
    """

    def __init__(self, M, sigma_kern=1.0, alpha=1.0, sigma_d_squared=0.0, sigma_n_squared=0.5):
        """
        初始化 MCC-PLMS 滤波器

        Parameters:
        M: int - 滤波器长度
        sigma_kern: float - MCC核宽度 (建议设为噪声标准差的 1~3 倍)
        alpha: float - MCC缩放因子
        sigma_d_squared: float - 参数扩散方差 (0 表示平稳系统)
        sigma_n_squared: float - 观测噪声方差 (用于数值保护)
        """
        self.M = M
        self.sigma_kern = sigma_kern
        self.alpha = alpha
        self.sigma_d_squared = sigma_d_squared
        self.sigma_n_squared = sigma_n_squared

        # 初始化参数
        self.w = np.zeros(M)
        self.sigma_k_squared = 1.0

        # 历史记录
        self.msd_history = []
        self.sigma_history = []
        self.eta_history = []

        # 数值稳定参数
        self.eps_lambda = 1e-6
        self.sigma_eff2_max = 1e6
        self.eta_min = 1e-8
        self.eta_max = 1.0
        self.gamma = 1.0  # 可调缩放因子（吸收 alpha/σ²）

    def update(self, x_k, y_k, w_true=None):
        """
        使用 MCC 准则更新滤波器参数
        """
        # 预测输出
        y_pred = np.dot(x_k.T, self.w)
        e = y_k - y_pred

        # === 1. 计算 MCC 核函数 ===
        kappa = np.exp(-0.5 * (e ** 2) / (self.sigma_kern ** 2))

        # === 2. 一阶、二阶导数 ===
        d1 = -self.alpha * (e / (self.sigma_kern ** 2)) * kappa
        d2 = self.alpha * kappa * ((e ** 2) / (self.sigma_kern ** 4) - 1.0 / (self.sigma_kern ** 2))
        Lambda = -d2  # local precision

        # === 3. 数值保护与退化处理 ===
        if Lambda <= self.eps_lambda:
            # 若局部曲率信息不可靠，则退化为标准PLMS更新
            sigma_eff2 = max(self.sigma_n_squared, 1e-3)
        else:
            sigma_eff2 = 1.0 / Lambda
            sigma_eff2 = min(sigma_eff2, self.sigma_eff2_max)

        # === 4. 自适应步长（基于局部曲率）===
        x_norm_squared = np.dot(x_k, x_k)
        sigma_prior2 = self.sigma_k_squared + self.sigma_d_squared
        eta_k = sigma_prior2 / (sigma_prior2 * x_norm_squared + sigma_eff2)
        eta_k = np.clip(eta_k, self.eta_min, self.eta_max)

        # === 5. 参数更新 ===
        # 注意：-d1 = α e κ / σ²
        self.w = self.w + self.gamma * eta_k * (-d1) * x_k

        # === 6. 更新不确定性估计 ===
        self.sigma_k_squared = (1 - eta_k * x_norm_squared / self.M) * sigma_prior2
        self.sigma_k_squared = max(self.sigma_k_squared, 1e-12)  # 防止负数

        # === 7. 记录学习曲线 ===
        if w_true is not None:
            msd = np.mean((w_true - self.w) ** 2)
            self.msd_history.append(msd)
        self.sigma_history.append(self.sigma_k_squared)
        self.eta_history.append(eta_k)

        return y_pred

    def filter(self, x, d):
        """
        对整个信号序列执行滤波
        """
        N = len(x)
        y = np.zeros(N)
        e = np.zeros(N)
        x_buffer = np.zeros(self.M)

        for n in range(N):
            x_buffer = np.roll(x_buffer, 1)
            x_buffer[0] = x[n]
            y[n] = self.update(x_buffer, d[n])
            e[n] = d[n] - y[n]

        return y, e


# def generate_signals(N=1000, noise_power=0.5):
#     """
#     生成测试信号
    
#     Parameters:
#     N: int - Signal length
#     noise_power: float - Noise power
    
#     Returns:
#     t: array - Time vector
#     original: array - Clean original signal
#     noisy: array - Noisy signal
#     noise: array - Noise
#     """
#     t = np.arange(N)
    
#     # Generate original signal: combination of sinusoids
#     f1, f2, f3 = 0.02, 0.05, 0.08
#     original = (np.sin(2 * np.pi * f1 * t) + 
#                 0.5 * np.sin(2 * np.pi * f2 * t) +
#                 0.3 * np.sin(2 * np.pi * f3 * t))
    
#     # Add Gaussian white noise
#     noise = np.random.normal(0, np.sqrt(noise_power), N)
#     noisy = original + noise
    
#     return t, original, noisy, noise
def generate_signals(N=1000, noise_power=0.5, noise_type='impulsive', impulse_prob=0.1, impulse_amplitude=5.0):
    """
    生成测试信号（支持高斯和非高斯噪声）
    
    Parameters:
    N: int - Signal length
    noise_power: float - Base noise power
    noise_type: str - 'gaussian', 'impulsive', or 'mixed'
    impulse_prob: float - Probability of impulse occurrence (for impulsive noise)
    impulse_amplitude: float - Amplitude of impulses (relative to signal)
    
    Returns:
    t: array - Time vector
    original: array - Clean original signal
    noisy: array - Noisy signal
    noise: array - Noise
    """
    t = np.arange(N)
    
    # Generate original signal: combination of sinusoids
    f1, f2, f3 = 0.02, 0.05, 0.08
    original = (np.sin(2 * np.pi * f1 * t) + 
                0.5 * np.sin(2 * np.pi * f2 * t) +
                0.3 * np.sin(2 * np.pi * f3 * t))
    
    if noise_type == 'gaussian':
        # 纯高斯噪声
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        
    elif noise_type == 'impulsive':
        # 脉冲噪声 (Salt-and-Pepper + Gaussian base)
        noise = np.random.normal(0, np.sqrt(noise_power * 0.1), N)  # 小的高斯基底
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]
        
    elif noise_type == 'mixed':
        # 混合噪声：高斯 + 偶发脉冲
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]
        
    else:
        raise ValueError("noise_type must be 'gaussian', 'impulsive', or 'mixed'")
    
    noisy = original + noise
    
    return t, original, noisy, noise

def plot_results(t, original, noisy, filtered):
    """
    Plot comparison of three signals
    
    Parameters:
    t: array - Time vector
    original: array - Original signal
    noisy: array - Noisy signal
    filtered: array - Filtered signal
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Original signal
    axes[0].plot(t, original, 'g-', linewidth=1.5, label='原始信号')
    axes[0].set_title('原始干净信号', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('样本点')
    axes[0].set_ylabel('幅度')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    
    # Noisy signal
    axes[1].plot(t, noisy, 'r-', linewidth=0.8, alpha=0.7, label='加噪信号')
    axes[1].set_title('加噪声后的信号', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('样本点')
    axes[1].set_ylabel('幅度')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    
    # Filtered signal
    axes[2].plot(t, filtered, 'b-', linewidth=1.5, label='MCC-PLMS滤波信号')
    axes[2].plot(t, original, 'g--', linewidth=1, alpha=0.5, label='原始信号(参考)')
    axes[2].set_title('MCC-PLMS滤波后的信号', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('样本点')
    axes[2].set_ylabel('幅度')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()
    
    plt.tight_layout()
    plt.show()


def plot_comparison(t, original, noisy, filtered):
    """
    Plot all signals in one figure for comparison
    """
    plt.figure(figsize=(14, 6))
    
    plt.plot(t, original, 'g-', linewidth=2, label='原始信号', alpha=0.8)
    plt.plot(t, noisy, 'r-', linewidth=0.5, alpha=0.4, label='加噪信号')
    plt.plot(t, filtered, 'b-', linewidth=1.5, label='MCC-PLMS滤波信号', alpha=0.9)
    
    plt.title('信号对比：原始 vs 加噪 vs MCC-PLMS滤波', fontsize=16, fontweight='bold')
    plt.xlabel('样本点', fontsize=12)
    plt.ylabel('幅度', fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_learning_curves(mcc_plms, error):
    """
    Plot learning curves and adaptive parameters
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Error signal
    axes[0, 0].plot(np.abs(error), 'b-', linewidth=1)
    axes[0, 0].set_title('误差信号的绝对值', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('样本点')
    axes[0, 0].set_ylabel('|误差|')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Cumulative MSE
    N = len(error)
    mse_curve = np.cumsum(error**2) / (np.arange(N) + 1)
    axes[0, 1].plot(mse_curve, 'r-', linewidth=1.5)
    axes[0, 1].set_title('累积均方误差', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('样本点')
    axes[0, 1].set_ylabel('MSE')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Step size (eta) evolution
    axes[1, 0].plot(mcc_plms.eta_history, 'g-', linewidth=1)
    axes[1, 0].set_title('自适应步长 η(k) 演化', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('样本点')
    axes[1, 0].set_ylabel('步长 η')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Uncertainty (sigma) evolution
    axes[1, 1].plot(mcc_plms.sigma_history, 'm-', linewidth=1.5)
    axes[1, 1].set_title('不确定性估计 σ²(k) 演化', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('样本点')
    axes[1, 1].set_ylabel('不确定性 σ²')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def calculate_metrics(original, noisy, filtered):
    """
    Calculate performance metrics
    """
    # SNR improvement
    mse_noisy = np.mean((original - noisy) ** 2)
    mse_filtered = np.mean((original - filtered) ** 2)
    
    snr_input = 10 * np.log10(np.var(original) / mse_noisy)
    snr_output = 10 * np.log10(np.var(original) / mse_filtered)
    
    print("=" * 60)
    print("性能评估指标")
    print("=" * 60)
    print(f"输入信噪比 (SNR): {snr_input:.2f} dB")
    print(f"输出信噪比 (SNR): {snr_output:.2f} dB")
    print(f"信噪比改善: {snr_output - snr_input:.2f} dB")
    print(f"输入均方误差 (MSE): {mse_noisy:.6f}")
    print(f"输出均方误差 (MSE): {mse_filtered:.6f}")
    print(f"MSE降低: {(1 - mse_filtered/mse_noisy)*100:.2f}%")
    print("=" * 60)


# Main program
if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(20)
    
    # Parameters
    N = 1000              # Signal length
    M = 32                # Filter length
    noise_power = 0.5     # Noise power
    sigma_kern = 0.5      # MCC kernel width
    alpha = 1.0           # MCC scale factor
    sigma_d_squared = 0 # Parameter diffusion variance (0 for stationary)
    
    mcc_plms = MCC_PLMS(
    M=M,
    sigma_kern=1.5 * np.sqrt(noise_power),  # 核宽 ≈ 噪声标准差的1.5倍
    alpha=1.0,
    sigma_d_squared=0.0,
    sigma_n_squared=noise_power
    )
    
    print("MCC-PLMS算法演示")
    print("基于最大相关熵准则的概率LMS算法")
    print("=" * 60)
    print(f"信号长度: {N}")
    print(f"滤波器长度 M: {M}")
    print(f"MCC核宽度 σ_kern: {sigma_kern}")
    print(f"MCC缩放因子 α: {alpha}")
    print(f"参数扩散方差 σ²_d: {sigma_d_squared}")
    print(f"噪声功率: {noise_power}")
    print("=" * 60)
    
    # Generate signals
    t, original, noisy, noise = generate_signals(N, noise_power,noise_type='impulsive')

    # 运行滤波
    filtered, error = mcc_plms.filter(noisy, original)

    # 结果展示
    calculate_metrics(original, noisy, filtered)
    plot_results(t, original, noisy, filtered)
    plot_comparison(t, original, noisy, filtered)
    plot_learning_curves(mcc_plms, error)

    # Print final adaptive parameters
    print("\n最终自适应参数:")
    print(f"最终步长 η: {mcc_plms.eta_history[-1]:.6f}")
    print(f"最终不确定性 σ²: {mcc_plms.sigma_history[-1]:.6f}")
    print("=" * 60)