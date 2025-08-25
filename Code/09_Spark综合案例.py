from pyspark import SparkConf,SparkContext
import os
import sys
import json

def create_spark_context_basic():
    # 设置Hadoop环境
    HADOOP_HOME = r"C:/Users/26612\AppData/Local/Programs/hadoop-3.4.1"
    PYTHON_EXE = r"C:/Users/26612\AppData/Local/Programs/Python/Python311/python.exe"
    
    os.environ['HADOOP_HOME'] = HADOOP_HOME
    os.environ['PYSPARK_PYTHON'] = PYTHON_EXE
    os.environ['PYSPARK_DRIVER_PYTHON'] = PYTHON_EXE
    
    # 确保Hadoop bin在PATH中
    hadoop_bin = os.path.join(HADOOP_HOME, 'bin')
    if hadoop_bin not in os.environ.get('PATH', ''):
        os.environ['PATH'] = hadoop_bin + ';' + os.environ.get('PATH', '')
    
    conf = (SparkConf()
            .setMaster("local[*]")
            .setAppName("pyspark_windows_hadoop")
            .set("spark.sql.adaptive.enabled", "false")
            .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .set("spark.driver.memory", "2g")
            .set("spark.executor.memory", "1g"))
    
    sc = SparkContext(conf=conf)
    sc.setLogLevel("ERROR")
    return sc

def cal_sale() :
    sc = create_spark_context_basic()
    rdd = sc.textFile("D:/orders.txt").flatMap(lambda x : x.split("|"))
    #先解析为字典，再调用,将金额从字符串转变为float
    sales = rdd.map(lambda x : json.loads(x)).map(lambda x : (x["areaName"],float(x["money"])))
    #聚合计算每个地区的总销售额,从大到小
    all_sales = sales.reduceByKey(lambda a,b:a + b).sortBy(lambda x: x[1],ascending=False)

    print(all_sales.collect())

    sc.stop()

#计算各个城市的销售种类
def cal_category():
    sc = create_spark_context_basic()
    rdd = sc.textFile("D:/orders.txt").flatMap(lambda x : x.split("|"))
    categorys = rdd.map(lambda x : json.loads(x)).map(lambda x : (x["areaName"],x["category"]))\
    .distinct().groupByKey().mapValues(lambda x: sorted(list(x)))

    print(categorys.collect())

# 保存各城市销售总额示例
def save_city_sales():
    sc = create_spark_context_basic()
    # 处理数据
    city_sales = (sc.textFile("D:/orders.txt")
                  .flatMap(lambda x: x.split("|"))
                  .map(lambda x: json.loads(x))
                  .map(lambda x: (x["areaName"], float(x["money"])))
                  .reduceByKey(lambda a, b: a + b)
                  .sortBy(lambda x: x[1], ascending=False)
                  .map(lambda x: f"{x[0]},{x[1]:.2f}"))  # 转为CSV格式
    
    # 保存到文件
    output_path = "D:/spark_output/city_sales"
    
    # 清理旧文件（重要！）
    import shutil
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    
    # 保存数据
    city_sales.saveAsTextFile(output_path)
    
    sc.stop()
    print(f"数据已保存到: {output_path}")
if __name__ == '__main__':
    save_city_sales()
 