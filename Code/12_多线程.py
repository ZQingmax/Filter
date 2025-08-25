import threading
import time
def sing(msg):
  while True:
    print(msg)
    time.sleep(1)
def dance(msg):
  while True:
    print(msg)
    time.sleep(1)
if __name__ == '__main__':
  sing_thread = threading.Thread(target=sing,args=("我在唱歌，哈哈哈",),name="员工1")
  dance_thread = threading.Thread(target=dance,args=("我在跳舞，啦啦啦",),name="员工2")

  sing_thread.start()
  dance_thread.start()