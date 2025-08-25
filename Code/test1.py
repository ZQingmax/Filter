import random

num = random.randint(1,100)
count = 1
guess = int(input("请输入你猜的数字"))
while guess != num :
    if guess > num:
        print("你拆大了")
    elif guess < num :
        print("你拆小了")
    guess = int(input("请输入你猜的数字"))
    count += 1

print(f"恭喜你，拆对了,拆了{count}次")