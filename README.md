# fastapi-demo
FastApi DEMO

## 功能
* Swagger UI
* 输出日志
* 格式化返回
* API Key 认证
* 请求外部接口
* 自动部署脚本

## 使用

1. 创建虚拟环境：
```bash
python3 -m venv .venv
```

2. 激活虚拟环境：
```bash
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 初始化环境变量：
```bash
python3 script/init_env.py
```

5. 运行
```bash
fastapi dev app/main.py --port 10024
```

6. 访问文档
[Swagger UI](http://127.0.0.1:10024/docs)

## 开发

### 导出依赖列表（安装新包后记得更新）：
```bash
pip freeze > requirements.txt
```
