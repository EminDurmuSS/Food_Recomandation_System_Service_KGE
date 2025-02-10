FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY .python-version pyproject.toml uv.lock ./

RUN uv sync

COPY ./backend ./data ./embedding ./

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000