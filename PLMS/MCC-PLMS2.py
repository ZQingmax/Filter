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

        # === 2. 一阶、二阶导数（关于 e 的导数） ===
        # 注意符号：d1 = d/d(e) [-alpha * (1 - kappa)] = -alpha * d/d(e) ( -kappa ) = -alpha * (e / sigma_kern^2) * kappa * (-1)? 
        # 这里直接采用之前给定形式（与代码一致）
        d1 = -self.alpha * (e / (self.sigma_kern ** 2)) * kappa
        d2 = self.alpha * kappa * ((e ** 2) / (self.sigma_kern ** 4) - 1.0 / (self.sigma_kern ** 2))
        Lambda = -d2  # local precision (关于 e 的曲率)

        # === 3. 数值保护与退化处理 ===
        if Lambda <= self.eps_lambda:
            # 若局部曲率信息不可靠，则退化为标准PLMS更新（用观测噪声方差保护）
            sigma_eff2 = max(self.sigma_n_squared, 1e-3)
        else:
            sigma_eff2 = 1.0 / Lambda
            sigma_eff2 = min(sigma_eff2, self.sigma_eff2_max)

        # === 4. 自适应步长（基于局部曲率 + 先验不确定度）===
        x_norm_squared = np.dot(x_k, x_k)
        sigma_prior2 = self.sigma_k_squared + self.sigma_d_squared
        eta_k = sigma_prior2 / (sigma_prior2 * x_norm_squared + sigma_eff2)
        eta_k = np.clip(eta_k, self.eta_min, self.eta_max)

        # === 5. 参数更新 ===
        # 梯度方向取 -d1，实际更新项为 gamma * eta_k * (-d1) * x_k
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

    def filter(self, x, d, w_true=None):
        """
        对整个信号序列执行滤波
        支持传入真实系数 w_true 用于 MSD 计算
        """
        N = len(x)
        y = np.zeros(N)
        e = np.zeros(N)
        x_buffer = np.zeros(self.M)

        for n in range(N):
            x_buffer = np.roll(x_buffer, 1)
            x_buffer[0] = x[n]
            y[n] = self.update(x_buffer, d[n], w_true)
            e[n] = d[n] - y[n]

        return y, e

def generate_system_identification_data(N=1000, M=32, noise_power=0.5, 
                                        noise_type='impulsive', impulse_prob=0.1, 
                                        impulse_amplitude=5.0):
    """
    生成系统辨识数据（用于计算MSD）
    """
    # 生成真实系统系数 (unknown system)
    w_true = np.random.randn(M) * 0.5
    w_true = w_true / np.linalg.norm(w_true)  # 归一化到单位范数

    # 生成输入信号（白噪声）
    x = np.random.randn(N)

    # 通过真实系统生成期望输出
    d_clean = np.zeros(N)
    x_buffer = np.zeros(M)

    for n in range(N):
        x_buffer = np.roll(x_buffer, 1)
        x_buffer[0] = x[n]
        d_clean[n] = np.dot(w_true, x_buffer)

    # 添加噪声
    if noise_type == 'gaussian':
        noise = np.random.normal(0, np.sqrt(noise_power), N)

    elif noise_type == 'impulsive':
        noise = np.random.normal(0, np.sqrt(noise_power * 0.1), N)
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]

    elif noise_type == 'mixed':
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]

    else:
        raise ValueError("noise_type must be 'gaussian', 'impulsive', or 'mixed'")

    d = d_clean + noise

    return x, d, w_true, noise

def generate_signals(N=1000, noise_power=0.5, noise_type='impulsive', impulse_prob=0.1, impulse_amplitude=5.0):
    """
    生成测试信号（支持高斯和非高斯噪声）
    """
    t = np.arange(N)

    # Generate original signal: combination of sinusoids
    f1, f2, f3 = 0.02, 0.05, 0.08
    original = (np.sin(2 * np.pi * f1 * t) + 
                0.5 * np.sin(2 * np.pi * f2 * t) +
                0.3 * np.sin(2 * np.pi * f3 * t))

    if noise_type == 'gaussian':
        noise = np.random.normal(0, np.sqrt(noise_power), N)

    elif noise_type == 'impulsive':
        noise = np.random.normal(0, np.sqrt(noise_power * 0.1), N)  # 小的高斯基底
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]

    elif noise_type == 'mixed':
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
    axes[2].plot(t, filtered, 'b-', linewidth=1.5, label='MCC-PLMS 滤波信号')
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

def plot_learning_curves(plms, error):
    """
    Plot learning curves and adaptive parameters
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # MSD curve (if available) or Error signal
    if len(plms.msd_history) > 0:
        msd_db = 10 * np.log10(np.array(plms.msd_history) + 1e-12)
        axes[0, 0].plot(msd_db, 'b-', linewidth=1.5)
        axes[0, 0].set_title('均方偏差 (MSD) 学习曲线', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('样本点')
        axes[0, 0].set_ylabel('MSD (dB)')
        axes[0, 0].grid(True, alpha=0.3)
    else:
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
    axes[1, 0].plot(plms.eta_history, 'g-', linewidth=1)
    axes[1, 0].set_title('自适应步长 η(k) 演化', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('样本点')
    axes[1, 0].set_ylabel('步长 η')
    axes[1, 0].grid(True, alpha=0.3)

    # Uncertainty (sigma) evolution
    axes[1, 1].plot(plms.sigma_history, 'm-', linewidth=1.5)
    axes[1, 1].set_title('不确定性估计 σ²(k) 演化', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('样本点')
    axes[1, 1].set_ylabel('不确定性 σ²')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

def plot_coefficient_comparison(w_true, w_est):
    """
    Plot comparison between true and estimated coefficients
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Coefficient comparison
    indices = np.arange(len(w_true))
    axes[0].stem(indices, w_true, linefmt='g-', markerfmt='go', basefmt='k-', label='真实系数')
    axes[0].stem(indices, w_est, linefmt='b-', markerfmt='bs', basefmt='k-', label='估计系数')
    axes[0].set_title('系数对比：真实 vs 估计', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('系数索引')
    axes[0].set_ylabel('系数值')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Coefficient error
    error = w_true - w_est
    axes[1].bar(indices, error, color='r', alpha=0.7)
    axes[1].set_title('系数误差分布', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('系数索引')
    axes[1].set_ylabel('误差 (真实 - 估计)')
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].axhline(y=0, color='k', linestyle='-', linewidth=0.8)

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

# ----------------- Main program -----------------
if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)

    # Parameters
    N = 2000              # Signal length (增加到2000以更好观察收敛)
    M = 32                # Filter length
    noise_power = 0.5     # Noise power

    # 噪声参数
    noise_type = 'impulsive'  # 'gaussian', 'impulsive', or 'mixed'
    impulse_prob = 0.05       # 5% 的样本点出现脉冲
    impulse_amplitude = 8.0   # 脉冲幅度

    sigma_n_squared = noise_power  # Observation noise variance
    sigma_d_squared = 1e-6   # Parameter diffusion variance (0 for stationary)

    # MCC 参数（可调）
    sigma_kern = 1.0  # 核宽度，建议与噪声标准差相近或为其几倍
    alpha = 1.0

    print("=" * 70)
    print("MCC-PLMS 算法演示 - 系统辨识与去噪测试")
    print("=" * 70)

    # 选择运行模式
    print("\n请选择运行模式:")
    print("1 - 信号去噪模式 (Signal Denoising)")
    print("2 - 系统辨识模式 (System Identification with MSD)")
    mode = input("输入选项 [1/2]: ").strip()

    if mode == '2':
        # ========== 系统辨识模式 (计算MSD) ==========
        print("\n" + "=" * 70)
        print(">>> 系统辨识模式 (System Identification Mode) <<<")
        print("=" * 70)
        print(f"信号长度: {N}")
        print(f"滤波器长度 M: {M}")
        print(f"噪声类型: {noise_type.upper()}")
        if noise_type in ['impulsive', 'mixed']:
            print(f"脉冲概率: {impulse_prob*100:.1f}%")
            print(f"脉冲幅度: ±{impulse_amplitude}")
        print(f"观测噪声方差 σ²_n: {sigma_n_squared}")
        print(f"参数扩散方差 σ²_d: {sigma_d_squared}")
        print(f"MCC 核宽度 σ_kern: {sigma_kern}")
        print(f"MCC 缩放因子 alpha: {alpha}")
        print("=" * 70)

        # 生成系统辨识数据
        print("\n正在生成系统辨识数据...")
        x, d, w_true, noise = generate_system_identification_data(
            N, M, noise_power,
            noise_type=noise_type,
            impulse_prob=impulse_prob,
            impulse_amplitude=impulse_amplitude
        )

        print(f"真实系统系数范围: [{w_true.min():.4f}, {w_true.max():.4f}]")
        print(f"真实系数L2范数: {np.linalg.norm(w_true):.4f}")

        # 创建 MCC-PLMS 滤波器
        mcc_plms = MCC_PLMS(M, sigma_kern=sigma_kern, alpha=alpha,
                            sigma_d_squared=sigma_d_squared, sigma_n_squared=sigma_n_squared)

        # 运行自适应滤波
        print("\n正在运行 MCC-PLMS 自适应滤波...")
        y, error = mcc_plms.filter(x, d, w_true)

        # 显示结果
        print("\n" + "=" * 70)
        print("系统辨识结果")
        print("=" * 70)
        final_msd = mcc_plms.msd_history[-1] if len(mcc_plms.msd_history) > 0 else None
        if final_msd is not None:
            final_msd_db = 10 * np.log10(final_msd + 1e-12)
            print(f"最终MSD (线性): {final_msd:.8f}")
            print(f"最终MSD (dB): {final_msd_db:.2f} dB")
        print(f"最终步长 η: {mcc_plms.eta_history[-1]:.6f}")
        print(f"最终不确定性 σ²: {mcc_plms.sigma_history[-1]:.6f}")
        print(f"系数估计误差范数: {np.linalg.norm(w_true - mcc_plms.w):.6f}")
        print(f"平均MSE: {np.mean(error**2):.6f}")
        print("=" * 70)

        # 绘制学习曲线
        print("\n生成学习曲线图...")
        plot_learning_curves(mcc_plms, error)

        # 绘制系数对比
        print("生成系数对比图...")
        plot_coefficient_comparison(w_true, mcc_plms.w)

        print("\n✓ 系统辨识测试完成!")

    else:
        # ========== 信号去噪模式 ==========
        print("\n" + "=" * 70)
        print(">>> 信号去噪模式 (Signal Denoising Mode) <<<")
        print("=" * 70)
        print(f"信号长度: {N}")
        print(f"滤波器长度 M: {M}")
        print(f"噪声类型: {noise_type.upper()}")
        if noise_type in ['impulsive', 'mixed']:
            print(f"脉冲概率: {impulse_prob*100:.1f}%")
            print(f"脉冲幅度: ±{impulse_amplitude}")
        print(f"观测噪声方差 σ²_n: {sigma_n_squared}")
        print(f"参数扩散方差 σ²_d: {sigma_d_squared}")
        print(f"MCC 核宽度 σ_kern: {sigma_kern}")
        print(f"MCC 缩放因子 alpha: {alpha}")
        print("=" * 70)

        # Generate signals
        print("\n正在生成测试信号...")
        t, original, noisy, noise = generate_signals(
            N, noise_power, 
            noise_type=noise_type,
            impulse_prob=impulse_prob,
            impulse_amplitude=impulse_amplitude
        )

        # Create MCC-PLMS filter
        mcc_plms = MCC_PLMS(M, sigma_kern=sigma_kern, alpha=alpha,
                            sigma_d_squared=sigma_d_squared, sigma_n_squared=sigma_n_squared)

        # Apply filter
        print("正在运行 MCC-PLMS 滤波...")
        filtered, error = mcc_plms.filter(noisy, original)

        # Calculate performance metrics
        calculate_metrics(original, noisy, filtered)

        # Plot results
        print("\n生成信号对比图...")
        plot_results(t, original, noisy, filtered)
        plot_comparison(t, original, noisy, filtered)
        plot_learning_curves(mcc_plms, error)

        # Print final adaptive parameters
        print("\n最终自适应参数:")
        print(f"最终步长 η: {mcc_plms.eta_history[-1]:.6f}")
        print(f"最终不确定性 σ²: {mcc_plms.sigma_history[-1]:.6f}")
        print("=" * 70)

        print("\n✓ 信号去噪测试完成!")
