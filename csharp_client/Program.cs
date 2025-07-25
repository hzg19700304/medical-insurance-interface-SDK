using System;
using System.Windows.Forms;
using MedicalInsurance.Desktop;

namespace MedicalInsurance.Desktop
{
    internal static class Program
    {
        /// <summary>
        /// 应用程序的主入口点。
        /// </summary>
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            
            // 检查Web API服务是否可用
            using (var client = new Client.MedicalInsuranceClient())
            {
                var healthTask = client.CheckHealthAsync();
                healthTask.Wait();
                
                if (!healthTask.Result)
                {
                    MessageBox.Show(
                        "无法连接到医保SDK Web API服务！\n\n" +
                        "请确保Python Web API服务正在运行：\n" +
                        "python scripts/start_web_api.py\n\n" +
                        "服务地址：http://localhost:8080",
                        "连接错误",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                    return;
                }
            }
            
            Application.Run(new MainForm());
        }
    }
}