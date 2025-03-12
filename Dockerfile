
FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_SYSTEM_PYTHON=1
WORKDIR /app
ADD . /app
RUN uv sync --frozen
RUN uv run playwright install  --with-deps
ENTRYPOINT [ "uv", "run", "main.py" ]
