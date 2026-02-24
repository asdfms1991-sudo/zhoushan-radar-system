# 舟山定海渔港雷达监控系统

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建日志和数据目录
RUN mkdir -p logs data data/trajectories

# 暴露端口
EXPOSE 8081

# 启动命令
CMD ["python", "main.py", "--simulator"]
