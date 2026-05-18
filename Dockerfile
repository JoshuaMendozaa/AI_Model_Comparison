FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app


COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--app-dir", "/app"]