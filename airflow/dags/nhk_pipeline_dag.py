import sys
import os

project_path = os.getenv('PROJECT_PATH')
sys.path.append(project_path)

from scrapeNHKnews import main
from count_kanji import batch_process
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator

#TODO Airflow DAG files like nhk_pipeline_dag.py aren’t meant to be run directly in PyCharm or with python script.py.
# Airflow imports them automatically in the scheduler and executes tasks via the CLI or web UI.
# TODO create individual tasks, running scripts in IDE, then try running airflow at the end

with DAG(
   "kanji_counter",
   start_date=days_ago(1),
   schedule_interval="@daily",
   catchup=False,
) as dag:
    # INSTALL BS4 BY HAND THEN CALL FUNCTION

    # ts are tasks
    t1 = PythonOperator(
        task_id='task_one',
        depends_on_past=False,
        python_callable=main
    )
    t2 = PythonOperator(
        task_id='task_two',
        depends_on_past=False,
        python_callable=batch_process
    )

    # Task Dependencies (execution order)
    t1 >> t2# >> t3 >> t4 >> t5