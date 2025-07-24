"""医保接口响应模型"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MedicalInsuranceResponse:
    """医保接口标准响应格式"""

    infcode: int = 0  # 交易状态码：0-成功，-1-失败
    inf_refmsgid: str = ""  # 接收方报文ID(30位)
    refmsg_time: str = ""  # 接收报文时间(17位)
    respond_time: str = ""  # 响应报文时间(17位)
    err_msg: str = ""  # 错误信息(200位)
    output: Dict[str, Any] = None  # 交易输出(40000位)
    warn_msg: str = ""  # 警告信息
    cainfo: str = ""  # CA信息
    signtype: str = ""  # 签名类型
    parsed_data: Dict[str, Any] = None  # 解析后的数据

    def __post_init__(self):
        """初始化后处理"""
        if self.output is None:
            self.output = {}
        if self.parsed_data is None:
            self.parsed_data = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MedicalInsuranceResponse":
        """从字典创建响应对象"""
        return cls(
            infcode=data.get("infcode", -1),
            inf_refmsgid=data.get("inf_refmsgid", ""),
            refmsg_time=data.get("refmsg_time", ""),
            respond_time=data.get("respond_time", ""),
            err_msg=data.get("err_msg", ""),
            output=data.get("output", {}),
            warn_msg=data.get("warn_msg", ""),
            cainfo=data.get("cainfo", ""),
            signtype=data.get("signtype", ""),
            parsed_data=data.get("parsed_data", {}),
        )

    def is_success(self) -> bool:
        """判断是否成功"""
        return self.infcode == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "infcode": self.infcode,
            "inf_refmsgid": self.inf_refmsgid,
            "refmsg_time": self.refmsg_time,
            "respond_time": self.respond_time,
            "err_msg": self.err_msg,
            "output": self.output,
            "warn_msg": self.warn_msg,
            "cainfo": self.cainfo,
            "signtype": self.signtype,
        }
        
        # 如果有解析后的数据，将其合并到结果中
        if self.parsed_data:
            result.update(self.parsed_data)
            
        return result
