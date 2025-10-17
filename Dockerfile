FROM python:3.10
WORKDIR /usr/local/app

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy in the source code
COPY src/ ./

# Execute the orchestration script
CMD ["python", "test.py"]