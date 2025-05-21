FROM ubuntu:latest

RUN apt-get update -y && \
    apt-get install -y python3 python3-pip libgl1-mesa-dev libglib2.0-0 ffmpeg

WORKDIR /app/

COPY . /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy the rest of the application code to the working directory
VOLUME /app/Database
VOLUME /app/static
# Expose any necessary ports
EXPOSE 5000

# Define the command to run the application
CMD ["python3", "app.py"]
