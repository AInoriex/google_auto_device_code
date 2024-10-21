import os
import uvicorn
import platform
from loguru import logger
from youtube_oauth2 import get_token
from fastapi import FastAPI, HTTPException, Request
from pprint import pprint

# 任务锁存储路径
flag_file_path = './data/is_get_token.flag'

app = FastAPI()
logger.add(f"./log/server.log", rotation="1 days", retention="28 days", compression="zip")

@app.post("/get_token")
async def get_token_route(request: Request):
    # 定义 flag 文件路径
    try:
        # 检查是否存在 is_get_token.flag 文件
        if os.path.exists(flag_file_path):
            logger.info("get_token_route > 上一轮获取token的操作尚未结束。")
            logger.info("=========================================================================================")
            return {"code": -1, "msg": "上一轮获取token的操作尚未结束。"}

        # 创建 is_get_token.flag 文件，作为锁
        with open(flag_file_path, 'w') as flag_file:
            flag_file.write("lock")  # 写入一些内容以确保文件存在

        data_all = await request.json()
        # 解析数据：
        username = data_all.get("username", "")
        password = data_all.get("password", "")
        recovery_email = data_all.get("recovery_email", "")

        if username and password and recovery_email:
            token = get_token(username, password, recovery_email)
            if token == None:
                raise ValueError("获取token为空")
            logger.info(f"get_token_route > 获取的数据: {data_all}, 返回的token：")
            pprint(token)
            logger.info("=========================================================================================")

            # 获取成功后，删除 flag 文件
            os.remove(flag_file_path)
            return {"code": 200, "msg": "自动登陆成功", "token": token}
        else:
            logger.info(f"get_token_route > 存在无效的参数 username:{username} password:{password} recovery_email:{recovery_email}")
            logger.info("=========================================================================================")
            os.remove(flag_file_path)  # 确保在异常情况下也能删除 flag 文件
            return {"code": -1, "msg": "缺少邮箱/用户名或密码、验证邮箱"}
    except Exception as e:
        # 日志记录
        logger.error(f"get_token_route > {e}")
        logger.info("=========================================================================================")
        if os.path.exists(flag_file_path):
            os.remove(flag_file_path)  # 在出现异常时删除 flag 文件
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # 清理历史任务锁
    if os.path.exists(flag_file_path):
            os.remove(flag_file_path)

    # uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host=os.getenv("host"), port=os.getenv("port"))

