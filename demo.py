import subprocess
import time

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    code_match = None

    # 实时读取 stdout 和 stderr
    while True:
        output = process.stdout.readline()
        if output:
            # print(f"标准输出: {output.strip()}")
            if 'and enter code' in output:
                parts = output.split('and enter code')
                if len(parts) > 1:
                    code_match = parts[1].strip()

        error = process.stderr.readline()
        # if error:
        #     print(f"标准错误: {error.strip()}")

        if process.poll() is not None:
            break

    remaining_output, remaining_error = process.communicate()
    if remaining_output:
        # print(f"标准输出(剩余): {remaining_output.strip()}")
        if 'and enter code' in remaining_output:
            parts = remaining_output.split('and enter code')
            if len(parts) > 1:
                code_match = parts[1].strip()

    # if remaining_error:
    #     print(f"标准错误(剩余): {remaining_error.strip()}")

    return code_match

if __name__ == '__main__':
    time1 = time.time()
    command = "yt-dlp --username oauth2 --password '' --cache-dir /var/www/cache https://www.youtube.com/watch?v=TImtNKeNk78"
    code = run_command(command)
    if code:
        print(f'提取到的代码: {code}')
    else:
        print('未找到代码')
    print(f'使用时长：{time.time() - time1} s')

