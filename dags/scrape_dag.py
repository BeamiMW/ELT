from airflow import DAG
from airflow.utils.dates import days_ago
from datetime import timedelta
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from google.cloud import bigquery
import pandas as pd
import os

# define constants
DAG_ID = 'EL'
DATASET_NAME = 'demo'
TABLE_NAME = 'imdb_movie'
LOCAL_FILE_PATH = '/opt/airflow/data/imdb_top_20_indonesia.csv' 

# default args untuk DAG
default_args = {
    'owner': 'bmw',
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# function for load data from CSV to BigQuery
def load_to_bigquery():
    # set google cloud credentials dan inisialisasi client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/opt/airflow/gcloud_key.json'
    client = bigquery.Client()

    # define table ID
    table_id = f"{client.project}.{DATASET_NAME}.{TABLE_NAME}"

    # load data CSV to dataframe
    df = pd.read_csv(LOCAL_FILE_PATH)

    # job configuration untuk BigQuery
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # overwrite ke table (agar tidak append ke data yang telah ada u/ menghindari duplikat value)
        autodetect=True,  # deteksi schema otomatis
        source_format=bigquery.SourceFormat.CSV
        # skip_leading_rows=1  # skip header row di CSV, tidak pakai karena barisnya jadi berkurang kalau dipakai, harusnya 20 baris jadi 19 baris
    )

    # load data ke BigQuery
    load_job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load_job.result()  # tunggu sampai selesai

    print(f"Loaded {load_job.output_rows} rows into {table_id}.")

# define DAG
with DAG(
    dag_id=DAG_ID,
    schedule_interval='@once',  # eksekusi sekali
    default_args=default_args,
    catchup=False,
) as dag:

    # task untuk menjalankan file extract.py
    extract = BashOperator(
        task_id='extract',
        bash_command='xvfb-run --server-args="-screen 0 1920x1080x24" python3 /opt/airflow/scripts/scrape.py'  # path ke file scrape.py di dalam container. container Docker tidak memiliki akses ke layar fisik, maka Xvfb digunakan untuk mensimulasikan tampilan tersebut, dengan resolusi 1920x1080x24
    )

    # task untuk memuat data dari CSV ke BigQuery
    load = PythonOperator(
        task_id='load',
        python_callable=load_to_bigquery
    )

    extract >> load


