// Apifox条件Mock脚本
// 根据请求中的infno字段返回不同的医保接口数据

// 获取请求数据
const requestBody = pm.request.body;
const infno = requestBody.infno;

// 生成通用响应头
function generateCommonResponse() {
    return {
        "inf_refmsgid": pm.variables.replaceIn("{{$randomUUID}}"),
        "refmsg_time": pm.variables.replaceIn("{{$timestamp}}"),
        "respond_time": pm.variables.replaceIn("{{$timestamp}}"),
        "warn_msg": "",
        "cainfo": "",
        "signtype": ""
    };
}

// 根据接口编号返回不同数据
switch(infno) {
    case "1101":
        // 人员信息查询接口
        pm.response.json({
            "infcode": 0,
            "err_msg": "",
            ...generateCommonResponse(),
            "output": {
                "baseinfo": {
                    "psn_no": pm.variables.replaceIn("{{$randomInt(100000000, 999999999)}}"),
                    "psn_cert_type": "01",
                    "certno": requestBody.input.certno || "430123199001011234",
                    "psn_name": requestBody.input.psn_name || pm.variables.replaceIn("{{$randomChineseName}}"),
                    "gend": pm.variables.replaceIn("{{$randomInt(1, 2)}}"),
                    "naty": "01",
                    "brdy": "1990-01-01",
                    "age": 34,
                    "tel": pm.variables.replaceIn("{{$randomPhone}}"),
                    "addr": "湖南省长沙市测试地址",
                    "card_sn": pm.variables.replaceIn("{{$randomAlphaNumeric(16)}}"),
                    "cvlserv_flag": "0",
                    "insutype": "310",
                    "psn_type": "1",
                    "insuplc_admdvs": "4301"
                },
                "insuinfo": [
                    {
                        "balc": pm.variables.replaceIn("{{$randomFloat(1000, 10000, 2)}}"),
                        "insutype": "310",
                        "psn_idet_type": "1",
                        "psn_type": "1",
                        "psn_type_name": "在职职工",
                        "cum_amt_lmt": pm.variables.replaceIn("{{$randomFloat(50000, 100000, 2)}}"),
                        "psn_insu_stas": "1",
                        "psn_insu_date": "2020-01-01"
                    }
                ],
                "idetinfo": [
                    {
                        "psn_idet_type": "1",
                        "psn_type_lv": "1",
                        "begntime": "2023-01-01",
                        "endtime": "2025-12-31"
                    }
                ]
            }
        });
        break;
        
    case "2201":
        // 门诊结算接口
        const totalAmount = parseFloat(pm.variables.replaceIn("{{$randomFloat(100, 2000, 2)}}"));
        const insurancePay = totalAmount * 0.8; // 医保支付80%
        const personalPay = totalAmount - insurancePay; // 个人支付20%
        const accountPay = personalPay * 0.6; // 账户支付60%
        const cashPay = personalPay - accountPay; // 现金支付40%
        
        pm.response.json({
            "infcode": 0,
            "err_msg": "",
            ...generateCommonResponse(),
            "output": {
                "setlinfo": {
                    "setl_id": "SETL" + pm.variables.replaceIn("{{$timestamp}}"),
                    "setl_totlnum": totalAmount.toFixed(2),
                    "hifp_pay": insurancePay.toFixed(2),
                    "psn_pay": personalPay.toFixed(2),
                    "acct_pay": accountPay.toFixed(2),
                    "psn_cash_pay": cashPay.toFixed(2),
                    "setl_time": pm.variables.replaceIn("{{$isoTimestamp}}"),
                    "med_type": "11",
                    "setl_type": "1",
                    "invono": "INV" + pm.variables.replaceIn("{{$timestamp}}"),
                    "recp_no": "RCP" + pm.variables.replaceIn("{{$timestamp}}"),
                    "mdtrt_id": requestBody.input.mdtrt_id || "MDT" + pm.variables.replaceIn("{{$timestamp}}"),
                    "psn_no": requestBody.input.psn_no || pm.variables.replaceIn("{{$randomInt(100000000, 999999999)}}"),
                    "insutype": requestBody.input.insutype || "310"
                }
            }
        });
        break;
        
    case "1201":
        // 门诊登记接口（如果需要的话）
        pm.response.json({
            "infcode": 0,
            "err_msg": "",
            ...generateCommonResponse(),
            "output": {
                "mdtrt_id": "MDT" + pm.variables.replaceIn("{{$timestamp}}"),
                "psn_no": requestBody.input.psn_no || pm.variables.replaceIn("{{$randomInt(100000000, 999999999)}}"),
                "insutype": requestBody.input.insutype || "310",
                "begntime": pm.variables.replaceIn("{{$isoTimestamp}}"),
                "med_type": "11"
            }
        });
        break;
        
    default:
        // 未知接口返回错误
        pm.response.json({
            "infcode": -1,
            "err_msg": `不支持的接口编号: ${infno}`,
            ...generateCommonResponse(),
            "output": {}
        });
        break;
}