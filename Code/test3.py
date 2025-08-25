name = "zjl"
money = 0
def check():
    print(f"您的余额为{money:.4f}")

def deposit():
    global money
    num = float(input("请输入存款金额:"))
    money += num
    print(f"存款成功，您的余额为{money:.4f}")

def withdrawl():
    global money
    num = float(input("请输入取款金额:"))
    if num > money:
        print(f"对不起，您的余额不足，余额为{money:.4f}")
    else:
      money -= num
      print(f"取款成功，您的余额为{money:.4f}")

def menu():
    while True:
        print("-------------主菜单---------------")
        print(f"{name},您好，欢迎来到ATM，请选择操作：")
        print("查询余额\t输入1")
        print("存款\t输入2")
        print("取款\t输入3")
        print("退出\t输入4")
        select = int(input())
        if select == 1:
            check()
        elif select == 2:
            deposit()
        elif select == 3:
            withdrawl()
        elif select == 4:
            break
        else:
            print("输入无效请重新输入")
menu()