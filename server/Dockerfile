
FROM python:3.13.3

WORKDIR /app/server

# Instalar dependências do servidor
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar arquivos Python
COPY server/main.py server/database.py ./

# Copiar arquivos do dashboard
COPY dashboard/templates/ /app/dashboard/templates/
COPY dashboard/static/ /app/dashboard/static/

# Iniciar Flask e MQTT
CMD ["python", "-u", "main.py"]
