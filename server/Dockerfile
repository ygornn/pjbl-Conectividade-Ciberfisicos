
FROM python:3.13.3

WORKDIR /app/server

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/main.py server/database.py ./

COPY dashboard/templates/ /app/dashboard/templates/
COPY dashboard/static/ /app/dashboard/static/

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data

USER appuser

# Iniciar Flask e MQTT
CMD ["python", "-u", "main.py"]
