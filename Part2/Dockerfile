FROM python:3.10
WORKDIR /usr/local/app

# Install the application dependencies
COPY requirements.txt ./
RUN cat requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 
RUN python3 -m piper.download_voices en_US-lessac-medium
RUN apt update && apt -y install git ffmpeg libavcodec-extra 
# RUN git clone https://github.com/facebookresearch/ImageBind.git && pip install -r ImageBind/requirements.txt && mv ImageBind/imagebind imagebind && rm -rf ImageBind

# Copy in the source code
COPY src/ ./src

COPY app.py pipeline.py .

EXPOSE 8501

# Execute the orchestration script
CMD ["full"]
ENTRYPOINT ["python3", "app.py"]
