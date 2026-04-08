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