# ADSDB
Project for the course *Algorithms, Data Structures and Databases* (ADSDB) of the Master's Degree in Data Science (MDS) taught at UPC.

## File structure
This project contains the following folders:
- **docs**: Latex documents for project report.
- **notebooks**: Notebooks containing proof-of-concepts related to the development of the data pipeline.
- **src**: Data pipeline and application code.

## Dependencies
Before we fix it up, this project requires some dependencies to have been installed

### Python dependencies
To install python libraries, execute:
```sh
pip install -r requirements.txt
```
And to install the model for Audio generation in the data collection phase:
To install the model, you must execute this command:
```sh
python3 -m piper.download_voices en_US-lessac-medium
```

### Ffmpeg
Audio objects are processed using pydub library, which depends on having ffmpeg installed. To do so, execute:
```sh
sudo apt-get install ffmpeg libavcodec-extra
```
### 


## MinIO Setup
To deploy MinIO with Docker Compose it is needed to:
1. Verify that Docker and Docker Compose are installed.
2. Populate the .env file with the MinIO root credentials and its API endpoint:
    - **ACCESS_KEY_ID**=*root-user*    
    - **SECRET_ACCESS_KEY**=*root-user-password* 
    - **S3_API_ENDPOINT**=*minio:9000*
    - **S3_CONSOLE_ENDPOINT**=*minio:9001*
    - **CHROMADB_ENDPOINT**=chromadb
    - **CHROMADB_PORT**=8000
    - **GEMINI_API_KEY**=*gemini-api-key*

    You can view an example of .env file [here](./env.example).
3. Run the following command from the same directory where the docker-compose.yaml file is located:
```docker compose up```

Once this is done, the GUI can be accessed via [http://localhost:9001](http://localhost:9001)

## Data Collecting
For this project, we have designed an script that automatically collects data for further uploading and processing. This program is documented [here](./notebooks/landing_zone/data-collection.ipynb). In particular, the script will create the following directory structure representing 3 different datasources:
- output/dataset1 
- output/dataset2
- output/dataset3

It is needed to have the data as presented before starting the data pipeline. The first step of the pipeline consists on traversing all the files and uploading them to the temporal landing zone (see the [notebook](./notebooks/landing_zone/temporal_zone.ipynb) for more information).

## Run Data pipeline
The intended way to execute this project is using Docker containers. The stack (MinIO + ChromaDB + Application code) can be deployed using docker compose by executing:
```bash
docker compose up -d
```
Also, to deploy only the data pipeline / application (assuming MinIO and ChromaDB are already running):
```bash
docker run --env-file=.env ghcr.io/carles-aguilera-pilo/adsdb:latest 
```
Currently, the pipeline ([pipeline.py](./pipeline.py)) code contains the data collection script to automatically be able to execute the project code easily from end to end.

