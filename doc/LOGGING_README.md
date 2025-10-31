# 日志系统说明

## 日志框架
本项目使用 [loguru](https://github.com/Delgan/loguru) 作为日志框架，它提供了简洁且功能强大的日志记录功能。

## 日志级别控制

### 默认日志级别
项目默认日志级别为 `INFO`，这意味着只会显示 `INFO` 级别及以上的日志消息（INFO, WARNING, ERROR, CRITICAL）。

### 通过环境变量调整日志级别
可以通过设置环境变量 `LOGURU_LEVEL` 来动态调整日志级别：

```bash
# Windows (PowerShell)
$env:LOGURU_LEVEL = "DEBUG"
python app/main.py

# Linux/Mac
export LOGURU_LEVEL=DEBUG
python app/main.py
```

支持的日志级别（按严重程度递增）：
- `TRACE` (5)
- `DEBUG` (10)
- `INFO` (20)
- `SUCCESS` (25)
- `WARNING` (30)
- `ERROR` (40)
- `CRITICAL` (50)

### 示例
```bash
# 只显示错误信息
export LOGURU_LEVEL=ERROR
python app/main.py

# 显示所有调试信息
export LOGURU_LEVEL=DEBUG
python app/main.py
```

## 日志格式
日志输出格式为：
```
<时间> | <级别> | <trace_id> | <消息>
```

其中 `trace_id` 是 OpenTelemetry 的追踪ID，用于分布式追踪。

## 代码实现
日志初始化在 `app/internal/log/logger.py` 文件中的 `init_logger()` 函数中实现。该函数会在项目启动时被 `app/main.py` 调用。

```python
def init_logger():
    # 从环境变量获取日志级别，默认为INFO
    log_level = os.getenv("LOGURU_LEVEL", "INFO")
    
    # 配置日志处理器
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time}</green> | <level>{level}</level> | <cyan>{extra[trace_id]}</cyan> | {message}",
        filter=TraceIdFilter(),
    )
```