from pyspark.sql import SparkSession
from pyspark.sql.types import * 
from pyspark.sql.functions import col
from datetime import datetime
import os
from dotenv import load_dotenv
 

load_dotenv() 



MINIO_ACCESS = os.getenv("MINIO_ACCESS")
MINIO_SECRET = os.getenv("MINIO_SECRET")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")

 


spark = SparkSession.builder.appName("Gov_DWH").master("local[6]") \
    .config("spark.driver.memory", "5g") \
    .config("spark.executor.memory", "5g") \
    .config("spark.driver.maxResultSize", "5g") \
    .config("spark.jars", r"C:\Users\yazan\Desktop\Workspace_2\Other\Setups\mysql-connector-j-9.5.0\mysql-connector-j-9.5.0.jar") \
    .config("spark.jars.packages", 
            "org.apache.hadoop:hadoop-aws:3.4.1,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262,"
            "org.apache.iceberg:iceberg-spark-runtime-4.0_2.13:1.10.1") \
    .config("spark.driver.extraClassPath", r"C:\Users\yazan\Desktop\Workspace_2\Other\Setups\mysql-connector-j-9.5.0\mysql-connector-j-9.5.0.jar") \
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS) \
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET) \
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg.type", "hadoop") \
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://gov.data.gold/") \
    .config("spark.sql.optimizer.excludedRules", "org.apache.spark.sql.catalyst.optimizer.SimplifyCasts") \
    .getOrCreate()





def read_modee_table(table,partition_col,partitions_num):

    url =  "jdbc:mysql://localhost:3306/modee"
 
    bound = spark.read \
            .format("jdbc") \
            .option("driver","com.mysql.cj.jdbc.Driver") \
            .option("url",url) \
            .option("dbtable", f"""(SELECT min({partition_col}) low_bound , 
                                    max({partition_col}) as up_bound 
                            FROM modee.{table}) as tbl""") \
            .option("user", "root") \
            .option("password", "mysql") \
            .load().collect()[0]  

    df = spark.read \
        .format("jdbc") \
        .option("driver","com.mysql.cj.jdbc.Driver") \
        .option("url", url) \
        .option("dbtable", table) \
        .option("user", "root") \
        .option("password", "mysql") \
        .option("partitionColumn",f'{partition_col}') \
        .option("lowerBound",bound[0]) \
        .option("upperBound",bound[1]) \
        .option("numPartitions",partitions_num) \
        .load() 
    return df

"""
Not Specifying Partitions will read the entie Table into one partitioms
hence all the data is loaded into ram at once when invokig a job;
which might crash
"""


ssc_salaries = read_modee_table(table = "ssc_salaries",partition_col = "Social_Security_Number",partitions_num = 30)
ssc_insured_transaction = read_modee_table(table = "ssc_insured_transaction",partition_col = "Social_Security_Number",partitions_num = 30)
ssc_insured_info = read_modee_table(table = "ssc_insured_info",partition_col = "Social_Security_Number",partitions_num = 30)
ssc_insured_yearly_salary = read_modee_table(table = "ssc_insured_yearly_salary",partition_col = "Social_Security_Number",partitions_num = 30)
cspd_personal_info = read_modee_table(table = "cspd_personal_info",partition_col = "Birth_Date",partitions_num = 30)
 
# Canidate for Partition Column ideally should be:
# 1. Numeric
# 2. Have High Cardinality 
# 3. Evenly Distributed (no skew)
# 4. should not be Nullable


 