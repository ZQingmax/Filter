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


path = r"D:/search_log.txt"

def timeTop3():
    sc = create_spark_context_basic()
    
    rdd = sc.textFile(path).map(lambda x : x.split('\t'))
    top3 = rdd.map(lambda x : (x[0][:2],1))\
              .reduceByKey(lambda a,b:a + b)\
              .sortBy(lambda x : x[1],ascending=False)\
              .take(3)
    print(top3)
    sc.stop()
def searchWrodTop3():
    sc = create_spark_context_basic()
    
    rdd = sc.textFile(path).map(lambda x : x.split('\t'))
    top3 = rdd.map(lambda x : (x[2],1))\
              .reduceByKey(lambda a,b:a + b)\
              .sortBy(lambda x : x[1],ascending=False)\
              .take(3)
    print(top3)
    sc.stop()
def HeiMaMost():
    sc = create_spark_context_basic()
    
    rdd = sc.textFile(path).map(lambda x : x.split('\t'))
    top = rdd.filter(lambda word : word[2] == '黑马程序员')\
              .map(lambda x : (x[0][:2],1))\
              .reduceByKey(lambda a,b:a + b)\
              .sortBy(lambda x : x[1],ascending=False)\
              .take(1)
    print(top)
    sc.stop()
if __name__ == '__main__':
  timeTop3()
  # searchWrodTop3()
  # HeiMaMost()