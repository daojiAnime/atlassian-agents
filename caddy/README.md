# Caddy 反向代理配置

## 概述

使用 Caddy 作为轻量级、高性能的反向代理，统一处理前端（Next.js）和后端（FastAPI）的请求转发。

## 特点

- ✅ **轻量级**：Docker 镜像仅 ~15MB（vs Nginx ~140MB）
- ✅ **高性能**：Go 编写，低延迟，内存占用极低
- ✅ **零配置 HTTPS**：自动申请和续期 Let's Encrypt 证书
- ✅ **简单配置**：Caddyfile 语法直观易懂
- ✅ **自动压缩**：内置 gzip/zstd 压缩
- ✅ **健康检查**：自动监控后端服务状态
- ✅ **WebSocket**：原生支持 WebSocket 连接

## 架构

```
客户端请求
    ↓
Caddy (80/443)
    ├─→ /api/*              → Backend (FastAPI:8000)
    ├─→ /project-push-origin → Backend (FastAPI:8000)
    ├─→ /files/*            → Backend (FastAPI:8000)
    ├─→ /healthy            → Backend (FastAPI:8000)
    └─→ /*                  → Frontend (Next.js:3000)
```

## 路由规则

| 路径                   | 目标          | 说明           |
| ---------------------- | ------------- | -------------- |
| `/api/*`               | Backend:8000  | 所有 API 请求  |
| `/project-push-origin` | Backend:8000  | 项目推送接口   |
| `/files/*`             | Backend:8000  | 文件访问接口   |
| `/healthy`             | Backend:8000  | 健康检查       |
| `/health`              | Caddy         | Caddy 健康检查 |
| `/*`                   | Frontend:3000 | 前端页面       |

## 配置说明

### Caddyfile 主要配置

```caddyfile
:80 {
    # API 路由转发
    handle /api/* {
        reverse_proxy backend:8000 {
            # 保持原始请求头
            header_up Host {host}
            header_up X-Real-IP {remote_host}

            # 健康检查
            health_uri /healthy
            health_interval 30s
        }
    }

    # 前端路由转发
    handle /* {
        reverse_proxy frontend:3000
    }

    # 启用压缩
    encode gzip zstd
}
```

## 日志

Caddy 日志输出到 stdout，格式为 JSON：

```json
{
  "level": "info",
  "ts": "2025-01-08T10:00:00.000Z",
  "msg": "handled request",
  "request": {
    "method": "POST",
    "uri": "/api/project-push-origin",
    "proto": "HTTP/1.1"
  },
  "status": 200,
  "duration": 0.123
}
```

查看日志：

```bash
docker logs agentic-rag-caddy -f
```

## 性能优化

Caddy 已经内置了以下优化：

1. **HTTP/2 支持**：自动启用
2. **HTTP/3 (QUIC)**：自动启用（端口 443/udp）
3. **连接复用**：Keep-Alive 连接池
4. **响应压缩**：gzip/zstd 自动压缩
5. **健康检查**：自动检测后端状态

## 生产环境配置

### 启用 HTTPS

1. 在 Caddyfile 中取消注释 HTTPS 配置
2. 修改域名：

```caddyfile
yourdomain.com {
    handle /api/* {
        reverse_proxy backend:8000
    }

    handle /* {
        reverse_proxy frontend:3000
    }

    encode gzip zstd
}
```

3. Caddy 会自动：
   - 申请 Let's Encrypt 证书
   - 配置 HTTPS
   - 设置自动续期
   - 重定向 HTTP → HTTPS

### 自定义配置

如需修改配置，编辑 `caddy/Caddyfile` 后重启：

```bash
docker-compose -f docker-compose.caddy.yml restart caddy
```

## 监控

### 健康检查

```bash
# Caddy 自身健康检查
curl http://localhost/health

# 后端健康检查
curl http://localhost/healthy

# 查看 Caddy 状态
docker ps | grep caddy
```

### 性能指标

```bash
# 查看资源使用
docker stats agentic-rag-caddy

# 查看连接数
docker exec agentic-rag-caddy netstat -an | grep ESTABLISHED | wc -l
```

## 故障排查

### 1. Caddy 无法启动

```bash
# 检查配置语法
docker run --rm -v $(pwd)/caddy/Caddyfile:/etc/caddy/Caddyfile caddy:2-alpine caddy validate

# 查看详细错误
docker logs agentic-rag-caddy
```

### 2. 后端连接失败

```bash
# 检查后端是否运行
docker ps | grep backend

# 测试后端连接
docker exec agentic-rag-caddy wget -O- http://backend:8000/healthy
```

### 3. 前端连接失败

```bash
# 检查前端是否运行
docker ps | grep frontend

# 测试前端连接
docker exec agentic-rag-caddy wget -O- http://frontend:3000
```

## 对比 Nginx

| 特性       | Caddy | Nginx  |
| ---------- | ----- | ------ |
| 镜像大小   | ~15MB | ~140MB |
| 内存占用   | ~10MB | ~50MB  |
| HTTPS 配置 | 自动  | 手动   |
| 配置复杂度 | 极简  | 中等   |
| 性能       | 优秀  | 优秀   |
| 学习曲线   | 平缓  | 陡峭   |

## 更多资源

- [Caddy 官方文档](https://caddyserver.com/docs/)
- [Caddyfile 语法](https://caddyserver.com/docs/caddyfile)
- [反向代理指南](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
