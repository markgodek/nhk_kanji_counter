# NHK Kanji Counting Pipeline 🇯🇵📊

A containerized, end-to-end data engineering pipeline that scrapes Japanese news articles from NHK One, stores the raw text in a NoSQL document database, processes the text to count Kanji frequencies, and maintains a running aggregation in a relational SQL database.
This project was built to demonstrate modern data engineering principles including task orchestration, resilient web scraping, idempotent data processing, and multi-container microservice architecture.

## 🏗️ Architecture & Tech Stack
* Orchestration: Apache Airflow (Celery Executor)  
* Message Broker: Redis (for Airflow worker queues)  
* Ingestion / Scraping: Python, Playwright, BeautifulSoup, Flask (Playwright Microservice)  
* Data Lake / Raw Storage: MongoDB  
* Data Warehouse / Aggregation: MySQL  
* Presentation: Flask Web Application, Mongo Express  
* Infrastructure: Docker & Docker Compose  

## ✨ Key Features
* SPA Scraping Resilience: Bypasses JavaScript hydration issues and geographic modals on modern Single Page Applications (SPAs) by delegating web scraping to a custom headless Playwright microservice.  
* Idempotent Processing: Uses SHA-256 hashing and a processed_hashes metadata table to ensure articles are never double-counted, even if the pipeline is run multiple times or encounters failures.  
* Efficient Upserts: Batch processes raw data from MongoDB and utilizes MySQL's ON DUPLICATE KEY UPDATE to maintain a running tally of Kanji characters with minimal database overhead.  
* Fully Containerized: The entire environment (databases, web servers, scrapers, and orchestration nodes) spins up reliably using Docker Compose.  

## 📂 Project Structure
```
├── docker-compose.yml           # Multi-container cluster definition  
├── Dockerfile                   # Custom Airflow image with Python dependencies  
├── Dockerfile.flask             # Flask web app image  
├── Dockerfile.playwright        # Playwright headless browser image  
├── requirements.txt             # Airflow dependencies  
├── flask.requirements.txt       # Flask app dependencies  
├── playwright.requirements.txt  # Playwright service dependencies  
├── show_articles.py             # Flask web UI for viewing raw articles  
├── airflow/  
│   ├── nhk_pipeline_dag.py      # Airflow DAG definition  
│   ├── scrapeNHKnews.py         # Ingestion script (Playwright -> Mongo)  
│   ├── load_SQL.py              # Processing script (Mongo -> Kanji counts -> MySQL)  
│   ├── load_mongo.py            # MongoDB insertion helper  
│   └── webserver_config.py      # Airflow UI config  
├── common/  
│   └── mongo_connection.py      # Shared DB connection logic  
├── mysql-init/  
│   └── nhkDB.sql                # SQL initialization (Tables: kanji_count, metadata, processed_hashes)  
└── playwright/  
    └── playwright_service.py    # Flask API wrapping Playwright async browser logic
```
	
## 🚀 Getting Started
### Prerequisites  
1. Docker and Docker Compose installed.  
2. Git installed on your local machine.  

### Installation & Execution
1. Clone the repository  
2. Build the Docker images  
This step compiles the custom Airflow environment and installs the necessary headless browser binaries for Playwright.  
`docker-compose build`  
3. Initialize the Airflow Database  
Before starting the cluster, initialize the Airflow backend and create the default admin user. Wait for this command to finish and exit successfully.  
`docker-compose up airflow-init`  
4. Start the ClusterSpin up all services in detached mode.  
`docker-compose up -d`  
5. Trigger the Pipeline  
Navigate to the Airflow UI at http://localhost:8080.  
Log in using the credentials found in the table below
Unpause the kanji_counter DAG using the toggle on the left.  
Click the "Play" button under "Actions" to trigger a manual run.  

## 🖥️ Web Interfaces
Once the cluster is running, you can monitor the pipeline and view the data via the following interfaces:  

| Service | URL | Authentication | Description |
| :--- | :--- | :--- | :--- |
| **Airflow UI** | `http://localhost:8080` | `airflow` / `airflow` | Trigger the DAG and view task logs. |
| **Mongo Express** | `http://localhost:8082` | `admin` / `pass` | Inspect the raw scraped articles in MongoDB. |
| **Flask App** | `http://localhost:5000` | None | A custom paginated UI to read the scraped Japanese text. | 

## 🛑 Stopping the Cluster
To spin down the containers while preserving your database volumes:  
`docker-compose down`  
To spin down and completely wipe all databases and volumes (start fresh):  
`docker-compose down -v`
