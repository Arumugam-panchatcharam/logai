FROM python:3.11-slim
MAINTAINER p.arumugam@telekom-digital.com

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/app"]
#COPY . .

EXPOSE 40601

# Gunicorn: 4 workers, binds to 0.0.0.0:40601
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:40601", "logai_wsgi:server"]