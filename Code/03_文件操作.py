# f = open("D:\study\\test.txt","r",encoding="UTF-8")


# 1
# print(f.read())
# # 2
# for line in f:
#   print(f"每一行的数据是:{line}")

# 3
# lines = f.readlines()
# print(lines)
#f.close()    #调用完要关闭

# 4  这种方法无需关闭，使用完自动关闭
with open("D:\study\\test.txt","r",encoding="UTF-8") as f:
  for line in f :
    print(f"每一行的数据是：{line}")

#"w"会清空所有内容，"a"追加

