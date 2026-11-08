# dentex_week3 inference service. Build context: dentex_week3/ (see docker-compose.yml).
# The pipeline code is copied unmodified; the model weights (*.pt) are NOT in git:
# place them in dentex_week3/production/ before building (see notebooks/fetch_weights.sh).
FROM python:3.11-slim

# OpenCV (pulled in by ultralytics) needs these shared libraries.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/dentex
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY production/ production/
COPY api/app.py api/app.py
RUN mkdir -p feedback

WORKDIR /srv/dentex/api
EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
