from pymysql import Connection

conn = Connection(
  host="localhost",
  port=3306,
  user="root",
  password="123456",
  autocommit=True #事务 （自动确认）
)

print(conn.get_server_info())

#获取游标对象
cursor = conn.cursor()

#选择数据库
conn.select_db("big_event")

#执行sql
cursor.execute("select * from user")

#获取结果
results = cursor.fetchall()

for r in results:
  print(r)


conn.close()