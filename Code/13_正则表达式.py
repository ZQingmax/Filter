import re

s = "python hello wrold"

#math只匹配开头
# r = re.match("hello",s)
# print(r)
# print(r.span())
# print(r.group())

#search 找第一个
r = re.search("hello",s)
print(r)
print(r.span())
print(r.group())

#findall 毋庸置疑

ss = "pthois！！！ 123@ sdkd44 python ##jkiio100"

result = re.findall(r'\d',ss)  # r : 转义字符无效  正则：\d:匹配数字
print(result)
result = re.findall(r'\W',ss) # \W :特殊字符 \w:a-z,A-Z,0-9,_
print(result)
result = re.findall(r'[a-zA-Z]',ss) #[自定义]   - 范围  
print(result)