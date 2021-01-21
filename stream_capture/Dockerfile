# Use hyperpeer-py image as a parent image
# FROM 156.148.14.162/hyperpeer-py:latest
FROM python:3.7


# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY stream_capture.py /app/stream_capture.py

RUN mkdir /mnt/remote_media

# Run app.py when the container launches
CMD ["python", "/app/stream_capture.py"]
