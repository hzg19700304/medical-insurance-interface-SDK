"""医保接口请求模型"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MedicalInsuranceRequest:
    """医保接口标准请求格式"""

    infno: str = ""  # 交易编号(4位)
    msgid: str = ""  # 报文ID(30位)
    mdtrtarea_admvs: str = ""  # 就医地医保区划(6位)
    insuplc_admdvs: str = ""  # 参保地医保区划(6位)
    recer_sys_code: str = "99"  # 接收方系统代码(10位)
    dev_no: str = "null"  # 设备编号(100位,可空)
    dev_safe_info: str = "null"  # 设备安全信息(2000位,可空)
    cainfo: str = "null"  # 数字签名信息(1024位,可空)
    signtype: str = "SM2"  # 签名类型(10位,建议SM2/SM3)
    infver: str = "1.0.0"  # 接口版本号(6位)
    opter_type: str = "1"  # 经办人类别(3位)
    opter: str = ""  # 经办人(30位)
    opter_name: str = ""  # 经办人姓名(50位)
    inf_time: str = ""  # 交易时间(19位)
    fixmedins_code: str = ""  # 定点医药机构编号(12位)
    fixmedins_name: str = ""  # 定点医药机构名称(20位)
    sign_no: str = "null"  # 交易签到流水号(30位,可空)
    input: Dict[str, Any] = None  # 交易输入(40000位)

    def __post_init__(self):
        """初始化后处理"""
        if self.input is None:
            self.input = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MedicalInsuranceRequest":
        """从字典创建请求对象"""
        return cls(
            infno=data.get("infno", ""),
            msgid=data.get("msgid", ""),
            mdtrtarea_admvs=data.get("mdtrtarea_admvs", ""),
            insuplc_admdvs=data.get("insuplc_admdvs", ""),
            recer_sys_code=data.get("recer_sys_code", "99"),
            dev_no=data.get("dev_no", "null"),
            dev_safe_info=data.get("dev_safe_info", "null"),
            cainfo=data.get("cainfo", "null"),
            signtype=data.get("signtype", "SM2"),
            infver=data.get("infver", "1.0.0"),
            opter_type=data.get("opter_type", "1"),
            opter=data.get("opter", ""),
            opter_name=data.get("opter_name", ""),
            inf_time=data.get("inf_time", ""),
            fixmedins_code=data.get("fixmedins_code", ""),
            fixmedins_name=data.get("fixmedins_name", ""),
            sign_no=data.get("sign_no", "null"),
            input=data.get("input", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "infno": self.infno,
            "msgid": self.msgid,
            "mdtrtarea_admvs": self.mdtrtarea_admvs,
            "insuplc_admdvs": self.insuplc_admdvs,
            "recer_sys_code": self.recer_sys_code,
            "dev_no": self.dev_no,
            "dev_safe_info": self.dev_safe_info,
            "cainfo": self.cainfo,
            "signtype": self.signtype,
            "infver": self.infver,
            "opter_type": self.opter_type,
            "opter": self.opter,
            "opter_name": self.opter_name,
            "inf_time": self.inf_time,
            "fixmedins_code": self.fixmedins_code,
            "fixmedins_name": self.fixmedins_name,
            "sign_no": self.sign_no,
            "input": self.input,
        }
