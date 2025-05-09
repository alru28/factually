FROM python:3.10-slim


RUN apt-get update && \
    apt-get install -y wget gnupg2 unzip curl chromium chromium-driver locales && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i '/en_US.UTF-8/s/^# //' /etc/locale.gen && \
    sed -i '/es_ES.UTF-8/s/^# //' /etc/locale.gen && \
    locale-gen

ENV LANG=es_ES.UTF-8
ENV LC_ALL=es_ES.UTF-8
ENV LC_TIME=es_ES.UTF-8

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OTEL_PYTHON_LOG_CORRELATION=true

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
