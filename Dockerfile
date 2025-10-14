FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py data_processing.py layout.py styles.py utils.py ./
COPY assets/ ./assets/

EXPOSE 8050

CMD ["python", "app.py"]
