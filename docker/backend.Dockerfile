FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
# 安装 agent 包（Agent Loop + RAG + Skill 系统），backend 直接 import storyclaw
COPY packages/storyclaw /app/storyclaw
RUN pip install --no-cache-dir -e /app/storyclaw
COPY backend /app/backend
COPY configs /app/configs
COPY skills /app/skills
WORKDIR /app/backend
ENV PYTHONPATH=/app/storyclaw_src:/app/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
