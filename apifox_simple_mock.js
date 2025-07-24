// 简化版Apifox Mock脚本

const infno = pm.request.body.infno;

if (infno === "1101") {
    // 1101人员信息查询
    pm.response.json({
        "infcode": 0,
        "inf_refmsgid": "MSG001",
        "respond_time": "20240115103000",
        "err_msg": "",
        "output": {
            "baseinfo": {
                "psn_no": "123456789",
                "psn_name": "张三",
                "gend": "1",
                "brdy": "1990-01-01",
                "certno": "430123199001011234",
                "tel": "13800138000",
                "addr": "湖南省长沙市"
            },
            "insuinfo": [{
                "insutype": "310",
                "balc": "5000.00",
                "psn_insu_stas": "1"
            }]
        }
    });
} else if (infno === "2201") {
    // 2201门诊结算
    pm.response.json({
        "infcode": 0,
        "inf_refmsgid": "MSG002", 
        "respond_time": "20240115103000",
        "err_msg": "",
        "output": {
            "setlinfo": {
                "setl_id": "SETL20240115001",
                "setl_totlnum": "1000.00",
                "hifp_pay": "800.00",
                "psn_pay": "200.00",
                "acct_pay": "100.00",
                "psn_cash_pay": "100.00",
                "setl_time": "2024-01-15 10:30:00"
            }
        }
    });
} else {
    // 其他接口返回错误
    pm.response.json({
        "infcode": -1,
        "err_msg": "不支持的接口: " + infno,
        "output": {}
    });
}