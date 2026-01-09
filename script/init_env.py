import os
import re
import secrets


def init_env():
    if os.path.exists('.env'):
        print('已存在.env文件，无须初始化')
        return
    
    if not os.path.exists('.env.local'):
        print('未找到.env.local文件，初始化失败')
        return

    # 读取.env.local文件内容
    with open('.env.local', 'r', encoding='utf8') as f:
        env_local_content = f.read()

    # 创建一个.env文件，将ENV_NAME设置为prod
    env_local_content = env_local_content.replace('ENV_NAME = local', 'ENV_NAME = prod')
    # 生成32位随机API_KEY
    env_local_content = re.sub(
        r'API_KEY\s*=\s*.*',
        f'API_KEY={secrets.token_hex(32)}',
        env_local_content,
        flags=re.MULTILINE,
    )
    # 写入.env文件
    with open('.env', 'w', encoding='utf8') as f:
        f.write(env_local_content)

    # 初始化完成
    print('初始化完成，请修改.env文件')


if __name__ == '__main__':
    init_env()
