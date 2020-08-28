# Use hyperpeer-py image as a parent image
FROM 156.148.14.162/hyperpeer-py:latest


# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY stream_capture.py /app/stream_capture.py

RUN mkdir /mnt/remote_media

# Install any needed packages specified in requirements.txt
#RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Define environment variable
#ENV HP_SERVER 156.148.132.107:8080
#192.168.0.182:8080
#192.168.0.181:8080
#156.148.33.62:8080
#hyperpeer-demo-v0.eu-central-1.elasticbeanstalk.com
#192.168.1.12 
#156.148.132.107

# Run app.py when the container launches
CMD ["python", "/app/stream_capture.py"]
