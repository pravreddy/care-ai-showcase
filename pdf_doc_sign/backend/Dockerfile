FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libmagic1 ghostscript \
    libreoffice-writer libreoffice-calc libreoffice-impress \
    libreoffice-core fonts-liberation fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# LibreOffice needs a home dir for temp files
ENV HOME=/tmp

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
