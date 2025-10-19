import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
from pathlib import Path
from Comparison import ProbLMSFilter, NVSNLMSFilter, VSSNLMSFilter, JONLMSFilter

def load_speech_signal(num_samples, fs=8000, wav_file=None):
    """
    加载语音信号：
    - 如提供 wav_file，会检查路径并读取；若采样率 != fs，会用 resample_poly 重采样；
    - 若文件不存在或读取失败，回退到一阶 AR 模拟语音（保证不抛异常）。
    返回长度为 num_samples 的浮点 ndarray。
    """
    if wav_file:
        p = Path(wav_file)
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        if p.exists():
            try:
                sr, data = wavfile.read(str(p))
                # 转为单通道、浮点
                if data.ndim > 1:
                    data = data[:, 0]
                data = data.astype(np.float64)
                # 若是整数 PCM，需要归一到 [-1,1]（可选——依数据而定）
                if data.dtype == np.int16 or data.dtype == np.int32:
                    # 归一化（基于最大可能值）
                    data = data / np.max(np.abs(data))
                # 重采样到 fs（若必要）
                if sr != fs:
                    # 使用多项式重采样（resample_poly），参数为 up=fs, down=sr
                    data = signal.resample_poly(data, fs, sr)
                # 截取或循环填充到 num_samples
                if len(data) < num_samples:
                    data = np.tile(data, int(np.ceil(num_samples / len(data))))[:num_samples]
                else:
                    data = data[:num_samples]
                print(f"Loaded wav: {p}  (sr={sr} -> {fs} Hz), length={len(data)}")
                return data.astype(np.float64)
            except Exception as e:
                print("读取 wav 出错，回退到模拟语音。错误信息：", e)
        else:
            print(f"wav 文件不存在: {p}，回退到模拟语音。")
    # 回退：AR 模拟语音
    print("使用 AR(1) 模拟语音信号。")
    ar_coeffs = [1, -0.95]
    white = np.random.randn(num_samples)
    speech_signal = signal.lfilter([1], ar_coeffs, white)
    return speech_signal

def generate_echo_path(L=128):
    """生成并归一化 128 taps 回声路径（与之前相似的模拟）"""
    echo_path = np.zeros(L)
    echo_path[0] = 0.8
    echo_path[5] = -0.4
    echo_path[12] = 0.25
    echo_path[25] = -0.15
    echo_path[45] = 0.08
    # 指数衰减
    idx = np.arange(L)
    echo_path *= np.exp(-idx * 0.02)
    # 归一化（保持能量为1，便于 MSD 计算可比较）
    norm = np.linalg.norm(echo_path)
    if norm > 0:
        echo_path = echo_path / norm
    return echo_path

def echo_cancellation_experiment(num_iterations=5000,
                                 monte_carlo_runs=100,
                                 wav_file=None,
                                 fs=8000,
                                 filter_length=128,
                                 SNR_dB=20,
                                 show=True,
                                 save_path=None):
    """
    回声消除实验（兼容版：修复 matplotlib.stem 参数问题）
    """
    print("\n===== 回声消除实验（改进版） =====")
    echo_path = generate_echo_path(filter_length)

    msd_prob = np.zeros((monte_carlo_runs, num_iterations))
    msd_nvs = np.zeros((monte_carlo_runs, num_iterations))
    msd_vss = np.zeros((monte_carlo_runs, num_iterations))
    msd_jo = np.zeros((monte_carlo_runs, num_iterations))

    for run in range(monte_carlo_runs):
        speech_signal = load_speech_signal(num_iterations + filter_length, fs=fs, wav_file=wav_file)
        signal_power = np.var(speech_signal)
        sigma2_v = signal_power / (10 ** (SNR_dB / 10))

        prob_lms = ProbLMSFilter(filter_length, sigma2_init=0.01, sigma2_q=1e-8)
        nvs_nlms = NVSNLMSFilter(filter_length)
        vss_nlms = VSSNLMSFilter(filter_length)
        jo_nlms = JONLMSFilter(filter_length)

        for k in range(num_iterations):
            u = speech_signal[k:k + filter_length][::-1]
            d_clean = np.dot(u, echo_path)
            noise = np.random.randn() * np.sqrt(sigma2_v)
            d = d_clean + noise

            prob_lms.update(u, d, sigma2_v)
            nvs_nlms.update(u, d)
            vss_nlms.update(u, d)
            jo_nlms.update(u, d)

            msd_prob[run, k] = np.sum((echo_path - prob_lms.w) ** 2)
            msd_nvs[run, k] = np.sum((echo_path - nvs_nlms.w) ** 2)
            msd_vss[run, k] = np.sum((echo_path - vss_nlms.w) ** 2)
            msd_jo[run, k] = np.sum((echo_path - jo_nlms.w) ** 2)

        print(f"Monte Carlo 进度: {run+1}/{monte_carlo_runs}", end="\r")

    avg_prob = 10 * np.log10(np.mean(msd_prob, axis=0) + 1e-12)
    avg_nvs = 10 * np.log10(np.mean(msd_nvs, axis=0) + 1e-12)
    avg_vss = 10 * np.log10(np.mean(msd_vss, axis=0) + 1e-12)
    avg_jo = 10 * np.log10(np.mean(msd_jo, axis=0) + 1e-12)

    # 绘图
    fig, axes = plt.subplots(1, 2, figsize=(14, 4))
    ax0, ax1 = axes

    FONTSIZE = 12
    TICKSIZE = 10
    LINEWIDTH = 1.6

    markerline, stemlines, baseline = ax0.stem(range(filter_length), echo_path, linefmt='C0-',    markerfmt='C0o', basefmt=" ")

    baseline.set_visible(False)
    ax0.set_xlabel('Tap index', fontsize=FONTSIZE)
    ax0.set_ylabel('Amplitude', fontsize=FONTSIZE)
    ax0.set_title('回声路径脉冲响应', fontsize=FONTSIZE)
    ax0.grid(True, alpha=0.25)
    ax0.tick_params(axis='both', labelsize=TICKSIZE)
    ax0.set_xlim(-1, filter_length)
    y_abs = np.max(np.abs(echo_path))
    ax0.set_ylim(-1.1*y_abs, 1.1*y_abs)

    # (b) MSD learning curves
    ax1.plot(avg_prob, '-', c='r',linewidth=LINEWIDTH+0.4, label='Prob-LMS')
    ax1.plot(avg_nvs, '--', linewidth=LINEWIDTH, label='NVS-NLMS')
    ax1.plot(avg_vss, '-.', linewidth=LINEWIDTH, label='VSS-NLMS')
    ax1.plot(avg_jo, ':', linewidth=LINEWIDTH, label='JO-NLMS')

    ax1.set_xlabel('Iteration', fontsize=FONTSIZE)
    ax1.set_ylabel('MSD (dB)', fontsize=FONTSIZE)
    ax1.set_title('回声消除MSD学习曲线', fontsize=FONTSIZE)
    ax1.grid(True, alpha=0.25)
    ax1.legend(fontsize=TICKSIZE)
    ax1.tick_params(axis='both', labelsize=TICKSIZE)
    ax1.set_xlim(0, num_iterations - 1)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300)
        print(f"\nFigure saved to {save_path}")
    if show:
        plt.show()
    else:
        plt.close(fig)

    steady_idx = int(num_iterations * 0.9)
    def steady_mean(arr):
        return np.mean(arr[steady_idx:])
    print("\n稳态 MSD (dB):")
    print(f"- Prob-LMS: {steady_mean(avg_prob):.2f} dB")
    print(f"- NVS-NLMS: {steady_mean(avg_nvs):.2f} dB")
    print(f"- VSS-NLMS: {steady_mean(avg_vss):.2f} dB")
    print(f"- JO-NLMS: {steady_mean(avg_jo):.2f} dB")
if __name__ == "__main__":
    # 使用真实语音信号
    wav_abs_path = r"c:\Users\26612\Desktop\Work\Python\data\speech.wav"
    echo_cancellation_experiment(num_iterations=5000,
                                 monte_carlo_runs=100,
                                 wav_file=wav_abs_path,
                                 fs=8000,
                                 filter_length=128,
                                 SNR_dB=20,
                                 show=True,
                                 save_path="fig3_echo.png")
