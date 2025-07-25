using System;
using System.Collections.Generic;
using System.Drawing;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using MedicalInsurance.Client;

namespace MedicalInsurance.Desktop
{
    public partial class MainForm : Form
    {
        private MedicalInsuranceClient _client;
        private TextBox _apiCodeTextBox;
        private TextBox _orgCodeTextBox;
        private TextBox _dataTextBox;
        private TextBox _resultTextBox;
        private Button _callButton;
        private Button _validateButton;
        private Button _asyncCallButton;
        private ComboBox _interfaceComboBox;
        private StatusStrip _statusStrip;
        private ToolStripStatusLabel _statusLabel;

        public MainForm()
        {
            InitializeComponent();
            _client = new MedicalInsuranceClient();
            LoadSupportedInterfaces();
        }

        private void InitializeComponent()
        {
            this.Text = "医保接口SDK桌面客户端";
            this.Size = new Size(800, 600);
            this.StartPosition = FormStartPosition.CenterScreen;

            // 创建控件
            var mainPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 7
            };

            // 接口选择
            mainPanel.Controls.Add(new Label { Text = "接口选择:", Anchor = AnchorStyles.Right }, 0, 0);
            _interfaceComboBox = new ComboBox 
            { 
                Dock = DockStyle.Fill,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            _interfaceComboBox.SelectedIndexChanged += InterfaceComboBox_SelectedIndexChanged;
            mainPanel.Controls.Add(_interfaceComboBox, 1, 0);

            // 接口编码
            mainPanel.Controls.Add(new Label { Text = "接口编码:", Anchor = AnchorStyles.Right }, 0, 1);
            _apiCodeTextBox = new TextBox { Dock = DockStyle.Fill, Text = "1101" };
            mainPanel.Controls.Add(_apiCodeTextBox, 1, 1);

            // 机构代码
            mainPanel.Controls.Add(new Label { Text = "机构代码:", Anchor = AnchorStyles.Right }, 0, 2);
            _orgCodeTextBox = new TextBox { Dock = DockStyle.Fill, Text = "H43010000001" };
            mainPanel.Controls.Add(_orgCodeTextBox, 1, 2);

            // 请求数据
            mainPanel.Controls.Add(new Label { Text = "请求数据:", Anchor = AnchorStyles.Right | AnchorStyles.Top }, 0, 3);
            _dataTextBox = new TextBox 
            { 
                Dock = DockStyle.Fill, 
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                Text = GetDefaultRequestData()
            };
            mainPanel.Controls.Add(_dataTextBox, 1, 3);

            // 按钮面板
            var buttonPanel = new FlowLayoutPanel { Dock = DockStyle.Fill };
            _callButton = new Button { Text = "调用接口", Size = new Size(80, 30) };
            _callButton.Click += CallButton_Click;
            _validateButton = new Button { Text = "验证数据", Size = new Size(80, 30) };
            _validateButton.Click += ValidateButton_Click;
            _asyncCallButton = new Button { Text = "异步调用", Size = new Size(80, 30) };
            _asyncCallButton.Click += AsyncCallButton_Click;

            buttonPanel.Controls.AddRange(new Control[] { _callButton, _validateButton, _asyncCallButton });
            mainPanel.Controls.Add(new Label(), 0, 4);
            mainPanel.Controls.Add(buttonPanel, 1, 4);

            // 响应结果
            mainPanel.Controls.Add(new Label { Text = "响应结果:", Anchor = AnchorStyles.Right | AnchorStyles.Top }, 0, 5);
            _resultTextBox = new TextBox 
            { 
                Dock = DockStyle.Fill, 
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true
            };
            mainPanel.Controls.Add(_resultTextBox, 1, 5);

            // 设置行高
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 30));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 40));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 60));

            // 设置列宽
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 100));
            mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));

            // 状态栏
            _statusStrip = new StatusStrip();
            _statusLabel = new ToolStripStatusLabel("就绪");
            _statusStrip.Items.Add(_statusLabel);

            this.Controls.Add(mainPanel);
            this.Controls.Add(_statusStrip);
        }

        private string GetDefaultRequestData()
        {
            var defaultData = new Dictionary<string, object>
            {
                ["psn_no"] = "H430100000000000001",
                ["mdtrt_cert_type"] = "01",
                ["mdtrt_cert_no"] = "430100000000000001",
                ["psn_name"] = "张三"
            };

            return JsonSerializer.Serialize(defaultData, new JsonSerializerOptions 
            { 
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            });
        }

        private async void LoadSupportedInterfaces()
        {
            try
            {
                UpdateStatus("加载接口列表...");
                var result = await _client.GetSupportedInterfacesAsync();
                
                if (result.Success && result.Data?.Interfaces != null)
                {
                    _interfaceComboBox.Items.Clear();
                    _interfaceComboBox.Items.Add("请选择接口");
                    
                    foreach (var interface_ in result.Data.Interfaces)
                    {
                        if (interface_.ContainsKey("api_code") && interface_.ContainsKey("api_name"))
                        {
                            var item = $"{interface_["api_code"]} - {interface_["api_name"]}";
                            _interfaceComboBox.Items.Add(item);
                        }
                    }
                    
                    _interfaceComboBox.SelectedIndex = 0;
                    UpdateStatus("接口列表加载完成");
                }
                else
                {
                    UpdateStatus("加载接口列表失败");
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"加载接口列表异常: {ex.Message}");
            }
        }

        private void InterfaceComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (_interfaceComboBox.SelectedIndex > 0)
            {
                var selectedText = _interfaceComboBox.SelectedItem.ToString();
                var apiCode = selectedText.Split(' ')[0];
                _apiCodeTextBox.Text = apiCode;
                
                // 根据接口类型设置默认数据
                UpdateDefaultDataForInterface(apiCode);
            }
        }

        private void UpdateDefaultDataForInterface(string apiCode)
        {
            Dictionary<string, object> defaultData;
            
            switch (apiCode)
            {
                case "1101":
                    defaultData = new Dictionary<string, object>
                    {
                        ["psn_no"] = "H430100000000000001",
                        ["mdtrt_cert_type"] = "01",
                        ["mdtrt_cert_no"] = "430100000000000001",
                        ["psn_name"] = "张三"
                    };
                    break;
                    
                case "2201":
                    defaultData = new Dictionary<string, object>
                    {
                        ["psn_no"] = "H430100000000000001",
                        ["mdtrt_cert_type"] = "01",
                        ["mdtrt_cert_no"] = "430100000000000001",
                        ["ipt_otp_no"] = "OP202501250001",
                        ["atddr_no"] = "DOC001",
                        ["dr_name"] = "李医生",
                        ["dept_code"] = "001",
                        ["dept_name"] = "内科"
                    };
                    break;
                    
                default:
                    defaultData = new Dictionary<string, object>
                    {
                        ["psn_no"] = "H430100000000000001",
                        ["mdtrt_cert_type"] = "01"
                    };
                    break;
            }

            _dataTextBox.Text = JsonSerializer.Serialize(defaultData, new JsonSerializerOptions 
            { 
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            });
        }

        private async void CallButton_Click(object sender, EventArgs e)
        {
            await CallInterface(false);
        }

        private async void ValidateButton_Click(object sender, EventArgs e)
        {
            try
            {
                UpdateStatus("验证数据中...");
                SetButtonsEnabled(false);

                var data = JsonSerializer.Deserialize<Dictionary<string, object>>(_dataTextBox.Text);
                var result = await _client.ValidateDataAsync(_apiCodeTextBox.Text, data, _orgCodeTextBox.Text);

                DisplayResult(result);
                UpdateStatus(result.Success ? "数据验证完成" : "数据验证失败");
            }
            catch (Exception ex)
            {
                _resultTextBox.Text = $"验证异常: {ex.Message}";
                UpdateStatus("验证异常");
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        private async void AsyncCallButton_Click(object sender, EventArgs e)
        {
            try
            {
                UpdateStatus("提交异步任务...");
                SetButtonsEnabled(false);

                var data = JsonSerializer.Deserialize<Dictionary<string, object>>(_dataTextBox.Text);
                var result = await _client.CallInterfaceAsyncTask(_apiCodeTextBox.Text, data, _orgCodeTextBox.Text);

                if (result.Success && result.Data != null)
                {
                    var taskId = result.Data.TaskId;
                    UpdateStatus($"异步任务已提交，任务ID: {taskId}");
                    
                    // 轮询获取结果
                    await PollTaskResult(taskId);
                }
                else
                {
                    DisplayResult(result);
                    UpdateStatus("异步任务提交失败");
                }
            }
            catch (Exception ex)
            {
                _resultTextBox.Text = $"异步调用异常: {ex.Message}";
                UpdateStatus("异步调用异常");
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        private async Task CallInterface(bool isAsync)
        {
            try
            {
                UpdateStatus("调用接口中...");
                SetButtonsEnabled(false);

                var data = JsonSerializer.Deserialize<Dictionary<string, object>>(_dataTextBox.Text);
                var result = await _client.CallInterfaceAsync(_apiCodeTextBox.Text, data, _orgCodeTextBox.Text);

                DisplayResult(result);
                UpdateStatus(result.Success ? "接口调用完成" : "接口调用失败");
            }
            catch (Exception ex)
            {
                _resultTextBox.Text = $"调用异常: {ex.Message}";
                UpdateStatus("调用异常");
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        private async Task PollTaskResult(string taskId)
        {
            const int maxAttempts = 30;
            const int intervalMs = 1000;

            for (int i = 0; i < maxAttempts; i++)
            {
                await Task.Delay(intervalMs);
                
                var result = await _client.GetTaskResultAsync(taskId);
                
                if (result.Success && result.Data != null)
                {
                    if (result.Data.ContainsKey("status"))
                    {
                        var status = result.Data["status"].ToString();
                        
                        if (status == "completed")
                        {
                            DisplayResult(result);
                            UpdateStatus("异步任务完成");
                            return;
                        }
                        else if (status == "failed")
                        {
                            DisplayResult(result);
                            UpdateStatus("异步任务失败");
                            return;
                        }
                        else
                        {
                            UpdateStatus($"任务状态: {status} ({i + 1}/{maxAttempts})");
                        }
                    }
                }
            }
            
            UpdateStatus("异步任务超时");
        }

        private void DisplayResult<T>(ApiResponse<T> result)
        {
            var displayResult = new
            {
                success = result.Success,
                message = result.Message,
                error = result.Error,
                data = result.Data
            };

            _resultTextBox.Text = JsonSerializer.Serialize(displayResult, new JsonSerializerOptions 
            { 
                WriteIndented = true,
                Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
            });
        }

        private void UpdateStatus(string message)
        {
            if (_statusLabel != null)
            {
                _statusLabel.Text = $"{DateTime.Now:HH:mm:ss} - {message}";
            }
        }

        private void SetButtonsEnabled(bool enabled)
        {
            _callButton.Enabled = enabled;
            _validateButton.Enabled = enabled;
            _asyncCallButton.Enabled = enabled;
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            _client?.Dispose();
            base.OnFormClosed(e);
        }
    }
}