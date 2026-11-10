# python-svc 镜像：默认启动情感分析服务（8001）
# 构建（在 python-svc 目录）：docker build -t sentiment-python-svc .
# 运行：docker run --rm -p 8001:8001 --env-file .env sentiment-python-svc
#
# 也可覆盖 CMD 启动其它两个服务：
#   docker run --rm -p 8002:8002 sentiment-python-svc python news_feed_service.py
#   docker run --rm -p 8003:8003 sentiment-python-svc python report_gen.py
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "app.py"]
