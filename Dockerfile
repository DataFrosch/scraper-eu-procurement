FROM python:3.12-slim

RUN pip install uv

WORKDIR /app
COPY . .
RUN uv sync

CMD ["uv", "run", "awards", "run", "--portal", "ted"]
