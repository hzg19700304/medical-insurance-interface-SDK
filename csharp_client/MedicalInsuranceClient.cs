using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace MedicalInsurance.Client
{
    /// <summary>
    /// 医保接口SDK C# 客户端
    /// </summary>
    public class MedicalInsuranceClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;

        public MedicalInsuranceClient(string baseUrl = "http://localhost:8080")
        {
            _baseUrl = baseUrl;
            _httpClient = new HttpClient();
            _httpClient.Timeout = TimeSpan.FromSeconds(30);
        }

        /// <summary>
        /// 调用医保接口
        /// </summary>
        /// <param name="apiCode">接口编码</param>
        /// <param name="data">请求数据</param>
        /// <param name="orgCode">机构代码</param>
        /// <returns>接口响应结果</returns>
        public async Task<ApiResponse<Dictionary<string, object>>> CallInterfaceAsync(
            string apiCode, 
            Dictionary<string, object> data, 
            string orgCode)
        {
            var request = new InterfaceCallRequest
            {
                ApiCode = apiCode,
                Data = data,
                OrgCode = orgCode
            };

            var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            try
            {
                var response = await _httpClient.PostAsync($"{_baseUrl}/api/call", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                var result = JsonSerializer.Deserialize<ApiResponse<Dictionary<string, object>>>(
                    responseJson, 
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    });

                return result;
            }
            catch (Exception ex)
            {
                return new ApiResponse<Dictionary<string, object>>
                {
                    Success = false,
                    Error = ex.Message,
                    Message = "网络请求失败"
                };
            }
        }

        /// <summary>
        /// 异步调用医保接口
        /// </summary>
        public async Task<ApiResponse<TaskInfo>> CallInterfaceAsyncTask(
            string apiCode, 
            Dictionary<string, object> data, 
            string orgCode,
            bool useCelery = true)
        {
            var request = new AsyncCallRequest
            {
                ApiCode = apiCode,
                Data = data,
                OrgCode = orgCode,
                UseCelery = useCelery
            };

            var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            try
            {
                var response = await _httpClient.PostAsync($"{_baseUrl}/api/call/async", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                var result = JsonSerializer.Deserialize<ApiResponse<TaskInfo>>(
                    responseJson, 
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    });

                return result;
            }
            catch (Exception ex)
            {
                return new ApiResponse<TaskInfo>
                {
                    Success = false,
                    Error = ex.Message,
                    Message = "异步任务提交失败"
                };
            }
        }

        /// <summary>
        /// 获取异步任务结果
        /// </summary>
        public async Task<ApiResponse<Dictionary<string, object>>> GetTaskResultAsync(string taskId)
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_baseUrl}/api/task/{taskId}");
                var responseJson = await response.Content.ReadAsStringAsync();
                
                var result = JsonSerializer.Deserialize<ApiResponse<Dictionary<string, object>>>(
                    responseJson, 
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    });

                return result;
            }
            catch (Exception ex)
            {
                return new ApiResponse<Dictionary<string, object>>
                {
                    Success = false,
                    Error = ex.Message,
                    Message = "获取任务结果失败"
                };
            }
        }

        /// <summary>
        /// 批量调用医保接口
        /// </summary>
        public async Task<ApiResponse<BatchResult>> CallBatchAsync(List<InterfaceCallRequest> requests)
        {
            var batchRequest = new BatchCallRequest
            {
                Requests = requests
            };

            var json = JsonSerializer.Serialize(batchRequest, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            try
            {
                var response = await _httpClient.PostAsync($"{_baseUrl}/api/call/batch", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                var result = JsonSerializer.Deserialize<ApiResponse<BatchResult>>(
                    responseJson, 
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    });

                return result;
            }
            catch (Exception ex)
            {
                return new ApiResponse<BatchResult>
                {
                    Success = false,
                    Error = ex.Message,
                    Message = "批量调用失败"
                };
            }
        }

        /// <summary>
        /// 获取支持的接口列表
        /// </summary>
        public async Task<ApiResponse<InterfaceList>> GetSupportedInterfacesAsync(string orgCode = null)
        {
            try
            {
                var url = $"{_baseUrl}/api/interfaces";
                if (!string.IsNullOrEmpty(orgCode))
                {
                    url += $"?org_code={orgCode}";
                }

                var response = await _httpClient.GetAsync(url);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                var result = JsonSerializer.Deserialize<ApiResponse<InterfaceList>>(
                    responseJson, 
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    });

                return result;
            }
            catch (Exception ex)
            {
                return new ApiResponse<InterfaceList>
                {
                    Success = false,
                    Error = ex.Message,
                    Message = "获取接口列表失败"
                };
            }
        }

        /// <summary>
        /// 验证接口数据
        /// </summary>
        public async Task<ApiResponse<Dictionary<string, object>>> ValidateDataAsync(
            string apiCode, 
            Dictionary<string, object> data, 
            string orgCode)
        {
            var request = new InterfaceCallRequest
            {
                ApiCode = apiCode,
                Data = data,
                OrgCode = orgCode
            };

            var json = JsonSerializer.Serialize(request, new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });

            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            try
            {
                var response = await _httpClient.PostAsync($"{_baseUrl}/api/validate", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                var result = JsonSerializer.Deserialize<ApiResponse<Dictionary<string, object>>>(
                    responseJson, 
                    new JsonSerializerOptions
                    {
                        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                    });

                return result;
            }
            catch (Exception ex)
            {
                return new ApiResponse<Dictionary<string, object>>
                {
                    Success = false,
                    Error = ex.Message,
                    Message = "数据验证失败"
                };
            }
        }

        /// <summary>
        /// 检查服务健康状态
        /// </summary>
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_baseUrl}/health");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    // 数据模型
    public class InterfaceCallRequest
    {
        public string ApiCode { get; set; }
        public Dictionary<string, object> Data { get; set; }
        public string OrgCode { get; set; }
    }

    public class AsyncCallRequest : InterfaceCallRequest
    {
        public bool UseCelery { get; set; } = true;
    }

    public class BatchCallRequest
    {
        public List<InterfaceCallRequest> Requests { get; set; }
    }

    public class ApiResponse<T>
    {
        public bool Success { get; set; }
        public T Data { get; set; }
        public string Error { get; set; }
        public string Message { get; set; }
    }

    public class TaskInfo
    {
        public string TaskId { get; set; }
    }

    public class BatchResult
    {
        public List<Dictionary<string, object>> Results { get; set; }
    }

    public class InterfaceList
    {
        public List<Dictionary<string, object>> Interfaces { get; set; }
    }
}