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

print(MINIO_ACCESS)