FROM python:3.13.3

WORKDIR /app

COPY requirements.txt .
COPY templates/ ./templates/
COPY stacic/ ./static/

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "main.py"]
