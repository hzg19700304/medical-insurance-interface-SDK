# 医保SDK使用示例 - 弹窗+打印方案

## 方案概述

**弹窗显示 + 自动打印** = 完美的用户体验

```
刷卡 → 医保查询 → 弹窗显示结果 → 自动打印凭条 → 用户确认
  ↓         ↓           ↓            ↓           ↓
 瞬间      3秒内      实时查看      纸质凭证    继续业务
```

## 1. 增强版弹窗程序

### 1.1 带打印功能的弹窗
```python
# medical_result_display_with_print.py
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import json
import threading
import time
from datetime import datetime
import winsound
import win32print
import win32ui
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os

class MedicalResultDisplayWithPrint:
    """医保结果展示+打印程序"""
    
    def __init__(self):
        self.db_connection = "DRIVER={SQL Server};SERVER=localhost;DATABASE=HIS;Trusted_Connection=yes;"
        self.last_check_time = datetime.now()
        self.running = True
        
        # 打印机配置
        self.printer_name = self._get_default_printer()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self._monitor_results, daemon=True)
        monitor_thread.start()
        
        print(f"医保结果显示程序启动，使用打印机: {self.printer_name}")
    
    def _get_default_printer(self):
        """获取默认打印机"""
        try:
            return win32print.GetDefaultPrinter()
        except:
            # 如果没有默认打印机，获取第一个可用打印机
            printers = [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            return printers[0] if printers else None
    
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
                    SELECT id, input_data, input_type, result_data, workstation_id, process_time
                    FROM medical_trigger
                    WHERE status = 'COMPLETED'
                    AND process_time > ?
                    AND result_data IS NOT NULL
                    AND printed = 0  -- 未打印的记录
                    ORDER BY process_time DESC
                """, self.last_check_time)
                
                results = cursor.fetchall()
                
                for result in results:
                    self._process_result(result)
                    
                    # 标记为已处理
                    cursor.execute("""
                        UPDATE medical_trigger 
                        SET printed = 1, print_time = GETDATE()
                        WHERE id = ?
                    """, result.id)
                    conn.commit()
                
                if results:
                    self.last_check_time = datetime.now()
                    
        except Exception as e:
            print(f"检查结果异常: {e}")
    
    def _process_result(self, result_record):
        """处理查询结果"""
        try:
            result_data = json.loads(result_record.result_data)
            
            if result_data.get('infcode') == '0':
                # 成功：显示弹窗 + 打印
                self._show_success_popup_and_print(result_record, result_data)
            else:
                # 失败：只显示错误弹窗
                self._show_error_popup(result_record, result_data)
                
        except Exception as e:
            print(f"处理结果异常: {e}")
    
    def _show_success_popup_and_print(self, record, result_data):
        """显示成功弹窗并打印"""
        # 1. 先打印（避免用户忘记）
        print_success = self._print_medical_info(record, result_data)
        
        # 2. 播放提示音
        winsound.MessageBeep(winsound.MB_OK)
        
        # 3. 显示弹窗
        popup = tk.Toplevel()
        popup.title("医保查询成功")
        popup.geometry("450x400")
        popup.attributes('-topmost', True)
        popup.grab_set()
        
        # 窗口位置（右下角）
        popup.geometry("+{}+{}".format(
            popup.winfo_screenwidth() - 470,
            popup.winfo_screenheight() - 450
        ))
        
        # 创建界面
        main_frame = ttk.Frame(popup, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_text = "✅ 医保查询成功" + (" (已打印)" if print_success else " (打印失败)")
        title_label = ttk.Label(main_frame, text=title_text, 
                               font=("微软雅黑", 12, "bold"),
                               foreground="green" if print_success else "orange")
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # 显示患者信息
        self._display_person_info_in_popup(main_frame, result_data)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=20, column=0, columnspan=2, pady=(15, 0))
        
        ttk.Button(button_frame, text="确定", 
                  command=popup.destroy).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="重新打印", 
                  command=lambda: self._print_medical_info(record, result_data)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="复制信息", 
                  command=lambda: self._copy_to_clipboard(result_data)).pack(side=tk.LEFT)
        
        # 8秒后自动关闭
        popup.after(8000, popup.destroy)
    
    def _print_medical_info(self, record, result_data):
        """打印医保信息"""
        try:
            if not self.printer_name:
                print("未找到可用打印机")
                return False
            
            # 生成打印内容
            print_content = self._generate_print_content(record, result_data)
            
            # 创建打印图像
            print_image = self._create_print_image(print_content)
            
            # 执行打印
            self._execute_print(print_image)
            
            print(f"打印成功: {record.input_data}")
            return True
            
        except Exception as e:
            print(f"打印失败: {e}")
            return False
    
    def _generate_print_content(self, record, result_data):
        """生成打印内容"""
        person_info = result_data.get('output', {}).get('baseinfo', {})
        
        content = {
            'title': '医保信息查询结果',
            'time': record.process_time.strftime('%Y-%m-%d %H:%M:%S'),
            'workstation': record.workstation_id or '未知工作站',
            'items': [
                ('姓名', person_info.get('psn_name', '')),
                ('性别', '男' if person_info.get('gend') == '1' else '女'),
                ('出生日期', person_info.get('brdy', '')),
                ('证件号码', person_info.get('certno', record.input_data)),
                ('参保状态', person_info.get('psn_insu_stas', '')),
                ('参保类型', self._get_insurance_type_name(person_info.get('insutype', ''))),
                ('个人账户余额', f"{person_info.get('act_pay_sumamt', 0):.2f}元"),
                ('统筹账户余额', f"{person_info.get('ovlmt_amt', 0):.2f}元"),
            ]
        }
        
        return content
    
    def _create_print_image(self, content):
        """创建打印图像"""
        # 小票尺寸 (58mm热敏打印机)
        width = 384  # 58mm = 384像素 (约6.8像素/mm)
        height = 600  # 根据内容动态调整
        
        # 创建图像
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        
        # 字体设置
        try:
            title_font = ImageFont.truetype("msyh.ttc", 16)  # 微软雅黑
            normal_font = ImageFont.truetype("msyh.ttc", 12)
            small_font = ImageFont.truetype("msyh.ttc", 10)
        except:
            title_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        y = 10
        
        # 标题
        title_bbox = draw.textbbox((0, 0), content['title'], font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, y), content['title'], 
                 fill='black', font=title_font)
        y += 30
        
        # 分割线
        draw.line([(10, y), (width-10, y)], fill='black', width=1)
        y += 15
        
        # 查询时间
        draw.text((10, y), f"查询时间: {content['time']}", fill='black', font=small_font)
        y += 20
        
        # 工作站
        draw.text((10, y), f"工作站: {content['workstation']}", fill='black', font=small_font)
        y += 25
        
        # 分割线
        draw.line([(10, y), (width-10, y)], fill='black', width=1)
        y += 15
        
        # 患者信息
        for label, value in content['items']:
            if value:  # 只显示有值的项目
                text = f"{label}: {value}"
                draw.text((10, y), text, fill='black', font=normal_font)
                y += 22
        
        # 底部分割线
        y += 10
        draw.line([(10, y), (width-10, y)], fill='black', width=1)
        y += 15
        
        # 底部说明
        footer_text = "此凭条仅供参考，以医保系统实际数据为准"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=small_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        draw.text(((width - footer_width) // 2, y), footer_text, 
                 fill='gray', font=small_font)
        y += 30
        
        # 裁剪图像到实际使用的高度
        img = img.crop((0, 0, width, y))
        
        return img
    
    def _execute_print(self, image):
        """执行打印"""
        # 保存临时图像文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.bmp', delete=False)
        image.save(temp_file.name, 'BMP')
        temp_file.close()
        
        try:
            # 使用Windows API打印
            hprinter = win32print.OpenPrinter(self.printer_name)
            
            try:
                # 开始打印作业
                hjob = win32print.StartDocPrinter(hprinter, 1, ("医保查询结果", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                
                # 读取图像数据
                with open(temp_file.name, 'rb') as f:
                    image_data = f.read()
                
                # 发送到打印机
                win32print.WritePrinter(hprinter, image_data)
                
                # 结束打印
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                
            finally:
                win32print.ClosePrinter(hprinter)
                
        finally:
            # 删除临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
    
    def _get_insurance_type_name(self, insutype):
        """获取参保类型名称"""
        type_map = {
            '310': '城镇职工基本医疗保险',
            '320': '城乡居民基本医疗保险',
            '330': '公务员医疗补助',
            '340': '新农合',
            '390': '其他医疗保险'
        }
        return type_map.get(insutype, f'未知类型({insutype})')
    
    def _display_person_info_in_popup(self, parent, result_data):
        """在弹窗中显示人员信息"""
        person_info = result_data.get('output', {}).get('baseinfo', {})
        
        info_items = [
            ("姓名", person_info.get('psn_name', '')),
            ("性别", "男" if person_info.get('gend') == '1' else "女"),
            ("出生日期", person_info.get('brdy', '')),
            ("参保状态", person_info.get('psn_insu_stas', '')),
            ("参保类型", self._get_insurance_type_name(person_info.get('insutype', ''))),
            ("个人账户余额", f"{person_info.get('act_pay_sumamt', 0):.2f}元"),
            ("统筹账户余额", f"{person_info.get('ovlmt_amt', 0):.2f}元"),
        ]
        
        row = 1
        for label, value in info_items:
            if value:  # 只显示有值的项目
                ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, pady=3)
                value_label = ttk.Label(parent, text=value, font=("微软雅黑", 9, "bold"))
                value_label.grid(row=row, column=1, sticky=tk.W, padx=(15, 0), pady=3)
                row += 1
    
    def _show_error_popup(self, record, result_data):
        """显示错误弹窗"""
        winsound.MessageBeep(winsound.MB_ICONERROR)
        
        messagebox.showerror(
            "医保查询失败",
            f"查询失败: {result_data.get('err_msg', '未知错误')}\n\n"
            f"输入数据: {record.input_data}\n"
            f"工作站: {record.workstation_id}\n"
            f"时间: {record.process_time}"
        )
    
    def _copy_to_clipboard(self, result_data):
        """复制信息到剪贴板"""
        try:
            import pyperclip
            
            person_info = result_data.get('output', {}).get('baseinfo', {})
            clipboard_text = f"""医保信息查询结果
姓名: {person_info.get('psn_name', '')}
性别: {'男' if person_info.get('gend') == '1' else '女'}
出生日期: {person_info.get('brdy', '')}
参保状态: {person_info.get('psn_insu_stas', '')}
参保类型: {self._get_insurance_type_name(person_info.get('insutype', ''))}
个人账户余额: {person_info.get('act_pay_sumamt', 0):.2f}元
统筹账户余额: {person_info.get('ovlmt_amt', 0):.2f}元
查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            pyperclip.copy(clipboard_text)
            messagebox.showinfo("提示", "信息已复制到剪贴板")
            
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {e}")

if __name__ == "__main__":
    app = MedicalResultDisplayWithPrint()
    
    # 保持程序运行
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.running = False
        print("程序停止")
```

## 2. 数据库表结构更新

```sql
-- 在medical_trigger表中添加打印相关字段
ALTER TABLE medical_trigger 
ADD printed BIT DEFAULT 0,           -- 是否已打印
    print_time DATETIME,             -- 打印时间
    print_count INT DEFAULT 0;       -- 打印次数
```

## 3. 打印效果示例

### 3.1 热敏小票效果
```
    ================================
           医保信息查询结果
    ================================
    查询时间: 2024-01-15 14:30:25
    工作站: CASHIER-01
    --------------------------------
    姓名: 张三
    性别: 男
    出生日期: 1990-01-01
    证件号码: 430123199001011234
    参保状态: 正常参保
    参保类型: 城镇职工基本医疗保险
    个人账户余额: 1,234.56元
    统筹账户余额: 5,678.90元
    --------------------------------
    此凭条仅供参考，以医保系统实际数据为准
```

### 3.2 A4纸打印效果（可选）
```python
def _create_a4_print_content(self, content):
    """创建A4纸打印内容"""
    # A4尺寸: 210mm x 297mm
    width = 1654  # 210mm * 7.87像素/mm
    height = 2339  # 297mm * 7.87像素/mm
    
    # 创建更详细的打印内容，包含医院信息、患者照片等
    # ...
```

## 4. 配置文件

```json
{
  "database": {
    "connection_string": "DRIVER={SQL Server};SERVER=localhost;DATABASE=HIS;Trusted_Connection=yes;"
  },
  "printer": {
    "default_printer": "",  // 空表示使用系统默认打印机
    "paper_type": "thermal_58mm",  // thermal_58mm, thermal_80mm, a4
    "auto_print": true,     // 是否自动打印
    "print_copies": 1       // 打印份数
  },
  "display": {
    "popup_duration": 8,    // 弹窗显示时间(秒)
    "check_interval": 2,    // 检查间隔(秒)
    "sound_enabled": true,  // 是否播放提示音
    "position": "bottom_right"  // 弹窗位置
  }
}
```

## 5. 使用场景

### 场景1：门诊挂号
```
1. 患者到挂号窗口
2. 挂号员刷患者医保卡
3. 自动打印患者医保信息小票
4. 弹窗显示详细信息
5. 挂号员将小票给患者，继续HIS挂号
```

### 场景2：门诊收费
```
1. 患者到收费窗口出示医保卡
2. 收费员刷卡查询医保信息
3. 打印医保账户余额凭条
4. 弹窗显示可用额度
5. 收费员根据信息进行收费
```

### 场景3：药房发药
```
1. 患者到药房取药
2. 药师刷患者医保卡
3. 打印患者用药限制信息
4. 弹窗显示特殊用药提醒
5. 药师根据信息决定发药
```

## 6. 优势总结

### ✅ 用户体验
- **即时反馈**：刷卡后立即看到结果
- **纸质凭证**：患者可以带走参考
- **操作简单**：无需额外操作

### ✅ 技术优势
- **零HIS入侵**：完全不修改HIS代码
- **自动化程度高**：刷卡即打印
- **兼容性好**：支持各种打印机

### ✅ 实用性
- **信息完整**：包含所有关键医保信息
- **便于存档**：纸质凭条可以保存
- **减少错误**：避免手工记录错误

这个**弹窗+打印**的方案真正做到了用户友好，既有实时的电子显示，又有可保存的纸质凭证。你觉得这个方案怎么样？