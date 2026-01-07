FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 设置工作目录
WORKDIR /app

# 复制requirements.txt文件
COPY requirements.txt /app/requirements.txt
# 安装依赖
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 复制app目录
COPY ./app /app/app

# 暴露端口
EXPOSE 10024
# 使用 fastapi CLI 以单进程模式启动应用
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "10024"]
