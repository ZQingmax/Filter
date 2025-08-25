import json

#json 格式 转字典
s = '{"name":"zhangsan","addr":"北京"}'
l = json.loads(s)
print(type(l))
print(l)

#列表 转 json格式
data = [{"zhangsan":"666"},{"lisi":"555"}]
d = json.dumps(data)
print(type(d))
print(d)