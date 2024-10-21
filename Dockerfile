FROM python:3.10.13-slim

# 更换源为 USTC，并更新 APT 包管理器
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get -y upgrade \
    && apt-get install -y --no-install-recommends \
        bash vim wget httpie netcat-openbsd htop curl gcc make g++ procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Shanghai

# 创建并设置工作目录
WORKDIR /var/www/ytb_login_by_automation

# 将项目的源代码复制到容器中
COPY . .

# 安装Python依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 指定默认命令来运行Python程序
CMD ["python3", "server.py"]
