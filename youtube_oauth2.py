import os
import time
import json
import shutil
import platform
import subprocess
from loguru import logger
from datetime import datetime
from selenium import webdriver
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# 自定义 ChromeDriver 路径和浏览器路径
# ChromeDriver 路径
CHROME_DRIVER_PATH = r"E:\chromedriver-win64\chromedriver.exe"
# Chrome 浏览器可执行文件路径
CHROME_BINARY_PATH = r"E:\chrome-win64\chrome.exe"

# selenium_ip = "seleniumSLC_debug"
selenium_ip = "seleniumSLC"

browser, wait = None, None

logger.add(f"./log/youtube_oauth2.log", rotation="1 days", retention="28 days", compression="zip")


def init():
    global browser
    global wait
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')

    # 设置浏览器可执行文件的路径
    options.binary_location = CHROME_BINARY_PATH

    # 使用 Service 指定 ChromeDriver 路径
    service = Service(executable_path=CHROME_DRIVER_PATH)

    # 启动 Chrome 浏览器
    browser = webdriver.Chrome(service=service, options=options)

    # 修改浏览器指纹
    browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    wait = WebDriverWait(browser, 30)  # 设置页面加载的最长等待时间


def init_net():
    global browser
    global wait
    host = f"http://{selenium_ip}:4444/wd/hub"
    broser = "chrome"
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用启用Blink运行时的功能
    options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 去除浏览器检测框
    options.add_argument('ignore-certificate-errors')

    # 设置自定义 User-Agent
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0")
    options.add_argument(f"user-agent={user_agent}")
    caps = {"browserName": broser, 'goog:loggingPrefs': {'performance': 'ALL'}}  # 开启日志性能监听

    # 将caps添加到options中
    for key, value in caps.items():
        options.set_capability(key, value)

    try:
        browser = Remote(command_executor=host, options=options)
        wait = WebDriverWait(browser, 30)
        # selenium/standalone-chrome-debug 不能用 'execute_cdp_cmd'
        # 会报错：AttributeError: 'WebDriver' object has no attribute 'execute_cdp_cmd'
        # browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        #     "source": """
        #                             Object.defineProperty(navigator, 'webdriver', {
        #                                 get: () => undefined
        #                             })
        #     """})
        logger.info(f"连接完成：{host}")
        return True
    except Exception as e:
        logger.error(f"链接错误：{e}")
        return False


def login(device_code: str, username: str, password: str, recovery_email: str):
    """
    通过设备标识码登录 Google 帐号

    :param device_code: code
    :param username: 用户名
    :param password: 密码
    """
    if platform.system() == "Linux":
        init_net()
    else:
        init()
    browser.get('https://accounts.google.com/o/oauth2/device/usercode?ddm=0&flowName=DeviceOAuth')

    try:
        # 标识码
        element = wait.until(EC.visibility_of_element_located((By.ID, "code")))
        logger.info(f"输入设备标识码:{device_code}")
        element.send_keys(device_code)

        button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#next > div > button")))
        logger.info("点击 `继续` 按钮")
        button_element.click()

        # 用户名
        element = wait.until(EC.visibility_of_element_located((By.ID, "identifierId")))
        logger.info(f"输入用户名:{username}")
        element.send_keys(username)
        # time.sleep(2)

        button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#identifierNext > div > button")))
        logger.info("点击 `下一步` 按钮")
        button_element.click()

        # 密码
        element = wait.until(EC.visibility_of_element_located((By.NAME, "Passwd")))
        logger.info(f"输入密码:{password}")
        element.send_keys(password)
        # time.sleep(2)

        button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#passwordNext > div > button")))
        logger.info("点击 `下一步` 按钮")
        button_element.click()
        logger.info("等待 5 秒后继续...")
        time.sleep(5)

        # 第一次登陆同意协议
        auto_agree_protocol(browser)

        # Opt: 辅助邮箱验证
        recovery_email_selector = ("#yDmH0d > c-wiz > div > div.UXFQgc > div > div > div > form > span > "
                                   "section:nth-child(2) > div > div > section > div > div > div > ul > li:nth-child("
                                   "3)")
        elements = browser.find_elements(By.CSS_SELECTOR, recovery_email_selector)
        if elements:
            logger.info("找到 `辅助邮箱验证` 元素, 需验证辅助邮箱")
            button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                                    "#yDmH0d > c-wiz > div > div.UXFQgc > div > div > "
                                                                    "div > form > span > section:nth-child(2) > div > "
                                                                    "div > section > div > div > div > ul > "
                                                                    "li:nth-child(3)")))
            logger.info("点击 `确认您的辅助邮箱` 按钮")
            button_element.click()

            element = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@type="email"]')))
            logger.info(f"输入辅助邮箱:{recovery_email}")
            element.send_keys(recovery_email)
            time.sleep(1)
            button_element = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#yDmH0d > c-wiz > div > div.JYXaTc.lUWEgd > div > div.TNTaPb > div > div > button")))
            logger.info("点击 `下一步` 按钮")
            button_element.click()
        else:
            logger.info("未找到相关元素，跳过 `辅助邮箱验证`")

        # 最终确认
        # Allow Selector    #submit_approve_access > div > button
        # Allow Xpath       //*[@id="submit_approve_access"]/div/button
        button_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#submit_approve_access > div > button')))
        # button_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit_approve_access"]/div/button')))
        logger.info("点击 `Allow` 按钮")
        button_element.click()
        time.sleep(5)

    except TimeoutException:
        logger.error("元素未在预期时间内出现，操作超时。")
        browser.save_screenshot('./data/screenshot_TimeoutException.png')
    except Exception as e:
        logger.error(f"处理元素时发生错误: {e}")
        browser.save_screenshot('./data/screenshot_Exception.png')
    else:
        logger.info(
            f"登录成功 | device_code: {device_code}, username: {username}, password: {password}, recovery_email: {recovery_email}")
    finally:
        time.sleep(3)
        logger.info("关闭浏览器")
        browser.quit()  # 关闭浏览器


# def get_ytb_account():
#     """
#     获取随机的 Google 帐号
#     """
#     from youtube_account import YTB_ACCOUNT_LIST
#     import random
#     username, password, recovery_email = random.choice(YTB_ACCOUNT_LIST)
#     return username, password, recovery_email


def auto_agree_protocol(browser):
    """
    If the browser is on the "Welcome to your new account" page,
    auto-pass the first login agreement.

    This function is used to handle the situation where the browser is
    on the "Welcome to your new account" page after logging in with a
    new account.

    It will click the "I understand" button to agree to the terms and
    conditions.

    :param browser: The Selenium WebDriver object.
    """
    elements = browser.find_elements(By.CSS_SELECTOR,
                                     "#yDmH0d > div.s2h6df > div.RgEUV.ZnXjYc.EaNIqc.JhUD8d > div.glT6eb > div > h1")
    if elements:
        logger.info("识别到 `Welcome to your new account`, 自动同意协议")
        button_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#confirm")))
        logger.info("点击 `I understand` 按钮")
        button_element.click()
        logger.info("通过 auto_pass_first_login 处理")
    else:
        logger.info("跳过 auto_pass_first_login 处理")


def run_command_and_get_code(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    code = None
    # 实时读取 stdout，获取code
    while True:
        output = process.stdout.readline()
        if output:
            logger.info(f"标准输出: {output.strip()}")
            # 查找 'and enter code' 后面的内容
            if 'and enter code' in output:
                parts = output.split('and enter code')
                if len(parts) > 1:
                    code = parts[1].strip()
                    break  # 一旦获取到code，退出循环

        # 检查进程是否已经结束
        if process.poll() is not None:
            break

    return process, code  # 返回process对象和获取到的code


def read_token_and_rename_move_folder(username):
    # 定义原始文件路径和目录路径
    token_file_path = './data/youtube-oauth2/token_data.json'
    source_directory = './data/youtube-oauth2'
    target_directory = './cache'

    # 检查 token_data.json 文件是否存在
    if os.path.exists(token_file_path):
        # 读取 token_data.json 文件内容
        with open(token_file_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)

        # 获取当前日期和时间，并格式化为 'YYYYMMDD_HHMMSS' 格式
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 将 youtube-oauth2 文件夹重命名为传入的 code + 日期时间戳
        new_directory_name = os.path.join('./data', f"{username}_{timestamp}")
        os.rename(source_directory, new_directory_name)

        # 确保目标目录 ./cache 存在，不存在则创建
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        # 将重命名后的文件夹移动到 ./cache 目录下
        shutil.move(new_directory_name, target_directory)

        # 返回读取到的 token 数据
        return token_data
    else:
        return None


def get_token(username, password, recovery_email)->dict:
    """
    自动化登陆Goolge设备验证码，获取token
    
    :param username: 账号
    :param password: 密码
    :param recovery_email: 验证邮箱
    :return: dict, the retrieved token.
    """
    if platform.system() == "Linux":
        get_token_linux(username, password, recovery_email)
    else:
        get_token_windows(username, password, recovery_email)


def get_token_linux(username, password, recovery_email):
    logger.info(f"get_token_linux > username: {username}, password: {password}, recovery_email: {recovery_email}")
    tmp_dir = os.path.join(os.getcwd(), "data")

    # 启动 yt-dlp 命令并获取 code
    # command = ("yt-dlp --username oauth2 --password '' --cache-dir /var/www/ytb_login_by_automation/data "
    command = (f"yt-dlp --username oauth2 --password '' --cache-dir {tmp_dir} "
               "https://www.youtube.com/watch?v=TImtNKeNk78")
    logger.info(f"get_token_linux > 执行命令 {command}")
    process, code = run_command_and_get_code(command)
    if not code:
        logger.info("get_token_linux > 生成设备验证码失败！")
        return None

    logger.info(f'get_token_linux > 提取到的设备验证码: {code}')
    # logger.info(f'请前往 https://www.google.com/device 使用设备验证码 {code} 完成登录')
    logger.info(f'get_token_linux > 设备验证码 {code} 获取完成，准备进入自动化登录流程')

    login(
        device_code=code,
        username=username,
        password=password,
        recovery_email=recovery_email
    )

    # yt-dlp 继续后台执行，等待它完成后再进行处理
    process.wait(timeout=30)  # 阻塞，直到 yt-dlp 进程完成
    logger.info('get_token_linux > yt-dlp 已完成操作')
    token_json = read_token_and_rename_move_folder(username)
    return token_json


def get_token_windows(username, password, recovery_email):
    logger.info(f"get_token_windows > username: {username}, password: {password}, recovery_email: {recovery_email}")
    tmp_dir = os.path.join(os.getcwd(), "data")

    # 启动 yt-dlp 命令并获取 code
    command = (f"yt-dlp --username oauth2 --password '' --cache-dir {tmp_dir} "
                "https://www.youtube.com/watch?v=TImtNKeNk78")
    logger.info(f"get_token_windows > 执行命令 {command}")
    process, code = run_command_and_get_code(command)
    if not code:
        logger.info("get_token_windows > 生成设备验证码失败！")
        return None

    logger.info(f'get_token_windows > 提取到的设备验证码: {code}')
    # logger.info(f'请前往 https://www.google.com/device 使用设备验证码 {code} 完成登录')
    logger.info(f'get_token_windows > 设备验证码 {code} 获取完成，准备进入自动化登录流程')

    # 执行登录逻辑
    login(
        device_code=code,
        username=username,
        password=password,
        recovery_email=recovery_email
    )

    # 使用 communicate 读取输出，防止卡住
    try:
        stdout, stderr = process.communicate(timeout=30)  # 读取 stdout 和 stderr，避免输出缓冲区卡住
        logger.info(f"get_token_windows > yt-dlp 标准输出: {stdout}")
        logger.info(f"get_token_windows > yt-dlp 标准错误: {stderr}")
        logger.info('get_token_windows > yt-dlp 已完成操作')
    except subprocess.TimeoutExpired:
        logger.error("get_token_windows > yt-dlp 命令超时未完成")
        process.kill()  # 强制终止进程
        stdout, stderr = process.communicate()  # 确保可以获取终止前的输出
        logger.error(f"get_token_windows > yt-dlp 超时后的输出: {stdout}")
        return None

    # 获取 token 并返回
    token_json = read_token_and_rename_move_folder(username)
    return token_json


if __name__ == '__main__':
    username = "jennabernal27@gmail.com"
    password = "my31t2sxsb61"
    recovery_email = "q7t19gsqh214@aol.com"
    logger.info(f"获取到的token为：{get_token(username, password, recovery_email)}")
