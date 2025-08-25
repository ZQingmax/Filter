# def outer(num1):

#   def inner(num2):
#     nonlocal num1  #nonlocal修饰，可以修改外层函数变量
#     num1 += num2
#     print(num1)
  
#   return inner  #返回函数
  
# fn = outer(10)
# fn(10)
# fn(10)
  
#装饰器  AOP 
def outer(func):
  def inner():
    print("我要睡觉了...")
    func()
    print("我要起床了...")
  return inner

#语法糖
@outer
def sleep():
  import random
  import time
  print("睡觉中。。。。。。")
  time.sleep(random.randint(1,5))

# fn = outer(sleep)   # 传递函数对象，不执行
# fn()
sleep()