# Dockerfile is a script that contains instructions on how to build a docker image for the app. In other words, it defines the env and dependencies needed to run the app in a container.
# is this file just an image? No, it's a set of instructions to build an image. The image is the result of running the instructions in the Dockerfile, and it contains everything needed to run the app, including the code, dependencies, and environment.
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app


COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--app-dir", "/app"]