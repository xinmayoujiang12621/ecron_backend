# 使用Python 3.12作为基础镜像
FROM python:3.12

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=ecron_backend.settings
ENV LOG_LEVEL=INFO
ENV PYTHONPATH=/app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN cd /app

# 暴露端口
EXPOSE 20130

# 启动命令
CMD ["gunicorn", "ecron_backend.wsgi:application", "--bind", "0.0.0.0:20130", "--workers", "4", "--timeout", "120"]