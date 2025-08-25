def user_info():
  return "zhangsan",12,"boy"

x,y,z = user_info()

print(x,y,z)

def user_info(name,age,gender):
  print(f"名字是{name}，年龄是{age}，性别是{gender}")

user_info(age=18,name="lisi",gender="girl")


# 不定长无参 - 位置不定长
def user_info(*args):
  print(f"类型是{type(args)},内容是{args}")
user_info("wangwu",19,"girl")

# 不定长无参 - 关键字不定长
def user_info(**kwargs):
  print(f"类型是{type(kwargs)},内容是{kwargs}")
user_info(name="laoliu",age=89,gender="boy")
