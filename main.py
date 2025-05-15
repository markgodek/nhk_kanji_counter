# do this https://classroom.emeritus.org/courses/9296/assignments/218600?module_item_id=1556656#

import re
import urllib.request
import time
import glob, os
import json
import chardet

from airflow import DAG
from datetime import timedelta

from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator

# url = 'https://www3.nhk.or.jp/news/'

# pull course catalog pages
def catalog():
    # define pull(url) helper function
    def pull(url):
        try:
            response = urllib.request.urlopen(url).read()
            data = response.decode('utf-8')
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:  # If the error is a 404, print and skip
                print(f"HTTPError 404 for URL: {url} - Page not found. Skipping...")
                return None  # Return None to signal failure
            else:
                # For other HTTP errors, log the error and return None
                print(f"HTTPError for URL: {url} - {e.code} {e.reason}")
                return None
        except urllib.error.URLError as e:
            print(f"URLError for URL: {url} - {e.reason}. Skipping...")
            return None  # Return None for URL errors
        except Exception as e:
            print(f"Unexpected error for URL: {url} - {str(e)}. Skipping...")
            return None  # Catch any other unexpected exceptions

    # define store(data,file) helper function
    def store(data, file):
        if data:  # Only store data if it is not None
            with open(file, 'w') as out:
                out.write(data)
                print(f'Wrote file: {file}')
        else:
            print(f"Skipping {file} due to missing data.")

    urls = [
        "https://www3.nhk.or.jp/news/"
    ]

    for url in urls:
        data = pull(url)
        print('pulled: ' + url)
        print('--- waiting ---')
        time.sleep(15)

        # get the index of the character after the last slash and
        # use everything after as the file name for use by the store function
        index = url.rfind('/') + 1
        file = url[index:]
        print('index: ', index)
        print('file: ', file)
        store(data, file)

# a function to determine the encoding of a website
def get_encoding(url):
    with urllib.request.urlopen(url) as response:
        raw_data = response.read()
        detected = chardet.detect(raw_data)
        print("Detected encoding:", detected)
        encoding = detected['encoding']
        return encoding

catalog()