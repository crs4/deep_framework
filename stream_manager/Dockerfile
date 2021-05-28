# Use hyperpeer-py image as a parent image
# FROM 156.148.14.162/hyperpeer-py:latest

FROM python:3.7

RUN apt-get update --fix-missing
RUN apt-get install -y ffmpeg libavcodec-dev libavformat-dev libswscale-dev libxine2-dev mplayer
# RUN apt-get install gcc -y
# RUN apt-get install git-all -y


# Set the working directory to /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
ADD . /app
COPY --from=utils:deep_setup /home/deepframework/utils /app/utils

# Define environment variable
#ENV HP_SERVER 156.148.132.107:8080

# Run app.py when the container launches
CMD ["python", "/app/stream_manager.py"]
