# ADSDB
Project for the course *Algorithms, Data Structures and Databases* (ADSDB) of the Master's Degree in Data Science (MDS) taught at UPC.

## MinIO Setup
To deploy MinIO with Docker Compose it is needed to:
1. Verify that Docker and Docker Compose are installed.
2. Populate the .env file with the MinIO root credentials and its API endpoint:
    - **ACCESS_KEY_ID**=*root-user*    
    - **SECRET_ACCESS_KEY**=*root-user-password* 
    - **S3_API_ENDPOINT**=*127.0.0.1:9000*

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
After setting up MinIO and having collected all the data for our pipeline, run the data pipeline to upload it to MinIO and process it for further exploitation. The scripts involved in the process, which are based on the notebooks' code, can be found in [src](./src/) folder.

The data pipeline process can be run as a docker container:
```bash
docker run -v ./output:/usr/local/app/output --env-file=.env ghcr.io/carles-aguilera-pilo/adsdb:latest
```

