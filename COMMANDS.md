# 常用命令快速参考

## 开发环境

### 激活虚拟环境
```powershell
# Windows
venv\Scripts\activate

# Linux/Mac  
source venv/bin/activate
```

### 安装依赖
```bash
pip install -r requirements.txt
pip install -e .
```

## 代码质量

### 格式化代码
```bash
black medical_insurance_sdk/
```

### 代码检查
```bash
flake8 medical_insurance_sdk/
```

### 类型检查
```bash
mypy medical_insurance_sdk/
```

## 测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试
```bash
pytest tests/test_basic.py -v
```

### 测试覆盖率
```bash
pytest tests/ --cov=medical_insurance_sdk --cov-report=html
```

## 项目管理

### 查看项目结构
```bash
tree medical_insurance_sdk/  # Linux/Mac
# 或使用IDE的文件浏览器
```

### 检查依赖
```bash
pip list
pip show medical-insurance-sdk
```

## 数据库

### 测试数据库连接
```python
from medical_insurance_sdk.core.database import DatabaseConfig, DatabaseManager

config = DatabaseConfig.from_env()
db_manager = DatabaseManager(config)
print(db_manager.test_connection())
```

## 文档

- 详细命令记录: [docs/setup-commands.md](docs/setup-commands.md)
- 项目文档: [docs/README.md](docs/README.md)
- 主要文档: [README.md](README.md)

## 快速验证

验证项目设置是否正确：

```bash
# 1. 激活虚拟环境
venv\Scripts\activate

# 2. 运行测试
pytest tests/ -v

# 3. 验证导入
python -c "from medical_insurance_sdk import MedicalInsuranceClient; print('导入成功')"

# 4. 检查代码格式
black --check medical_insurance_sdk/
```

如果所有命令都成功执行，说明项目环境配置正确。