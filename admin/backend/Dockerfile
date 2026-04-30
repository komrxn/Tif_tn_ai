FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

COPY app/ ./app/

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
