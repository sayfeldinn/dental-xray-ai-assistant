# dentex_week3 inference service. Build context: dentex_week3/ (see docker-compose.yml).
# The pipeline code is copied unmodified; the model weights (*.pt) are NOT in git:
# place them in dentex_week3/production/ before building (see notebooks/fetch_weights.sh).
FROM python:3.11-slim

# OpenCV (pulled in by ultralytics) needs these shared libraries.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/dentex
# CPU-only torch first: the default Linux wheel bundles CUDA (several GB) that this
# container never uses. Versions match the build that reproduced the locked benchmark.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.14.1 torchvision==0.29.1
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY production/ production/
COPY api/app.py api/app.py
RUN mkdir -p feedback

WORKDIR /srv/dentex/api
EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
