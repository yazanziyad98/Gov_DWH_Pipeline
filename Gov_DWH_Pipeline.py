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
    .config("spark.hadoop.fs.s3a.buffer.dir", "C:/Users/yazan/AppData/Local/Temp/s3a") \
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

    
def write_objects(destination,bucket,entity,df,table):
    date = datetime.now()
    path =  f"s3a://{bucket}/{entity}/{table}/{date.year}/{date.month}/{date.day}" 
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if destination.lower() == 'staging':
        df.write.parquet(f"{path}/{table}_{timestamp}")
    elif destination.lower() == 'dwh':
        df.writeTo(f"iceberg.{entity}.{table}.`{date.year}`.`{date.month}`.`{date.day}`").createOrReplace()

    return df 



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

print(2)
cspd_personal_info_df = cspd_personal_info \
            .withColumn("National_Number", (col("National_Number").cast("long"))) \
            .withColumn("Gender", (col("Gender").cast("int"))) \
            .withColumn("Religion_Code", (col("Religion_Code").try_cast("int"))) \
            .withColumn("Social_Status_Code", (col("Social_Status_Code").cast("int"))) \
            .withColumn("Birth_Country_Code", (col("Birth_Country_Code").cast("int"))) \
            .withColumn("Birth_Governorate_Code", (col("Birth_Governorate_Code").cast("int"))) \
            .withColumn("Birth_Kada_Code", (col("Birth_Kada_Code").cast("long"))) \
            .withColumn("Birth_Liwa_Code", (col("Birth_Liwa_Code").cast("long"))) \
            .withColumn("Father_National_Number", (col("Father_National_Number").cast("long"))) \
            .withColumn("Mother_National_Number", (col("Mother_National_Number").cast("long"))) 
 
ssc_insured_info_df = ssc_insured_info \
             .withColumn("National_Number", (col("National_Number").cast("long"))) 
 
ssc_salaries_df = ssc_salaries \
             .withColumn("National_Number", (col("National_Number").cast("long"))) 

ssc_insured_yearly_salary_df = ssc_insured_yearly_salary \
             .withColumn("Social_Security_Number", (col("Social_Security_Number").cast("long"))) 


ssc_insured_transaction_df =  ssc_insured_transaction \
             .withColumn("Social_Security_Number", (col("Social_Security_Number").cast("long")))


cspd_personal_info_stg = write_objects('staging',bucket ='gov.data', entity='cspd',df = cspd_personal_info_df,table ="cspd_personal_info")
ssc_insured_info_stg = write_objects('staging',bucket ='gov.data', entity='ssc',df = ssc_insured_info_df,table ="ssc_insured_info")
ssc_salaries_stg = write_objects('staging',bucket ='gov.data', entity='ssc',df = ssc_salaries_df,table ="ssc_salaries")
ssc_insured_yearly_salary_stg = write_objects('staging',bucket ='gov.data', entity='ssc',df = ssc_insured_yearly_salary_df,table ="ssc_insured_yearly_salary")
ssc_insured_transaction_stg = write_objects('staging',bucket ='gov.data', entity='ssc',df = ssc_insured_transaction_df,table ="ssc_insured_transaction")
