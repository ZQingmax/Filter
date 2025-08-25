def test(compute):
  result = compute(1,2)
  print(f"结果是{result}")
def compute(x,y):
  return x + y

test(compute)


print("----------------------------------")

def test(compute):
  result = compute(1,2)
  print(f"结果是{result}")

test(lambda x,y : x * y)
test(lambda x,y : x + y)
test(lambda x,y : x - y)