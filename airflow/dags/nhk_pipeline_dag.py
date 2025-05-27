import sys
import os

project_path = os.getenv('PROJECT_PATH')
sys.path.append(project_path)

#TODO Airflow DAG files like nhk_pipeline_dag.py aren’t meant to be run directly in PyCharm or with python script.py. Airflow imports them automatically in the scheduler and executes tasks via the CLI or web UI.
#TODO create individual tasks, running scripts in IDE, then try running airflow at the end

from scrapeNHKnews import scrape_NHK
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator


with DAG(
   "kanji_counter",
   start_date=days_ago(1),
   schedule_interval="@daily",
   catchup=False,
) as dag:
    # INSTALL BS4 BY HAND THEN CALL FUNCTION

    # ts are tasks
    t0 = BashOperator(
        task_id='task_zero',
        bash_command='pip install beautifulsoup4',
        retries=2
    )
    t1 = PythonOperator(
        task_id='task_one',
        depends_on_past=False,
        python_callable=scrape_NHK
    )
    t2 = PythonOperator(
        task_id='task_two',
        depends_on_past=False,
        python_callable=get_kanji
    )
    t3 = PythonOperator(
        task_id='task_three',
        depends_on_past=False,
        python_callable=load_SQL
    )
    t4 = PythonOperator(
        task_id='task_four',
        depends_on_past=False,
        python_callable=generate_visualization
    )
    t5 = PythonOperator(
        task_id='task_five',
        depends_on_past=False,
        python_callable=
    )

    # Task Dependencies (execution order)
    t0 >> t1 #>> t2 >> t3 >> t4 >> t5