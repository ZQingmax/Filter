import file_define
import file_reader
import total_compute
import pymysql


if __name__ == '__main__' :
  list1 = file_reader.TextFileReader("D:/2011年1月销售数据.txt").read_data()
  list2 = file_reader.JsonFileReader("D:/2011年2月销售数据JSON.txt").read_data()
  
  all_records = list1 + list2

  # compute = total_compute.Compute(all_records)

  # compute.make_picture()

  conn = pymysql.Connection(
    host="localhost",
    port=3306,
    user="root",
    password="123456",
    autocommit=True #事务 （自动确认）
  )

  
  conn.select_db("big_event")

  for record in all_records:
    sql = f"insert into orders(order_date,order_id,money,province) values('{record.date}','{record.order_id}',{record.money},'{record.province}')"
    
    #插入数据库
    conn.cursor().execute(sql)

  conn.close()
  
