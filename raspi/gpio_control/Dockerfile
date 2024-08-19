# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

RUN apt update && apt install -y gcc make 
# Copy the current directory contents into the container at /app
COPY requirements.txt .


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install -y wget unzip

RUN wget https://github.com/joan2937/pigpio/archive/master.zip && \
    unzip master.zip && \
    cd pigpio-master && \
    make && \
    make install

COPY . .

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME World
ENV PYTHONPATH /app

# Install watchdog for file monitoring
RUN pip install watchdog

# Copy the start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Set the entry point to the start script
ENTRYPOINT ["/app/start.sh"]