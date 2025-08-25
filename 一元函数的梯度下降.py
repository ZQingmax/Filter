import numpy as np 
import matplotlib.pyplot as plt
# 设置中文字体和负号
plt.rcParams['font.sans-serif'] = ['SimHei']   # 黑体
plt.rcParams['axes.unicode_minus'] = False

delta = 1/100000
x = np.arange(-1.1, 1.1, delta)
y = x ** 2
dot = np.array([1, 0.2, 0.04, 0.008])
plt.figure(figsize=(7,5))
plt.plot(x,y)
plt.grid(True)
plt.xlim(-1.2, 1.2)
plt.ylim(-0.2, 1.3)
plt.plot(dot, dot**2, 'r')
for i in range(len(dot)):
    plt.text(dot[i],dot[i]**2,r'$\theta_%d$' % i)
plt.title('一元函数的梯度下降过程')
plt.show()
