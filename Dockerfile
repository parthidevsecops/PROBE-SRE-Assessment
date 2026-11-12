# Stage 1: build the DigiCon_UI React app. Needs network access to npm's
# registry, which this stage has when you run `docker compose up --build`
# on your machine (unlike the sandbox this Dockerfile was written in).
#
# Pinned to node:16 (not 18, despite DigiCon_UI/.nvmrc saying 18.17.1):
# react-scripts 3.4.3 bundles webpack 4, whose createHash() call breaks
# under Node 17+'s default OpenSSL 3 provider (ERR_OSSL_EVP_UNSUPPORTED —
# a removed legacy digest, not a real crypto issue). Node 16 still ships
# OpenSSL 1.1.1 and doesn't hit this, and doesn't understand/need the
# --openssl-legacy-provider flag that fixes it on 17+ (that flag fails
# outright on Node 16, so do not add it here while pinned to 16).
FROM node:16-bullseye AS ui-builder
WORKDIR /ui
COPY Probe2026UI/package.json Probe2026UI/package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY Probe2026UI/ ./
RUN npm run build

# Stage 2: the Python app, serving the built UI as static files.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 INPUT_PATH=/app/input CHROMA_PATH=/app/chroma_db GRAPH_PATH=/app/graph_db/probe_graph.json INGEST_STATUS_FILE=/app/data/ingest_status.json
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements_rag.txt /app/requirements_rag.txt
# Install the CPU-only torch wheel FIRST, from PyTorch's own CPU index.
# sentence-transformers (in requirements_rag.txt) depends on torch, and
# pip's default PyPI wheel for Linux assumes a GPU and drags in the full
# NVIDIA CUDA toolkit (cusparse/cufft/cublas/cusolver/cudnn, several GB)
# even though this container has no GPU and never will. Satisfying the
# torch dependency here, before the main install, means pip sees it's
# already met and never touches the CUDA packages at all.
RUN pip install --upgrade pip && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r /app/requirements_rag.txt
COPY . /app
COPY --from=ui-builder /ui/build /app/Probe2026UI/build
RUN mkdir -p /app/input /app/data /app/chroma_db /app/graph_db && chmod +x /app/docker-entrypoint.sh
EXPOSE 8501
ENTRYPOINT ["/app/docker-entrypoint.sh"]
