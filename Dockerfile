FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY guard ./guard
COPY generator ./generator
RUN pip install --no-cache-dir -e . && useradd -m guard && mkdir -p /app/data && chown -R guard /app
USER guard
ENTRYPOINT ["guard"]
CMD ["--help"]
