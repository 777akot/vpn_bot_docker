FROM python:3.9-slim as builder
# Установка необходимых пакетов для компиляции

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     gcc gfortran libblas-dev liblapack-dev libatlas-base-dev \
#     libfreetype6-dev libpng-dev

COPY requirements.txt .
# RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt
# RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels numpy pandas
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Финальный этап
FROM python:3.9-slim

WORKDIR /usr/src/app/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=builder /app/wheels /usr/src/app/wheels
# COPY --from=builder /app/requirements.txt /usr/src/app

RUN pip install --no-cache /usr/src/app/wheels/*

# RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
COPY . /usr/src/app/