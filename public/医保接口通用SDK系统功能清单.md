# 医保接口结果展示解决方案

## 问题分析

```
刷卡 → 外挂程序 → 数据库触发器 → 医保接口调用 → 结果存储到数据库
                                                    ↓
                                            用户如何看到结果？
```

**核心问题：医保查询结果存储在数据库中，但用户（医生/收费员）如何实时看到这些结果？**

## 解决方案对比

### 方案1：弹窗提示（推荐）
```
优势：直观、实时、不依赖HIS界面
缺点：可能被拦截、需要用户确认
适用：所有场景
```

### 方案2：HIS界面集成
```
优势：界面统一、用户习惯
缺点：需要修改HIS代码
适用：有HIS源码的情况
```

### 方案3：独立显示程序
```
优势：专业、功能丰富
缺点：需要额外屏幕空间
适用：专门的医保工作站
```

### 方案4：Web界面
```
优势：跨平台、易维护
缺点：需要打开浏览器
适用：现代化医院
```

## 方案1：智能弹窗提示（推荐方案）

### 1.1 弹窗程序设计
```python
# medical_result_display.py
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import json
import threading
import time
from datetime import datetime
import winsound

class MedicalResultDisplay:
    """医保结果展示程序"""
    
    def __init__(self):
        self.db_connection = "DRIVER={SQL Server};SERVER=localhost;DATABASE=HIS;Trusted_Connection=yes;"
        self.last_check_time = datetime.now()
        self.running = True
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_results, daemon=True)
        monitor_thread.start()
    
    def _monitor_results(self):
        """监控医保查询结果"""
        while self.running:
            try:
                self._check_new_results()
                time.sleep(2)  # 每2秒检查一次
            except Exception as e:
                print(f"监控异常: {e}")
                time.sleep(5)
    
    def _check_new_results(self):
        """检查新的查询结果"""
        try:
            with pyodbc.connect(self.db_connection) as conn:
                cursor = conn.cursor()
                
                # 查询最新完成的记录
                cursor.execute("""
                    SELECT id, input_data, input_type, result_data, workstation_id
                    FROM medical_trigger
                    WHERE status = 'COMPLETED'
                    AND process_time > ?
                    AND result_data IS NOT NULL
                    ORDER BY process_time DESC
                """, self.last_check_time)
                
                results = cursor.fetchall()
                
                for result in results:
                    self._show_result_popup(result)
                
                if results:
                    self.last_check_time = datetime.now()
                    
        except Exception as e:
            print(f"检查结果异常: {e}")
    
    def _show_result_popup(self, result_record):
        """显示结果弹窗"""
        try:
            result_data = json.loads(result_record.result_data)
            
            if result_data.get('infcode') == '0':
                # 成功结果
                self._show_success_popup(result_record, result_data)
            else:
                # 错误结果
                self._show_error_popup(result_record, result_data)
                
        except Exception as e:
            print(f"显示弹窗异常: {e}")
    
    def _show_success_popup(self, record, result_data):
        """显示成功结果弹窗"""
        # 播放提示音
        winsound.MessageBeep(winsound.MB_OK)
        
        # 创建弹窗
        popup = tk.Toplevel()
        popup.title("医保查询结果")
        popup.geometry("400x300")
        popup.attributes('-topmost', True)  # 置顶显示
        popup.grab_set()  # 模态窗口
        
        # 设置窗口位置（右下角）
        popup.geometry("+{}+{}".format(
            popup.winfo_screenwidth() - 420,
            popup.winfo_screenheight() - 350
        ))
        
        # 创建界面
        main_frame = ttk.Frame(popup, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="✅ 医保查询成功", 
                               font=("微软雅黑", 12, "bold"),
                               foreground="green")
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # 解析并显示结果
        if record.input_type == 'card':
            self._display_person_info(main_frame, result_data)
        elif record.input_type == 'qrcode':
            self._display_qrcode_info(main_frame, result_data)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="确定", 
                  command=popup.destroy).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="复制信息", 
                  command=lambda: self._copy_to_clipboard(result_data)).pack(side=tk.LEFT)
        
        # 5秒后自动关闭
        popup.after(5000, popup.destroy)
    
    def _display_person_info(self, parent, result_data):
        """显示人员信息"""
        person_info = result_data.get('output', {}).get('baseinfo', {})
        
        info_items = [
            ("姓名", person_info.get('psn_name', '')),
            ("性别", "男" if person_info.get('gend') == '1' else "女"),
            ("出生日期", person_info.get('brdy', '')),
            ("参保状态", person_info.get('psn_insu_stas', '')),
            ("参保类型", person_info.get('insutype', '')),
            ("个人账户余额", f"{person_info.get('act_pay_sumamt', 0)}元"),
        ]
        
        row = 1
        for label, value in info_items:
            ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, pady=2)
            ttk.Label(parent, text=value, font=("微软雅黑", 9, "bold")).grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            row += 1
    
    def _show_error_popup(self, record, result_data):
        """显示错误结果弹窗"""
        # 播放错误提示音
        winsound.MessageBeep(winsound.MB_ICONERROR)
        
        messagebox.showerror(
            "医保查询失败",
            f"查询失败: {result_data.get('err_msg', '未知错误')}\n\n"
            f"输入数据: {record.input_data}\n"
            f"工作站: {record.workstation_id}"
        )
    
    def _copy_to_clipboard(self, result_data):
        """复制信息到剪贴板"""
        try:
            import pyperclip
            
            person_info = result_data.get('output', {}).get('baseinfo', {})
            clipboard_text = f"""
姓名: {person_info.get('psn_name', '')}
性别: {'男' if person_info.get('gend') == '1' else '女'}
出生日期: {person_info.get('brdy', '')}
参保状态: {person_info.get('psn_insu_stas', '')}
个人账户余额: {person_info.get('act_pay_sumamt', 0)}元
            """.strip()
            
            pyperclip.copy(clipboard_text)
            messagebox.showinfo("提示", "信息已复制到剪贴板")
            
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {e}")

if __name__ == "__main__":
    app = MedicalResultDisplay()
    
    # 保持程序运行
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.mainloop()
```

### 1.2 弹窗效果展示
```
┌─────────────────────────────────────┐
│  ✅ 医保查询成功                     │
├─────────────────────────────────────┤
│  姓名:     张三                      │
│  性别:     男                        │
│  出生日期: 1990-01-01               │
│  参保状态: 正常参保                  │
│  参保类型: 城镇职工基本医疗保险      │
│  个人账户余额: 1,234.56元           │
├─────────────────────────────────────┤
│  [确定]  [复制信息]                 │
└─────────────────────────────────────┘
```

## 方案2：HIS界面集成（如果可以修改HIS）

### 2.1 数据库视图方式
```sql
-- 创建医保信息视图，供HIS查询
CREATE VIEW v_patient_medical_insurance AS
SELECT 
    p.patient_id,
    p.id_card_no,
    t.result_data,
    JSON_VALUE(t.result_data, '$.output.baseinfo.psn_name') as insurance_name,
    JSON_VALUE(t.result_data, '$.output.baseinfo.psn_insu_stas') as insurance_status,
    JSON_VALUE(t.result_data, '$.output.baseinfo.act_pay_sumamt') as account_balance,
    t.process_time as last_update_time
FROM his_patient_table p
LEFT JOIN (
    SELECT DISTINCT 
        input_data,
        result_data,
        process_time,
        ROW_NUMBER() OVER (PARTITION BY input_data ORDER BY process_time DESC) as rn
    FROM medical_trigger 
    WHERE status = 'COMPLETED' AND result_data IS NOT NULL
) t ON p.id_card_no = t.input_data AND t.rn = 1;
```

### 2.2 HIS查询示例
```sql
-- HIS系统可以这样查询患者医保信息
SELECT 
    patient_name,
    insurance_name,
    insurance_status,
    account_balance,
    last_update_time
FROM v_patient_medical_insurance
WHERE patient_id = @patient_id;
```

## 方案3：独立显示程序

### 3.1 专业医保信息显示器
```python
# medical_info_dashboard.py
import tkinter as tk
from tkinter import ttk
import pyodbc
import json
import threading
import time

class MedicalInfoDashboard:
    """医保信息仪表板"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("医保信息显示器")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.start_monitoring()
    
    def setup_ui(self):
        """设置界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="医保信息实时显示", 
                               font=("微软雅黑", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 当前患者信息区域
        current_frame = ttk.LabelFrame(main_frame, text="当前患者", padding="10")
        current_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.current_info_text = tk.Text(current_frame, height=8, width=80, 
                                        font=("微软雅黑", 10))
        self.current_info_text.grid(row=0, column=0)
        
        # 历史记录区域
        history_frame = ttk.LabelFrame(main_frame, text="查询历史", padding="10")
        history_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建表格
        columns = ("时间", "输入", "姓名", "状态", "余额")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=120)
        
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.history_tree.configure(yscrollcommand=scrollbar.set)
    
    def start_monitoring(self):
        """启动监控"""
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _monitor_loop(self):
        """监控循环"""
        last_check = time.time()
        
        while True:
            try:
                self._update_display(last_check)
                last_check = time.time()
                time.sleep(3)
            except Exception as e:
                print(f"监控异常: {e}")
                time.sleep(5)
    
    def _update_display(self, last_check):
        """更新显示"""
        # 这里实现数据库查询和界面更新逻辑
        pass
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

if __name__ == "__main__":
    dashboard = MedicalInfoDashboard()
    dashboard.run()
```

## 方案4：Web界面展示

### 4.1 Web服务
```python
# medical_web_display.py
from flask import Flask, render_template, jsonify
import pyodbc
import json

app = Flask(__name__)

@app.route('/')
def index():
    """主页面"""
    return render_template('medical_display.html')

@app.route('/api/latest_results')
def get_latest_results():
    """获取最新查询结果"""
    try:
        with pyodbc.connect(db_connection) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 10 
                    input_data, input_type, result_data, process_time, workstation_id
                FROM medical_trigger
                WHERE status = 'COMPLETED'
                ORDER BY process_time DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                result_data = json.loads(row.result_data) if row.result_data else {}
                results.append({
                    'input_data': row.input_data,
                    'input_type': row.input_type,
                    'result_data': result_data,
                    'process_time': row.process_time.isoformat(),
                    'workstation_id': row.workstation_id
                })
            
            return jsonify(results)
            
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### 4.2 Web页面
```html
<!-- templates/medical_display.html -->
<!DOCTYPE html>
<html>
<head>
    <title>医保信息显示</title>
    <meta charset="utf-8">
    <style>
        body { font-family: "微软雅黑"; margin: 20px; }
        .result-card { 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 5px; 
        }
        .success { border-left: 5px solid #4CAF50; }
        .error { border-left: 5px solid #f44336; }
        .info-row { margin: 5px 0; }
        .label { font-weight: bold; display: inline-block; width: 100px; }
    </style>
</head>
<body>
    <h1>医保查询结果实时显示</h1>
    <div id="results-container"></div>

    <script>
        function updateResults() {
            fetch('/api/latest_results')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('results-container');
                    container.innerHTML = '';
                    
                    data.forEach(result => {
                        const card = document.createElement('div');
                        card.className = 'result-card ' + (result.result_data.infcode === '0' ? 'success' : 'error');
                        
                        if (result.result_data.infcode === '0') {
                            const person = result.result_data.output.baseinfo;
                            card.innerHTML = `
                                <div class="info-row"><span class="label">查询时间:</span>${result.process_time}</div>
                                <div class="info-row"><span class="label">工作站:</span>${result.workstation_id}</div>
                                <div class="info-row"><span class="label">姓名:</span>${person.psn_name}</div>
                                <div class="info-row"><span class="label">性别:</span>${person.gend === '1' ? '男' : '女'}</div>
                                <div class="info-row"><span class="label">参保状态:</span>${person.psn_insu_stas}</div>
                                <div class="info-row"><span class="label">账户余额:</span>${person.act_pay_sumamt}元</div>
                            `;
                        } else {
                            card.innerHTML = `
                                <div class="info-row"><span class="label">查询失败:</span>${result.result_data.err_msg}</div>
                                <div class="info-row"><span class="label">输入数据:</span>${result.input_data}</div>
                            `;
                        }
                        
                        container.appendChild(card);
                    });
                });
        }
        
        // 每3秒更新一次
        setInterval(updateResults, 3000);
        updateResults(); // 立即执行一次
    </script>
</body>
</html>
```

## 推荐实施方案

### 阶段1：基础弹窗（立即可用）
```python
# 部署弹窗程序，实现基本结果展示
python medical_result_display.py
```

### 阶段2：HIS集成（如果可能）
```sql
-- 创建视图供HIS查询
CREATE VIEW v_patient_medical_insurance AS ...
```

### 阶段3：专业显示（可选）
```python
# 部署专业显示程序或Web界面
python medical_info_dashboard.py
```

## 总结

**推荐使用方案1（智能弹窗）**，因为：

✅ **零HIS入侵**：不需要修改HIS任何代码
✅ **实时展示**：刷卡后几秒内弹窗显示结果  
✅ **用户友好**：直观的图形界面，支持复制信息
✅ **部署简单**：一个Python程序搞定
✅ **兼容性好**：适用于所有Windows系统

这样就完美解决了"医保返回结果如何展示给用户"的问题！

你觉得这个弹窗方案怎么样？还有什么需要优化的地方吗？