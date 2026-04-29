FROM python:3.11-slim
WORKDIR /app
COPY python/pyproject.toml python/README.md ./
COPY python/convoagent ./convoagent
RUN pip install --no-cache-dir -e . && useradd -m -u 1001 ca
USER ca
EXPOSE 8000
ENTRYPOINT ["convoagent", "serve", "--host", "0.0.0.0"]
