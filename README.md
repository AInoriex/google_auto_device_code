# 谷歌自动登陆设备验证码

​	该项目是用于登陆谷歌设备验证码的自动化脚本，并搭建Web服务提供获取账号Bearer Token能力，用于 [AInoriex/crawler_youtube_downloader](https://github.com/AInoriex/crawler_youtube_downloader) 项目使用。



## 相关框架

1. yt-dlp（最终服务框架）
2. yt-dlp-youtube-oauth2（验证设备验证码）
3. selenium（登陆界面操作）
4. fastapi（路由服务）



## Deploy

### Linux Docker部署：
```
# 拉取 selenium/standalone-chrome 镜像
# 不能用 docker pull selenium/standalone-chrome-debug，过不了
docker pull selenium/standalone-chrome

# 创建项目镜像
docker build -t youtube_login ./ytb_login_by_automation

# 创建日志映射目录
mkdir -p /home/www/ytb_login_by_automation/data

# 创建网络
docker network create dy_game_network

# 拉起 selenium 容器
# docker run -d --network=dy_game_network -p 4444:4444 -p 5900:5900 --shm-size 2g --name seleniumSLC_debug selenium/standalone-chrome-debug
docker run -d --network=dy_game_network -p 4444:4444 --shm-size 2g --name seleniumSLC selenium/standalone-chrome

# 拉起项目容器
docker run -d --network=dy_game_network \
    -v /home/www/ytb_login_by_automation/data:/var/www/ytb_login_by_automation/data \
    -v /home/www/ytb_login_by_automation/log:/var/www/ytb_login_by_automation/log \
    -v /home/www/ytb_login_by_automation/cache:/var/www/ytb_login_by_automation/cache \
    -p 32120:8000 --name ytb_login youtube_login
```

### windows 直接部署：
```
# 在合适的目录创建虚拟环境
python -m venv .venv

# 进入目录，激活虚拟环境
./.venv/Scripts/activate

# 进入项目目录，安装依赖：
pip install --no-cache-dir -r requirements.txt

# 进入项目目录，启动服务：
python server.py
```



