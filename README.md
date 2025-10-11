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
