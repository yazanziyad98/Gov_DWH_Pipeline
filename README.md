# Governmental Data Warehouse Pipeline

> A production-grade, parallelism-first replacement for a legacy **SQL Server + SSIS** ETL stack, built on **Apache MiNiFi → Apache NiFi → PySpark on YARN → MinIO → Apache Iceberg**, orchestrated by **Apache Airflow**. Real architecture from a governmental data integration project; data is masked and downstream consumers are omitted, but the topology and code are real.

![Stack](https://img.shields.io/badge/Spark-3.x_on_YARN-E25A1C?logo=apachespark&logoColor=white)
![NiFi](https://img.shields.io/badge/NiFi-2.9.0-728E9B?logo=apachenifi&logoColor=white)
![MiNiFi](https://img.shields.io/badge/MiNiFi-Java-728E9B?logo=apachenifi&logoColor=white)
![CEFM](https://img.shields.io/badge/Cloudera_EFM-managed-EE0000?logo=cloudera&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-3.0.6-017CEE?logo=apacheairflow&logoColor=white)
![Iceberg](https://img.shields.io/badge/Iceberg-Hadoop_Catalog-4FC3F7?logo=apache&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-distributed_3_nodes-C72E49?logo=minio&logoColor=white)
![CDP](https://img.shields.io/badge/Cloudera_CDP-7.3.1-EE0000?logo=cloudera&logoColor=white)
![RHEL](https://img.shields.io/badge/RHEL-9.5-EE0000?logo=redhat&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

A two-tier **medallion data warehouse** with **edge-to-core streaming ingestion** at the source side and **distributed batch transformation** at the analytical side.

**Apache MiNiFi** runs on an edge server outside the cluster network, continuously pulling citizen-level records from the operational MySQL via `QueryDatabaseTableRecord` (keyed on an incremental `message_num` column) and shipping the result to a 2-node **central NiFi cluster** via **Site-to-Site over HTTP**. A built-in **disaster-recovery sub-flow** falls back to CSV snapshots on the edge server when the source database is unreachable. Central NiFi stamps a `load_date` lineage column and lands the records in a staging MySQL.

An hourly  **Airflow** DAG triggers a **PySpark job with YARN** (3 NodeManagers). The job performs 15-way parallel partitioned JDBC reads against staging, lands the raw frame as **Bronze (Parquet)** on a 3-node distributed **MinIO** cluster, applies type coercion, cross-system joins, dimensional modeling, and business rules, then writes the curated output as **Gold (Apache Iceberg)** tables.

The whole stack replaces a legacy **SQL Server + SSIS** ETL that was single-speed, batch-only, and tightly coupled to a SQL transformation engine. The new design parallelizes work at **every** layer, runs continuously instead of nightly, decouples compute from storage, and keeps source-DB credentials and IPs entirely off the central NiFi cluster.

Sample dataset: **~14.4 million rows** across five tables. Real production scale: **~1.4 billion rows** (100×).

---

## Table of Contents

1. [Why this project exists](#why-this-project-exists)
2. [Architecture](#architecture)
3. [Data scale](#data-scale)
4. [End-to-end data flow](#end-to-end-data-flow)
5. [Tech stack](#tech-stack)
6. [Edge ingestion: MiNiFi](#edge-ingestion-minifi)
7. [Resilience and disaster recovery](#resilience-and-disaster-recovery)
8. [Central NiFi: receive and route](#central-nifi-receive-and-route)
9. [The Spark transformation layer](#the-spark-transformation-layer)
10. [Storage layer: MinIO + Iceberg](#storage-layer-minio--iceberg)
11. [Orchestration: Airflow](#orchestration-airflow)
12. [Operational notes](#operational-notes)
13. [Repository layout](#repository-layout)
14. [Running the pipeline](#running-the-pipeline)
15. [Schema, partitioning, and derived columns](#schema-partitioning-and-derived-columns)
16. [Roadmap](#roadmap)
17. [License](#license)

---

## Why this project exists

The legacy stack was **SQL Server + SSIS**. It worked for years, but as the need evolved past nightly batch reporting, four specific limitations dominated:

1. **One speed, one machine.** SSIS executed packages at a fixed throughput ceiling with no horizontal scaling path, you could tune buffer sizes and upgrade the host, but you could not add nodes. NiFi scales by adding processors and clustering; Spark scales by adding executors across NodeManagers. There was also no native path to *streaming*, every change to source data had to wait for the next package run.
2. **Once-a-day execution.** Anything that happened during the day was invisible to the warehouse until the next morning. Modern downstream consumers (operational dashboards, near-real-time integrations) couldn't be served at all.
3. **Narrow connector ecosystem.** The customer's roadmap explicitly required direct writes to **MinIO**, **Kafka** publish/consume, heavy **text/file manipulation**, and live ingestion over **UDP and TCP** sockets, all native NiFi processors, all custom Script Component territory in SSIS.
4. **Transformation engine couldn't keep up.** Some transformations were fundamentally too heavy for SQL-on-SQL-Server. They needed a real distributed compute engine, **Spark**.

The redesign keeps business semantics identical but moves every stage onto modern, horizontally parallel primitives:

| Old (SSIS / SQL Server)                               | New (MiNiFi → NiFi → Spark → Iceberg / MinIO)                          |
|---|---|
| Single-threaded "one speed" execution                  | Continuous edge capture + 15-way parallel Spark JDBC reads              |
| Once-nightly batch run                                 | MiNiFi runs 24/7; Airflow triggers Spark hourly for transformation       |
| OLE DB / file / SQL Server connectors only             | NiFi processors for MinIO, Kafka, UDP, TCP, files, text manipulation    |
| Mainly SQL-only transformation engine in SSIS Data Flow       | PySpark on YARN for heavy transformations; Iceberg for ACID/evolution   |
| Compute + storage fused on one SQL Server box          | Spark (3 nodes) and MinIO (3 nodes) scale independently |
| Source-DB credentials exposed to the ETL server        | Source DB only reachable from the edge MiNiFi; central NiFi never sees it |
| Schema changes nees an SSIS package redeploys                | Iceberg schema evolution without rewriting historical data              |

---

## Architecture

Two trust zones, one logical pipeline:

- **Edge server**, outside the cluster network, close to the source MySQL. Runs only **MiNiFi** (Java), managed remotely by **Cloudera Edge Flow Manager (CEFM)**. Holds source-DB credentials. Holds CSV recovery snapshots maintained by a cron task.
- **Cluster network**, runs everything else: **2-node NiFi cluster**, **staging MySQL**, **3-node MinIO** (distributed), 3-nodes for **Spark**, and **Airflow**. None of the components in this zone ever learn the source database's hostname or credentials.

**Two execution rhythms:**

- **MiNiFi runs continuously**, picking up new rows the moment they appear in the source MySQL, the streaming layer.
- **Airflow + Spark run hourly**, snapshotting whatever NiFi has accumulated into staging and producing the day's Bronze + Gold outputs,     the analytical layer.


---

## Data scale

The repository ships with a **sample dataset** sized to be reproducible on modest hardware. Real production volume is **~100×**.

| Table | Sample rows | Spark partition column |
|---|---:|---:|---|
| `salaries`              | 6,000,030  | `Social_Security_Number` |
| `personal_info`        | 4,398,818   | `Birth_Date` |
| `insured_info`          | 2,000,000  | `Social_Security_Number` |
| `insured_transaction`   | 1,000,000  | `Social_Security_Number` |
| `insured_yearly_salary` | 1,000,000  | `Social_Security_Number` |
| **Total**                   | **~14.4 M**| **~1.4 B** | |

At real-project scale, a naïve single-threaded `SELECT * FROM table` over JDBC would take hours per table and blow the driver heap before yielding the first row. Every parallelism and memory choice in the codebase — `numPartitions=15`, `fetchsize=5000`, `useCursorFetch=true`, executor counts, `socketTimeout=1800000` — exists because of this scale.

---

## End-to-end data flow

1. **MiNiFi** on the edge runs `QueryDatabaseTableRecord` against each source table, using `message_num` (a monotonically increasing column on the source) as the maximum-value column for incremental state. Only rows newer than the persisted watermark get fetched per cycle.
2. In parallel, a **disaster-recovery sub-flow** on MiNiFi attempts an `ExecuteSQL` probe on a schedule. If the probe fails (source DB unreachable), the failure relationship routes to `FetchFile` processors that pull the latest CSV backup snapshots from local disk. Either path lands on the same Site-to-Site sink.
3. **Site-to-Site over HTTP** ships the resulting flowfiles from the edge to the central NiFi cluster's Input Port. S2S handles back-pressure, retry, and resumable transfer natively.
4. **Central NiFi** routes from the Input Port through `UpdateRecord` (which stamps `load_date = ${now():format('yyyy-MM-dd HH:mm:ss')}`) and `PutDatabaseRecord` into the staging MySQL (`gov` database).
5. **Airflow** fires `@daily` and `spark-submit`s the PySpark job onto **Cloudera CDP YARN**.
6. **Spark** discovers numeric bounds per table (`SELECT MIN/MAX(partition_col)`), performs a **15-way parallel JDBC read** with cursor-based fetching, lands the raw frame in the **Bronze** bucket as Parquet, applies type casts and business rules, and writes the curated result as **Gold** Iceberg tables.

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| **Source** | MySQL (operational, on edge-adjacent network) | System of record; only the edge MiNiFi ever connects to it |
| **Edge agent** | Apache MiNiFi (Java) | Lightweight footprint; network-isolated from the cluster; full processor compatibility with NiFi |
| **Edge orchestration** | Cloudera Edge Flow Manager (CEFM) | Centralized configuration, version, and deploy management for the edge agent |
| **Edge-to-core transport** | NiFi Site-to-Site over HTTP | Back-pressure-aware, resumable; source IPs/creds never leave the edge |
| **Central routing** | Apache NiFi 2.9.0 (2-node cluster) | Receives via Input Port; stamps `load_date`; writes to staging MySQL |
| **Staging DB** | MySQL 8 (`gov`) | Decoupling layer; Spark hammers it at full parallelism without touching the operational source |
| **Compute** | PySpark 3.x on Cloudera CDP YARN (3 NodeManagers) | Distributed transformation; horizontally scalable |
| **Bronze storage** | MinIO (3-node distributed) + Parquet | S3-compatible, erasure-coded, partitioned by load date |
| **Gold storage** | MinIO + Apache Iceberg (Hadoop catalog) | ACID, time travel, schema/partition evolution, no metastore dependency |
| **Orchestration** | Apache Airflow 3.0.6 | Daily scheduling, retry/SLA semantics, log centralization |
| **Runtime** | RHEL 9.5, Java 21 OpenJDK, Python 3.9.21 | Server-grade Linux |

---

## Edge ingestion: MiNiFi

`[add screenshot of MiNiFi flow]`

### Why MiNiFi instead of putting NiFi on the edge?

Two reasons, both load-bearing:

1. **Lightweight footprint.** MiNiFi Java is designed for edge deployment — minimal heap, no UI overhead, no bundled service catalog. It runs comfortably on an edge box that can't justify a full NiFi installation.
2. **Network isolation.** Source database hostnames, credentials, and JDBC URLs **never leave the edge server**. Central NiFi only ever sees an inbound Site-to-Site connection from the edge; it has no route to, no knowledge of, and no credentials for the operational source. A compromised central NiFi node cannot pivot to the source database, because it doesn't have what it would need to even try.

### Management: Cloudera Edge Flow Manager (CEFM)

The edge agent is configured, versioned, and deployed remotely from **Cloudera Edge Flow Manager**. The MiNiFi instance on the edge pulls its flow definition from CEFM on boot and on demand; flow updates are pushed centrally without SSHing onto the edge box. This is the enterprise pattern for fleets of edge agents.

### The two MiNiFi sub-flows

The same MiNiFi canvas hosts two structurally independent ingest paths:

**(1) Primary — routine incremental capture**

```
QueryDatabaseTableRecord (per source table)
    │  • Table_Name = <source_table>
    │  • Maximum-Value Columns = message_num
    │  • Record Writer = AvroRecordSetWriter
    ▼
Remote Process Group → <central-nifi-host>:S2S Input Port
```

One `QueryDatabaseTableRecord` instance per source table. The processor tracks the high-watermark of `message_num` in its persistent state, so each cycle picks up only rows with `message_num > last_seen`. No external state store needed; it's handled by NiFi's local state provider.

**(2) Fallback — disaster recovery from CSV snapshots**

```
GenerateFlowFile (cron-style trigger)
    │
    ▼
ExecuteSQL (probe / fetch from source MySQL)
    │
    ├── success ─► (data flows through normal path)
    │
    └── failure ─► FetchFile (per table, points at CSV backup on edge disk)
                       │
                       ▼
                   Remote Process Group → <central-nifi-host>:S2S Input Port
```

When the source MySQL is unreachable, `ExecuteSQL`'s `failure` relationship routes the flowfile to `FetchFile`, which reads the latest CSV snapshot from local disk. The CSV snapshots themselves are produced and rotated by a **cron job on the customer's operating system**, fully outside this pipeline's responsibility. From the central NiFi's perspective, the failover is invisible — the same Input Port receives the data either way.

This is the kind of design choice that doesn't matter until the day the source database is unreachable, and then it's the only thing that matters.

### The `load_date` lineage column

```
${now():format('yyyy-MM-dd HH:mm:ss')}
```

Stamped on **central NiFi** (post-S2S, pre-staging-write), the simplest lineage column that solves three real problems:

1. **Reconciliation** — If a Spark run fails halfway, the next run can filter `WHERE load_date > last_successful_run` and avoid reprocessing rows that already made it to Bronze.
2. **Audit** — "When did this row arrive in our system?" is a question downstream consumers ask constantly. `load_date` answers it without depending on the source's clock.
3. **Backfill identification** — Rows ingested during a backfill carry the backfill's timestamp, making it trivial to isolate or replay them.

---

## Resilience and disaster recovery

| Failure mode | Detection | Recovery |
|---|---|---|
| Source MySQL unreachable | `ExecuteSQL` failure relationship | `FetchFile` reads CSV snapshot maintained by customer cron; Site-to-Site sink is unchanged |
| S2S transport interrupted | Built-in S2S retry + back-pressure | NiFi side queues; MiNiFi resumes from last acknowledged batch |
| Central NiFi node down | 2-node cluster + ZK-coordinated failover | The other node continues serving the Input Port |
| Staging MySQL write fails | `PutDatabaseRecord` failure relationship + NiFi back-pressure | Flowfile queues on NiFi disk until staging recovers |
| Spark job fails mid-run | Airflow task failure + retry | Re-run filters by `load_date > last_success` (planned, see [Roadmap](#roadmap)) |
| MinIO node down | 3-node distributed erasure coding | Writes continue against surviving quorum |

The pattern across all of these is the same: failure is detected at the closest possible point, and the recovery action is local — no cascading retries from far away.

---

## Central NiFi: receive and route

`[add screenshot of central NiFi receiver flow]`

Central NiFi's job is intentionally narrow:

```
S2S Input Port
    │
    ▼
UpdateRecord  ──  adds load_date = ${now():format('yyyy-MM-dd HH:mm:ss')}
    │
    ▼
PutDatabaseRecord  ──  JDBC batch insert into gov.<table>
```

No source-database connection. No source credentials. No source IPs in the flow definition. The Input Port is the only thing reachable from outside the cluster network, and Site-to-Site over HTTP handles authentication and back-pressure at the protocol level.

The 2-node cluster runs in active-active mode; either node can serve the Input Port and either node can run the downstream processors. The flow definition is replicated through NiFi's cluster coordination layer.

---

## The Spark transformation layer

The full job lives in `spark/pyspark_test.py`. Running on Cloudera CDP YARN — the `--master`, `--deploy-mode`, and resource flags are passed at `spark-submit` time, not in the `SparkSession.builder`.

### 1. Dynamic bounds discovery + parallel JDBC read

```python
bound = spark.read.format("jdbc") \
    .option("dbtable",
        f"(SELECT MIN({partition_col}) AS low_bound, "
        f"        MAX({partition_col}) AS up_bound "
        f"   FROM gov.{table}) AS tbl") \
    .load().collect()[0]

df = spark.read.format("jdbc") \
    .option("dbtable", table) \
    .option("partitionColumn", partition_col) \
    .option("lowerBound", bound[0]) \
    .option("upperBound", bound[1]) \
    .option("numPartitions", 15) \
    .option("fetchsize", "5000") \
    .load()
```

Instead of hardcoding bounds (which goes stale the moment rows are added), the job **discovers them at runtime** with a cheap MIN/MAX query, then issues 15 concurrent `WHERE partition_col BETWEEN x AND y` queries against MySQL. Cursor-based fetch (`fetchsize=5000`) keeps the JDBC driver from materializing entire result sets in memory.

Partition columns:
- SSC tables → `Social_Security_Number` (monotonically issued, dense)
- CSPD personal info → `Birth_Date` (uniformly distributed across decades)

### 2. Type coercion with dirty-data tolerance

The source columns arrive as strings (legacy SSIS pattern that the operational MySQL inherited). The job re-types them on read:

```python
.withColumn("National_Number",        col("National_Number").cast("long"))
.withColumn("Religion_Code",          col("Religion_Code").try_cast("int"))
.withColumn("Birth_Kada_Code",        col("Birth_Kada_Code").cast("long"))
.withColumn("Father_National_Number", col("Father_National_Number").cast("long"))
```

Note the `try_cast` on `Religion_Code` — known to occasionally contain non-numeric junk in legacy rows. `try_cast` returns `NULL` instead of throwing, so a single malformed value doesn't fail the whole stage.

### 3. Cross-system join and dimensional modeling

The two source systems are linked by `National_Number`:

```python
def natNumber_filter(table):
    return cspd_personal_info_stg[['National_Number']] \
        .join(table, "National_Number", "inner")
```

This filters SSC tables down to citizens who exist in the civil registry — eliminating orphan insurance records before they hit Gold.

**A real dimension:**

```python
dim_country = spark.sql(
    "SELECT DISTINCT Birth_Country_Code, Birth_Country "
    "FROM cspd_personal_info_stg")
cspd_personal_info_dip = cspd_personal_info_dip.drop("Birth_Country")
```

`Birth_Country` (the descriptive string) is lifted into its own `dim_country` table; the fact-side `cspd_personal_info` keeps only `Birth_Country_Code`. Textbook star-schema normalization.

### 4. `IS_Diplomat` derived flag

```python
cspd_personal_info_dip = spark.sql("""
    SELECT *,
           CASE WHEN Passport_Number LIKE '0000%'
                THEN 1 ELSE 0 END AS IS_Diplomat
    FROM cspd_personal_info_stg
""")
```

A boolean flag derived from the passport-number prefix, computed once at write time so downstream consumers don't have to re-encode the rule.

### 5. Bronze and Gold writes

```python
def write_objects(destination, bucket, entity, df, table):
    date = datetime.now()
    path = f"s3a://{bucket}/{entity}/{table}/{date.year}/{date.month}/{date.day}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if destination.lower() == 'staging':
        df.write.parquet(f"{path}/{table}_{timestamp}")
    elif destination.lower() == 'dwh':
        df.writeTo(
            f"iceberg.{entity}.{table}.`{date.year}`.`{date.month}`.`{date.day}`"
        ).createOrReplace()
```

- **Bronze (`gov.data`)** — timestamped Parquet directories, one per run. Immutable. Cheap to reprocess.
- **Gold (`gov.data.gold`)** — Iceberg tables with date-hierarchical namespacing. ACID writes, time travel via snapshots, schema evolution without rewriting data.

---

## Storage layer: MinIO + Iceberg

### MinIO — 3-node distributed cluster

Three MinIO nodes form a single distributed cluster with **erasure coding**: data is sharded across nodes with parity blocks, so the cluster tolerates node loss without losing data and continues to serve reads and writes during single-node failure.

Spark talks S3A to the cluster:

```python
.config("spark.hadoop.fs.s3a.endpoint", "http://<minio-endpoint>:9000")
.config("spark.hadoop.fs.s3a.path.style.access", "true")
.config("spark.hadoop.fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
```

`path.style.access=true` is mandatory for MinIO — it doesn't support virtual-host-style addressing.

### Iceberg catalog wiring

```python
.config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
.config("spark.sql.catalog.iceberg.type", "hadoop")
.config("spark.sql.catalog.iceberg.warehouse", "s3a://gov.data.gold/")
```

A **Hadoop-type** Iceberg catalog: no external Hive Metastore, no Nessie service — Iceberg stores its own metadata as files alongside the data. Self-contained, single-writer-safe. Migrating to a REST catalog (Nessie, Polaris) for multi-writer or external query engine support is a config change, not a rewrite.

---

## Orchestration: Airflow

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="gov_dwh_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["dwh", "spark", "yarn"],
) as dag:
    run_pipeline = BashOperator(
        task_id="run_spark_pipeline",
        bash_command="""
            export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-21.0.7.0.6-1.el9.x86_64 && \
            export PATH=$JAVA_HOME/bin:$PATH && \
            spark-submit \
                --master yarn \
                --deploy-mode client \
                --num-executors <TBD> \
                --executor-memory <TBD> \
                --executor-cores <TBD> \
                --driver-memory <TBD> \
                --jars /home/admin/spark_test/jars/mysql-connector-j-9.5.0.jar \
                /home/admin/spark_test/pyspark_test.py
        """,
    )
```

**Design choices:**

- `catchup=False` — no point firing a year of historical runs on first deploy.
- `BashOperator` over `SparkSubmitOperator` — keeps the Airflow Spark provider out of the venv, and the bash command is the *exact* same string that works manually, which is invaluable for debugging.
- `--master yarn --deploy-mode client` — driver runs on the Airflow worker so log streaming works cleanly through Airflow's task log infrastructure. `cluster` deploy mode would push the driver into a YARN container that Airflow can't directly tail.
- `JAVA_HOME` exported inside the bash command — required because Spark needs to know which JDK to use when launching YARN containers, and the Airflow worker's environment doesn't carry the shell login profile.
- Resource flags are placeholders to be sized against the actual cluster.

---

## Operational notes

A few configuration details worth flagging for anyone reproducing or operating the pipeline:

**JDBC at scale.** MySQL Connector/J defaults to materializing the entire result set in the driver heap before yielding the first row. At hundreds of millions of rows, that OOMs the Spark driver in seconds. The fix is two-fold — set `useCursorFetch=true` in the JDBC URL and `fetchsize=5000` on every Spark read.

**Spark resource flags must be set at submit time, not in `.config()`.** Driver memory, executor count, executor memory, and executor cores all need to be passed to `spark-submit` as command-line flags. Setting them via `SparkSession.builder.config(...)` is too late — the JVM is already running by then and silently ignores the values.

**`JAVA_HOME` inside the Airflow BashOperator.** Airflow workers don't execute a login shell, so the user's `~/.bashrc` exports don't carry over to the task subprocess. Export `JAVA_HOME` and prepend `$JAVA_HOME/bin` to `PATH` *inside* the BashOperator command string itself.

**Airflow API auth.** In `~/airflow/airflow.cfg` set `[api_auth] jwt_issuer = airflow` and `load_examples = False`.

---

## Repository layout

```
.
├── README.md                          # this file
├── airflow/
│   └── dags/
│       └── gov_dwh_pipeline.py        # the Airflow DAG (YARN spark-submit)
├── spark/
│   ├── pyspark_test.py                # the Spark transformation job
│   └── jars/
│       └── mysql-connector-j-9.5.0.jar
├── minifi/
│   └── gov_edge_flow.json             # MiNiFi flow definition (exported from CEFM)
├── nifi/
│   └── gov_receiver_flow.xml          # Central NiFi receiver flow (Input Port + UpdateRecord + PutDatabaseRecord)
└── docs/
    ├── minifi_flow.png                # [add screenshot of MiNiFi flow]
    └── nifi_receiver_flow.png         # [add screenshot of NiFi receiver flow]
```

---

## Running the pipeline

### Prerequisites

**Edge server** (separate from the cluster):

- Apache MiNiFi (Java) installed
- Cloudera Edge Flow Manager reachable from the edge box
- Source MySQL credentials configured in MiNiFi's `QueryDatabaseTableRecord` and `ExecuteSQL` processors
- MySQL Connector/J in MiNiFi's lib path
- Local directory with CSV backup snapshots maintained by the customer's cron

**Cluster** (RHEL 9.5+ hosts):

- Cloudera CDP 7.3.1 with YARN (3 NodeManagers minimum) and Spark
- 2-node NiFi cluster
- 3-node distributed MinIO with two buckets pre-created: `gov.data`, `gov.data.gold`
- Staging MySQL 8 reachable from the NiFi cluster and from the Spark NodeManagers
- Java 21 OpenJDK
- Python 3.9 with `pip`
- Airflow 3.0.6 in a Python venv

### Install MySQL Connector/J (wherever a JDBC client is needed)

```bash
wget https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.5.0/mysql-connector-j-9.5.0.jar \
     -P /home/admin/spark_test/jars/
```

### Cluster-side setup

```bash
# Java 21
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-21.0.7.0.6-1.el9.x86_64
export PATH=$JAVA_HOME/bin:$PATH

# Python venv for Airflow
python3.9 -m venv ~/airflow_venv
source ~/airflow_venv/bin/activate
pip install apache-airflow==3.0.6

# Airflow config
export AIRFLOW_HOME=~/airflow
airflow db migrate
# edit ~/airflow/airflow.cfg:
#   load_examples = False
#   [api_auth] jwt_issuer = airflow
airflow users create --role Admin --username admin --email admin@example.com ...

# Deploy DAG
cp airflow/dags/gov_dwh_pipeline.py ~/airflow/dags/
```

### Daily run (Airflow-managed)

The DAG is scheduled `@daily`. Manual trigger:

```bash
source ~/airflow_venv/bin/activate
airflow dags trigger gov_dwh_pipeline
```

Logs live at `~/airflow/logs/dag_id=gov_dwh_pipeline/...`.

---

## Schema, partitioning, and derived columns

### Source tables (masked names retained)

| Entity | Table | Partition column (Spark JDBC) | Notes |
|---|---|---|---|
| `ssc` | `ssc_salaries` | `Social_Security_Number` | Monthly salary records per insured |
| `ssc` | `ssc_insured_transaction` | `Social_Security_Number` | Insurance event log |
| `ssc` | `ssc_insured_info` | `Social_Security_Number` | Demographic snapshot per insured |
| `ssc` | `ssc_insured_yearly_salary` | `Social_Security_Number` | Annual aggregate (pre-computed in source) |
| `cspd` | `cspd_personal_info` | `Birth_Date` | Civil-registry master record |

All five tables share an incremental `message_num` column on the source — that's the column MiNiFi's `QueryDatabaseTableRecord` uses as its maximum-value watermark.

### Bronze partitioning

```
s3a://gov.data/{entity}/{table}/{YYYY}/{MM}/{DD}/{table}_{YYYYMMDD_HHMMSS}/
```

`{YYYY}/{MM}/{DD}` is the **load date** (Spark job's clock), not a business date. A single Bronze partition contains everything ingested in a single daily run.

### Gold (Iceberg) namespacing

```
iceberg.{entity}.{table}.`{YYYY}`.`{MM}`.`{DD}`
```

Iceberg's hierarchical namespace mirrors the Bronze path. Backticks are needed because numeric identifiers aren't valid SQL identifiers without quoting.

### Derived columns and dimensions

- **`load_date`** — set in central NiFi via `UpdateRecord`, carried through every layer.
- **`IS_Diplomat`** — boolean flag derived in Spark from `Passport_Number LIKE '0000%'`.
- **`dim_country`** — extracted as a true dimension; the fact-side keeps only `Birth_Country_Code`.

---

## Roadmap

| # | Item | Rationale |
|---|---|---|
| 1 | **Iceberg merge-on-read CDC** | Gold is currently `createOrReplace` per day. Switch to `MERGE INTO` with `load_date` as the high-water mark for true incremental Gold. |
| 2 | **Iceberg partition evolution** | Once query patterns stabilize, evolve partitioning (e.g., by `Birth_Country_Code` for CSPD) without rewriting historical data. |
| 3 | **Postgres for Airflow metadata** | SQLite is fine for one DAG; move to PostgreSQL when concurrency grows. |
| 4 | **TLS on Site-to-Site** | Currently HTTP. Move to HTTPS S2S with mutual TLS once cert lifecycle tooling is in place. |
| 5 | **Data quality gates** | Great Expectations or Soda checks between Bronze and Gold (row counts, null rates, referential integrity on `National_Number`). |
| 6 | **REST Iceberg catalog** | Swap Hadoop-type catalog for a REST catalog (Nessie, Polaris) to support multiple writers and external query engines (Trino, DuckDB). |
| 7 | **MiNiFi clustering / failover** | Single edge MiNiFi today. Cold-standby on a second edge box would close the last remaining single-point-of-failure. |
| 8 | **Kafka and UDP/TCP ingestion paths** | Wire the connector capabilities the platform was chosen for: real-time event streams from operational systems. |
| 9 | **Column-level lineage** | OpenLineage emitter on the Spark job → Marquez → end-to-end column lineage from source through Iceberg. |

---

## License

[MIT](LICENSE) — see `LICENSE` for details.

---

*Built on real governmental data. Names, columns, and downstream consumers are masked; architecture and code are real.*
