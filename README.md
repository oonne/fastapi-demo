# fastapi-demo
FastApi DEMO

## 功能
* 自动部署脚本
* Swagger UI
* 输出日志

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

4. 运行
```bash
fastapi dev app/main.py --port 10024
```

5、访问文档
[Swagger UI](http://127.0.0.1:10024/docs)

## 开发

### 导出依赖列表（安装新包后记得更新）：
```bash
pip freeze > requirements.txt
```
