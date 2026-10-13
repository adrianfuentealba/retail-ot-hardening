FROM python:3.11-slim-bookworm
WORKDIR /lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app /lab/app
COPY plc /lab/plc
COPY gateway /lab/gateway
COPY collector /lab/collector
COPY elastic /lab/elastic
COPY docs /lab/docs
COPY exercises /lab/exercises
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "app.main"]
