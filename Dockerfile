FROM python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE=/data/campus.db
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock && useradd --uid 10001 --create-home campus && mkdir /data && chown campus:campus /data
COPY app.py wsgi.py schema.sql ./
COPY templates ./templates
COPY static ./static
COPY scripts/bootstrap.py scripts/seed_demo.py ./scripts/
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')"
CMD ["gunicorn","--bind","0.0.0.0:8080","--workers","2","--threads","2","--worker-tmp-dir","/tmp","--access-logfile","-","--error-logfile","-","wsgi:application"]
