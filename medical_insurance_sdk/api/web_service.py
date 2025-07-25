"""
医保SDK Web API服务
为C#桌面程序提供HTTP接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import uvicorn

from ..client import MedicalInsuranceClient
from ..exceptions import MedicalInsuranceException

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="医保接口SDK Web API",
    description="为桌面应用提供医保接口调用服务",
    version="1.0.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局客户端实例
medical_client = None

# 请求模型
class InterfaceCallRequest(BaseModel):
    api_code: str = Field(alias="apiCode")
    data: Dict[str, Any]
    org_code: str = Field(alias="orgCode")
    
    class Config:
        allow_population_by_field_name = True

class BatchCallRequest(BaseModel):
    requests: List[InterfaceCallRequest]

class AsyncCallRequest(BaseModel):
    api_code: str = Field(alias="apiCode")
    data: Dict[str, Any]
    org_code: str = Field(alias="orgCode")
    use_celery: bool = Field(default=True, alias="useCelery")
    
    class Config:
        allow_population_by_field_name = True

# 响应模型
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化客户端"""
    global medical_client
    try:
        medical_client = MedicalInsuranceClient()
        logger.info("医保SDK客户端初始化成功")
    except Exception as e:
        logger.error(f"医保SDK客户端初始化失败: {e}")
        raise

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "医保接口SDK Web API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "medical-insurance-sdk-api",
        "client_ready": medical_client is not None
    }

@app.post("/api/call", response_model=ApiResponse)
async def call_interface(request: InterfaceCallRequest):
    """调用医保接口"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        result = medical_client.call(
            api_code=request.api_code,
            data=request.data,
            org_code=request.org_code
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="接口调用成功"
        )
        
    except MedicalInsuranceException as e:
        logger.error(f"医保接口调用失败: {e}")
        return ApiResponse(
            success=False,
            error=str(e),
            message="医保接口调用失败"
        )
    except Exception as e:
        logger.error(f"系统错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/call/async", response_model=ApiResponse)
async def call_interface_async(request: AsyncCallRequest):
    """异步调用医保接口"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        task_id = medical_client.call_async(
            api_code=request.api_code,
            data=request.data,
            org_code=request.org_code,
            use_celery=request.use_celery
        )
        
        return ApiResponse(
            success=True,
            data={"task_id": task_id},
            message="异步任务提交成功"
        )
        
    except Exception as e:
        logger.error(f"异步调用失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}", response_model=ApiResponse)
async def get_task_result(task_id: str):
    """获取异步任务结果"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        result = medical_client.get_task_result(task_id)
        
        return ApiResponse(
            success=True,
            data=result,
            message="任务结果获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/call/batch", response_model=ApiResponse)
async def call_batch(request: BatchCallRequest):
    """批量调用医保接口"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        # 转换请求格式
        batch_requests = [
            {
                "api_code": req.api_code,
                "data": req.data,
                "org_code": req.org_code
            }
            for req in request.requests
        ]
        
        results = medical_client.call_batch(batch_requests)
        
        return ApiResponse(
            success=True,
            data={"results": results},
            message="批量调用成功"
        )
        
    except Exception as e:
        logger.error(f"批量调用失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interfaces", response_model=ApiResponse)
async def get_supported_interfaces(org_code: Optional[str] = None):
    """获取支持的接口列表"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        interfaces = medical_client.get_supported_interfaces(org_code)
        
        return ApiResponse(
            success=True,
            data={"interfaces": interfaces},
            message="接口列表获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取接口列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interface/{api_code}", response_model=ApiResponse)
async def get_interface_info(api_code: str, org_code: Optional[str] = None):
    """获取接口详细信息"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        info = medical_client.get_interface_info(api_code, org_code)
        
        return ApiResponse(
            success=True,
            data=info,
            message="接口信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取接口信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/validate", response_model=ApiResponse)
async def validate_data(request: InterfaceCallRequest):
    """验证接口数据"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        result = medical_client.validate_data(
            api_code=request.api_code,
            data=request.data,
            org_code=request.org_code
        )
        
        return ApiResponse(
            success=True,
            data=result,
            message="数据验证完成"
        )
        
    except Exception as e:
        logger.error(f"数据验证失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=ApiResponse)
async def get_stats():
    """获取统计信息"""
    try:
        if not medical_client:
            raise HTTPException(status_code=500, detail="医保客户端未初始化")
        
        stats = medical_client.get_processing_stats()
        
        return ApiResponse(
            success=True,
            data=stats,
            message="统计信息获取成功"
        )
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "medical_insurance_sdk.api.web_service:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )