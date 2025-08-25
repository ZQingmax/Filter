from pyspark import SparkConf, SparkContext
import os
import sys

# 方案一：基础修复版本
def create_spark_context_basic():
    """基础修复版本"""
    # Python解释器路径
    PYTHON_EXE = r"C:/Users/26612/AppData/Local/Programs/Python/Python311/python.exe"
    
    # 设置环境变量
    os.environ['PYSPARK_PYTHON'] = PYTHON_EXE
    os.environ['PYSPARK_DRIVER_PYTHON'] = PYTHON_EXE
    
    # 创建SparkConf - 添加超时配置
    conf = (SparkConf()
            .setMaster("local[1]")  # 使用单线程避免通信问题
            .setAppName("pyspark_windows_fix")
            .set("spark.sql.adaptive.enabled", "false")
            .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .set("spark.driver.memory", "2g")
            .set("spark.executor.memory", "1g")
           )
    
    sc = SparkContext(conf=conf)
    sc.setLogLevel("ERROR")  # 减少日志输出
    return sc

# 方案二：完整配置版本
def create_spark_context_advanced():
    """完整配置版本，解决Windows环境问题"""
    PYTHON_EXE = r"C:/Users/26612/AppData/Local/Programs/Python/Python311/python.exe"
    
    # 设置所有必要的环境变量
    os.environ['PYSPARK_PYTHON'] = PYTHON_EXE
    os.environ['PYSPARK_DRIVER_PYTHON'] = PYTHON_EXE
    os.environ['PYTHONPATH'] = sys.executable
    
    # 完整的Spark配置
    conf = (SparkConf()
            .setMaster("local[1]")  # 单线程模式
            .setAppName("pyspark_windows_advanced")
            # 网络和超时配置
            .set("spark.network.timeout", "300s")
            .set("spark.executor.heartbeatInterval", "60s")
            .set("spark.sql.adaptive.enabled", "false")
            .set("spark.sql.adaptive.coalescePartitions.enabled", "false")
            # 内存配置
            .set("spark.driver.memory", "2g")
            .set("spark.executor.memory", "1g")
            .set("spark.driver.maxResultSize", "1g")
            # Python配置
            .set("spark.executorEnv.PYTHONPATH", sys.executable)
            .set("spark.python.worker.reuse", "false")
            # 序列化配置
            .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
           )
    
    sc = SparkContext(conf=conf)
    sc.setLogLevel("ERROR")
    return sc

# 测试函数
def test_spark_operations(sc):
    """测试Spark操作"""
    print(f"Spark版本: {sc.version}")
    print("="*50)
    
    try:
        # 简单测试
        print("测试1: 基础操作")
        rdd1 = sc.parallelize([1, 2, 3, 4, 5])
        result1 = rdd1.map(lambda x: x * 2).collect()
        print(f"结果1: {result1}")
        
        print("\n测试2: 字符串操作")
        rdd2 = sc.parallelize(["hello", "world", "spark"])
        result2 = rdd2.map(lambda x: x.upper()).collect()
        print(f"结果2: {result2}")
        
        print("\n测试3: reduceByKey操作")
        rdd3 = sc.parallelize([('a', 1), ('b', 2), ('c', 6), ('c', 4), ('a', 3), ('b', 5)])
        result3 = rdd3.reduceByKey(lambda x, y: x + y).collect()
        print(f"结果3: {result3}")
        
        print("\n测试4: 排序操作")
        result4 = rdd3.reduceByKey(lambda x, y: x + y).sortBy(lambda x: x[1], ascending=False).collect()
        print(f"结果4: {result4}")
        
        print("\n所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False
    
    return True

# 主程序
if __name__ == "__main__":
    print("PySpark Windows 环境修复")
    print("="*50)
    
    # 尝试方案一：基础修复
    print("尝试方案一：基础修复")
    try:
        sc = create_spark_context_basic()
        if test_spark_operations(sc):
            print("方案一成功！")
        sc.stop()
    except Exception as e:
        print(f"方案一失败: {str(e)}")
        
        # 尝试方案二：完整配置
        print("\n尝试方案二：完整配置")
        try:
            sc = create_spark_context_advanced()
            if test_spark_operations(sc):
                print("方案二成功！")
            sc.stop()
        except Exception as e:
            print(f"方案二也失败: {str(e)}")
            print("\n请参考下面的替代方案")

# 如果上述方案都失败，使用最简单的本地测试
def simple_local_test():
    """最简单的本地测试，不依赖Spark集群模式"""
    print("\n最简本地测试（无集群模式）：")
    print("="*30)
    
    # 模拟你的数据处理逻辑
    data = [('a', 1), ('b', 2), ('c', 6), ('c', 4), ('a', 3), ('b', 5)]
    
    # 使用Python原生方法实现相同逻辑
    from collections import defaultdict
    
    # 相当于reduceByKey
    result_dict = defaultdict(int)
    for key, value in data:
        result_dict[key] += value
    
    # 相当于sortBy
    result = sorted(result_dict.items(), key=lambda x: x[1], reverse=True)
    
    print(f"原始数据: {data}")
    print(f"处理结果: {result}")
    
    return result

# 运行简单测试
if __name__ == "__main__":
    # 如果Spark有问题，至少可以验证逻辑
    simple_result = simple_local_test()