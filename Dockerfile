FROM python:3.11-slim

WORKDIR /app

COPY . .

ENV PORT=8000
ENV HOST=0.0.0.0
CMD ["python", "server/app.py"]
