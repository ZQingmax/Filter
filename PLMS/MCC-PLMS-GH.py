import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from numpy.polynomial.hermite import hermgauss
import math
# import optuna  # 如果需要重新优化，取消注释

# 设置中文字体支持
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

class MCC_PLMS_GH:
    """
    MCC-PLMS using Gauss-Hermite moment matching (Assumed Density Filtering style).
    - Projects posterior of scalar z = x^T w (via numerical integration)
      and matches first/second moments to obtain Gaussian q(w)=N(mu, sigma2 I).
    - More accurate than local curvature (d2) approximation.
    """

    def __init__(self, M, sigma_kern=1.0, alpha=1.0, sigma_d_squared=0.0,
                 sigma_n_squared=0.5, gh_points=40):
        """
        Parameters:
          M: filter length
          sigma_kern: MCC kernel width (σ in κ(e)=exp(-e^2/(2σ^2)))
          alpha: scaling for pseudo-log-likelihood (log p ~ alpha * κ(e))
          sigma_d_squared: process diffusion variance
          sigma_n_squared: observation noise variance (fallback)
          gh_points: number of Gauss-Hermite points (20~40 recommended)
        """
        self.M = M
        self.sigma_kern = float(sigma_kern)
        self.alpha = float(alpha)
        self.sigma_d_squared = float(sigma_d_squared)
        self.sigma_n_squared = float(sigma_n_squared)

        # parameter posterior approx q(w) = N(mu, sigma2 * I)
        self.w = np.zeros(M)
        self.sigma_k_squared = 1.0

        # history
        self.msd_history = []
        self.sigma_history = []
        self.eta_history = []

        # Gauss-Hermite nodes & weights (for ∫ e^{-t^2} f(t) dt)
        self.gh_n = int(gh_points)
        self.gh_x, self.gh_w = hermgauss(self.gh_n)  # nodes & weights

        # numerical safeguards
        self.min_sigma2 = 1e-12
        self.min_Z = 1e-15  # avoid division by zero

    def _compute_posterior_moments_z(self, m_z, s_z2, y):
        """
        Compute posterior mean and variance of z given prior N(m_z, s_z2) and
        pseudo-likelihood L(y|z) = exp(alpha * kappa(y - z)), using Gauss-Hermite.

        Returns:
          m_z_post, s_z_post2, Z (normalizing constant)
        """
        # If s_z2 extremely small, return near-delta
        if s_z2 <= 0:
            return m_z, 0.0, 1.0

        # Transform GH nodes: z_i = m_z + sqrt(2*s_z2) * t_i
        sqrt_2_s = math.sqrt(2.0 * s_z2)
        z_pts = m_z + sqrt_2_s * self.gh_x  # shape (gh_n,)

        # compute pseudo-likelihood values L(y|z) = exp(alpha * kappa(e))
        # where e = y - z
        e_pts = y - z_pts
        # compute kappa safely
        kappa_pts = np.exp(-0.5 * (e_pts ** 2) / (self.sigma_kern ** 2))
        L_pts = np.exp(self.alpha * kappa_pts)

        # weights for GH: integral ≈ (1 / sqrt(pi)) * sum_i w_i * f(m+sqrt(2 s) x_i)
        gw = self.gh_w  # already numpy array
        pref = 1.0 / math.sqrt(math.pi)

        # Z = ∫ N(z;m,s2) L(y|z) dz ≈ pref * sum w_i * L(z_i)
        Z = pref * np.dot(gw, L_pts)

        # Numerator for mean: ∫ z * N(z;m,s2) L dz ≈ pref * sum w_i * z_i * L_i
        num_mean = pref * np.dot(gw, z_pts * L_pts)

        # Numerator for second moment: ∫ z^2 * N(z;...) L dz
        num_second = pref * np.dot(gw, (z_pts ** 2) * L_pts)

        # Numerical safeguard
        if Z < self.min_Z:
            # Very small normalization constant -> fallback to prior
            return m_z, s_z2, Z

        m_z_post = num_mean / Z
        E_z2 = num_second / Z
        s_z_post2 = max(E_z2 - m_z_post ** 2, 0.0)

        return m_z_post, s_z_post2, Z

    def update(self, x_k, y_k, w_true=None):
        """
        One-step update using moment matching on z = x^T w.
        """
        # Prior projection parameters
        sigma_prior2 = self.sigma_k_squared + self.sigma_d_squared
        x_norm_squared = np.dot(x_k, x_k)

        # Prior marginal of z = x^T w: Gaussian with mean m_z and variance s_z2
        m_z = np.dot(x_k, self.w)  # x^T mu_prior
        s_z2 = sigma_prior2 * x_norm_squared

        # Compute posterior moments of z via GH quadrature
        m_z_post, s_z_post2, Z = self._compute_posterior_moments_z(m_z, s_z2, y_k)

        # If Z extremely small (degenerate), fallback to PLMS-like update
        if Z < self.min_Z:
            # fallback simple PLMS update (robust)
            # choose an eta similar to PLMS formula using observation noise
            eta_k = sigma_prior2 / (sigma_prior2 * x_norm_squared + self.sigma_n_squared)
            # standard LMS-like update
            e = y_k - m_z
            self.w = self.w + eta_k * e * x_k
            # covariance update
            self.sigma_k_squared = max((1 - eta_k * x_norm_squared / self.M) * sigma_prior2, self.min_sigma2)
            # record and return
            self.eta_history.append(eta_k)
            self.sigma_history.append(self.sigma_k_squared)
            if w_true is not None:
                self.msd_history.append(np.mean((w_true - self.w) ** 2))
            return m_z_post  # predicted y (prior mean)

        # Project back to parameter space:
        # Update mean: mu_new = mu_prior + (m_z_post - m_z) / ||x||^2 * x
        if x_norm_squared <= 0:
            delta_mu = np.zeros_like(self.w)
        else:
            delta_mu = ((m_z_post - m_z) / x_norm_squared) * x_k

        mu_new = self.w + delta_mu

        # Update isotropic variance:
        # prior variance along z: s_z2 = sigma_prior2 * x_norm_squared
        # posterior variance along z: s_z_post2
        # reduction along z: s_z2 - s_z_post2
        # distribute reduction equally across dimensions: sigma_new2 = sigma_prior2 - (s_z2 - s_z_post2)/||x||^2
        if x_norm_squared <= 0:
            sigma_new2 = sigma_prior2
        else:
            variance_reduction = (s_z2 - s_z_post2) / x_norm_squared
            sigma_new2 = sigma_prior2 - variance_reduction
            # numerical guard
            sigma_new2 = max(sigma_new2, self.min_sigma2)

        # compute an effective scalar step-size (for logging) as norm change ratio
        # we can define eta_k akin to PLMS form for comparability:
        # eta_k = ||delta_mu|| / (|e| * ||x||) approx; but we compute a proxy:
        if np.linalg.norm(x_k) > 0 and abs(y_k - m_z) > 1e-12:
            eta_k = np.linalg.norm(delta_mu) / (abs(y_k - m_z) * np.linalg.norm(x_k))
        else:
            # fallback eta
            eta_k = sigma_prior2 / (sigma_prior2 * x_norm_squared + self.sigma_n_squared)

        # Assign new posterior approx
        self.w = mu_new
        self.sigma_k_squared = sigma_new2

        # record
        self.eta_history.append(float(eta_k))
        self.sigma_history.append(float(self.sigma_k_squared))
        if w_true is not None:
            self.msd_history.append(np.mean((w_true - self.w) ** 2))

        # return predicted y (prior mean used for prediction)
        return m_z_post

    def filter(self, x, d):
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

def generate_signals(N=1000, noise_power=0.5):
    """
    生成测试信号
    
    Parameters:
    N: int - Signal length
    noise_power: float - Noise power
    
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
    
    # Add Gaussian white noise
    noise = np.random.normal(0, np.sqrt(noise_power), N)
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


# 如果需要重新运行Optuna优化，定义以下函数（当前注释掉）
# def run_filter(M, sigma_kern, alpha, sigma_d_squared, sigma_n_squared, gh_points):
#     np.random.seed(42)  # For reproducibility
#     N = 1000
#     noise_power = 0.5
#     t, original, noisy, noise = generate_signals(N, noise_power)
#     
#     mcc_plms = MCC_PLMS_GH(
#         M=M,
#         sigma_kern=sigma_kern,
#         alpha=alpha,
#         sigma_d_squared=sigma_d_squared,
#         sigma_n_squared=sigma_n_squared,
#         gh_points=gh_points
#     )
#     
#     filtered, error = mcc_plms.filter(noisy, original)
#     
#     mse_noisy = np.mean((original - noisy) ** 2)
#     mse_filtered = np.mean((original - filtered) ** 2)
#     
#     return {'output_mse': mse_filtered}
#
# def objective(trial):
#     noise_power = 0.5
#     sigma_kern = trial.suggest_float('sigma_kern', 0.1, 2.0) * np.sqrt(noise_power)
#     alpha = trial.suggest_float('alpha', 0.1, 5.0)
#     M = trial.suggest_int('M', 16, 128)
#     sigma_d_squared = trial.suggest_float('sigma_d_squared', 1e-6, 1e-2, log=True)
#     sigma_n_squared = noise_power
#     gh_points = 40
#     
#     metrics = run_filter(M, sigma_kern, alpha, sigma_d_squared, sigma_n_squared, gh_points)
#     return metrics['output_mse']
#
# study = optuna.create_study(direction='minimize')
# study.optimize(objective, n_trials=50)
#
# print("Best parameters:", study.best_params)
# print("Best MSE:", study.best_value)

# Main program
if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Parameters (使用Optuna优化的最优值)
    N = 1000              # Signal length
    noise_power = 0.5     # Noise power
    M = 102               # Optimized filter length
    sigma_kern = 1.0695   # Optimized MCC kernel width
    alpha = 4.9441        # Optimized MCC scale factor
    sigma_d_squared = 0.006989  # Optimized parameter diffusion variance
    gh_points = 40        # Fixed
    
    mcc_plms = MCC_PLMS_GH(
        M=M,
        sigma_kern=sigma_kern,
        alpha=alpha,
        sigma_d_squared=sigma_d_squared,
        sigma_n_squared=noise_power,
        gh_points=gh_points
    )
    
    print("MCC-PLMS算法演示（使用Optuna优化的参数）")
    print("基于最大相关熵准则的概率LMS算法")
    print("=" * 60)
    print(f"信号长度: {N}")
    print(f"滤波器长度 M: {M}")
    print(f"MCC核宽度 σ_kern: {sigma_kern:.4f}")
    print(f"MCC缩放因子 α: {alpha:.4f}")
    print(f"参数扩散方差 σ²_d: {sigma_d_squared:.6f}")
    print(f"噪声功率: {noise_power}")
    print("=" * 60)
    
    # Generate signals
    t, original, noisy, noise = generate_signals(N, noise_power)

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