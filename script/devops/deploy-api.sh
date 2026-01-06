#!/bin/bash
# 更新api。从本地构建镜像，上传到服务器，重启服务。

# 遇到错误立即退出
set -e

# 获取当前路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 加载配置文件
source server.conf

# 删除本地旧镜像（允许失败，因为可能不存在）
docker rmi fastapi_demo:latest 2>/dev/null || true
echo "🗑️ 本地旧镜像已删除"

# 构建镜像
cd ../../
echo "开始构建镜像..."
if ! docker compose build; then
    echo "❌ 构建失败！部署已终止。"
    exit 1
fi
echo "✅ 构建镜像完成"

# 保存镜像
rm -rf fastapi_demo_image.tar
docker save -o fastapi_demo_image.tar fastapi_demo
echo "镜像已保存为 fastapi_demo_image.tar"

# 上传到服务器的 /data/docker_image 目录
echo "正在上传 fastapi_demo_image 到服务器..."
scp fastapi_demo_image.tar root@$SERVER_IP:/data/docker_image
rm -rf fastapi_demo_image.tar

# 连接到服务器
ssh root@$SERVER_IP << 'EOF'

# 检查新镜像文件是否存在
if [ ! -f /data/docker_image/fastapi_demo_image.tar ]; then
    echo "❌ 错误：fastapi_demo_image.tar 文件不存在！"
    exit 1
fi
echo "✅ 新镜像文件已确认存在"

# 备份旧镜像
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if docker image inspect fastapi_demo:latest >/dev/null 2>&1; then
    docker tag fastapi_demo:latest fastapi_demo:backup_$TIMESTAMP
    echo "✅ 旧镜像已备份为 fastapi_demo:backup_$TIMESTAMP"
    HAS_BACKUP=true
else
    echo "ℹ️ 未发现旧镜像，跳过备份"
    HAS_BACKUP=false
fi

# 停止api服务
cd /data/bin/api
docker compose down
echo "api 已停止"

# 删除旧镜像的 latest 标签
if docker image inspect fastapi_demo:latest >/dev/null 2>&1; then
    docker rmi fastapi_demo:latest
    echo "旧镜像 latest 标签已删除"
fi

# 加载新镜像
cd /data/docker_image
docker load -i fastapi_demo_image.tar
echo "✅ 新镜像加载完成"

# 启动新服务
cd /data/bin
sh fastapi-demo-start.sh

# 删除压缩文件
rm -rf /data/docker_image/fastapi_demo_image.tar

# 等待服务启动并检查状态
echo "等待服务启动..."
sleep 5

# 检查服务是否正常运行
cd /data/bin/fast
if docker compose ps | grep -q "Up"; then
    echo "✅ 新服务已成功启动"
    
    # 删除备份的旧镜像
    OLD_IMAGES=$(docker images | grep "fastapi_demo" | grep "backup_" | awk '{print $1":"$2}')
    if [ -n "$OLD_IMAGES" ]; then
        echo "清理备份镜像..."
        echo "$OLD_IMAGES" | xargs -r docker rmi
        echo "✅ 旧镜像已清理"
    fi
else
    echo "⚠️ 警告：服务可能未正常启动，请手动检查"
    if [ "$HAS_BACKUP" = "true" ]; then
        echo "备份镜像已保留，可以使用以下命令回滚："
        echo "docker rmi fastapi_demo:latest && docker tag fastapi_demo:backup_$TIMESTAMP fastapi_demo:latest && cd /data/bin && sh fast-start.sh"
    else
        echo "无旧镜像备份，无法自动回滚"
    fi
fi

# 退出服务器
exit
EOF

echo "友单API已经更新！"
