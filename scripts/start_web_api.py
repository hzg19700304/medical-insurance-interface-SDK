#!/usr/bin/env python3
"""
启动医保SDK Web API服务
"""

import sys
import os
from pathlib import Path
import uvicorn

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_web_api():
    """启动Web API服务"""
    print("🚀 启动医保SDK Web API服务...")
    print("📍 服务地址: http://localhost:8080")
    print("📖 API文档: http://localhost:8080/docs")
    print("🔍 健康检查: http://localhost:8080/health")
    
    try:
        uvicorn.run(
            "medical_insurance_sdk.api.web_service:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")

if __name__ == "__main__":
    start_web_api()