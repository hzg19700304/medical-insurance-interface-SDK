"""
测试运行器
统一运行所有测试并生成报告
"""

import unittest
import sys
import os
import time
import argparse
from io import StringIO

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestResult:
    """测试结果统计"""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.start_time = None
        self.end_time = None
        self.failures = []
        self.errors = []
        self.test_details = []
    
    def add_test_result(self, test_name, status, duration, error_msg=None):
        """添加测试结果"""
        self.total_tests += 1
        self.test_details.append({
            'name': test_name,
            'status': status,
            'duration': duration,
            'error': error_msg
        })
        
        if status == 'PASS':
            self.passed_tests += 1
        elif status == 'FAIL':
            self.failed_tests += 1
            if error_msg:
                self.failures.append((test_name, error_msg))
        elif status == 'ERROR':
            self.error_tests += 1
            if error_msg:
                self.errors.append((test_name, error_msg))
        elif status == 'SKIP':
            self.skipped_tests += 1
    
    def get_success_rate(self):
        """获取成功率"""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def get_total_duration(self):
        """获取总耗时"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0


class CustomTestResult(unittest.TestResult):
    """自定义测试结果收集器"""
    
    def __init__(self, test_result: TestResult, verbose=False):
        super().__init__()
        self.test_result = test_result
        self.verbose = verbose
        self.current_test_start = None
    
    def startTest(self, test):
        """测试开始"""
        super().startTest(test)
        self.current_test_start = time.time()
        if self.verbose:
            print(f"运行测试: {test._testMethodName} ({test.__class__.__name__})")
    
    def addSuccess(self, test):
        """测试成功"""
        super().addSuccess(test)
        duration = time.time() - self.current_test_start if self.current_test_start else 0
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_result.add_test_result(test_name, 'PASS', duration)
        if self.verbose:
            print(f"  ✓ 通过 ({duration:.3f}s)")
    
    def addError(self, test, err):
        """测试错误"""
        super().addError(test, err)
        duration = time.time() - self.current_test_start if self.current_test_start else 0
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        error_msg = self._exc_info_to_string(err, test)
        self.test_result.add_test_result(test_name, 'ERROR', duration, error_msg)
        if self.verbose:
            print(f"  ✗ 错误 ({duration:.3f}s)")
    
    def addFailure(self, test, err):
        """测试失败"""
        super().addFailure(test, err)
        duration = time.time() - self.current_test_start if self.current_test_start else 0
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        error_msg = self._exc_info_to_string(err, test)
        self.test_result.add_test_result(test_name, 'FAIL', duration, error_msg)
        if self.verbose:
            print(f"  ✗ 失败 ({duration:.3f}s)")
    
    def addSkip(self, test, reason):
        """测试跳过"""
        super().addSkip(test, reason)
        duration = time.time() - self.current_test_start if self.current_test_start else 0
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        self.test_result.add_test_result(test_name, 'SKIP', duration, reason)
        if self.verbose:
            print(f"  - 跳过 ({reason})")


class TestRunner:
    """测试运行器"""
    
    def __init__(self, verbose=False, quiet=False):
        self.verbose = verbose
        self.quiet = quiet
        self.test_result = TestResult()
    
    def discover_tests(self, test_dir=None, pattern='test_*.py'):
        """发现测试用例"""
        if test_dir is None:
            test_dir = os.path.dirname(__file__)
        
        loader = unittest.TestLoader()
        suite = loader.discover(test_dir, pattern=pattern)
        return suite
    
    def run_specific_test(self, test_module=None, test_class=None, test_method=None):
        """运行特定测试"""
        if test_module:
            # 导入测试模块
            module_name = f"tests.{test_module}" if not test_module.startswith('tests.') else test_module
            try:
                __import__(module_name)
                module = sys.modules[module_name]
            except ImportError as e:
                print(f"无法导入测试模块 {module_name}: {e}")
                return None
            
            loader = unittest.TestLoader()
            
            if test_class and test_method:
                # 运行特定测试方法
                suite = loader.loadTestsFromName(f"{test_class}.{test_method}", module)
            elif test_class:
                # 运行特定测试类
                suite = loader.loadTestsFromName(test_class, module)
            else:
                # 运行整个模块
                suite = loader.loadTestsFromModule(module)
            
            return suite
        
        return None
    
    def run_tests(self, test_suite):
        """运行测试套件"""
        if not test_suite:
            print("没有找到测试用例")
            return self.test_result
        
        # 统计测试数量
        test_count = test_suite.countTestCases()
        if not self.quiet:
            print(f"发现 {test_count} 个测试用例")
            print("=" * 70)
        
        # 创建自定义测试结果收集器
        result_collector = CustomTestResult(self.test_result, self.verbose)
        
        # 记录开始时间
        self.test_result.start_time = time.time()
        
        # 运行测试
        test_suite.run(result_collector)
        
        # 记录结束时间
        self.test_result.end_time = time.time()
        
        return self.test_result
    
    def print_summary(self, test_result):
        """打印测试摘要"""
        if self.quiet:
            return
        
        print("\n" + "=" * 70)
        print("测试摘要")
        print("=" * 70)
        
        # 基本统计
        print(f"总测试数: {test_result.total_tests}")
        print(f"通过: {test_result.passed_tests}")
        print(f"失败: {test_result.failed_tests}")
        print(f"错误: {test_result.error_tests}")
        print(f"跳过: {test_result.skipped_tests}")
        print(f"成功率: {test_result.get_success_rate():.1f}%")
        print(f"总耗时: {test_result.get_total_duration():.3f}秒")
        
        # 失败详情
        if test_result.failures:
            print("\n失败的测试:")
            print("-" * 50)
            for test_name, error_msg in test_result.failures:
                print(f"FAIL: {test_name}")
                print(f"  {error_msg.split(chr(10))[0]}")  # 只显示第一行错误信息
        
        # 错误详情
        if test_result.errors:
            print("\n错误的测试:")
            print("-" * 50)
            for test_name, error_msg in test_result.errors:
                print(f"ERROR: {test_name}")
                print(f"  {error_msg.split(chr(10))[0]}")  # 只显示第一行错误信息
        
        # 详细结果（仅在verbose模式下）
        if self.verbose and test_result.test_details:
            print("\n详细测试结果:")
            print("-" * 50)
            for detail in test_result.test_details:
                status_symbol = {
                    'PASS': '✓',
                    'FAIL': '✗',
                    'ERROR': '✗',
                    'SKIP': '-'
                }.get(detail['status'], '?')
                
                print(f"{status_symbol} {detail['name']} ({detail['duration']:.3f}s)")
                if detail['error'] and self.verbose:
                    print(f"    {detail['error'].split(chr(10))[0]}")
    
    def print_test_coverage(self):
        """打印测试覆盖范围"""
        if self.quiet:
            return
        
        print("\n" + "=" * 70)
        print("测试覆盖范围")
        print("=" * 70)
        
        coverage_info = {
            "核心组件": [
                "UniversalInterfaceProcessor - 通用接口处理器",
                "DataValidator - 数据验证器", 
                "ConfigManager - 配置管理器",
                "CacheManager - 缓存管理器",
                "DataHelper - 数据处理辅助工具"
            ],
            "功能覆盖": [
                "接口调用流程",
                "数据验证和转换",
                "配置管理和缓存",
                "错误处理和异常管理",
                "批量操作",
                "并发处理",
                "数据库操作"
            ],
            "测试类型": [
                "单元测试 - 测试单个组件功能",
                "集成测试 - 测试组件间协作",
                "异常测试 - 测试错误处理",
                "性能测试 - 测试并发和缓存性能"
            ]
        }
        
        for category, items in coverage_info.items():
            print(f"\n{category}:")
            for item in items:
                print(f"  ✓ {item}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='医保接口SDK测试运行器')
    parser.add_argument('--test', help='指定测试模块名称')
    parser.add_argument('--class', dest='test_class', help='指定测试类名称')
    parser.add_argument('--method', dest='test_method', help='指定测试方法名称')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--coverage', action='store_true', help='显示测试覆盖范围')
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = TestRunner(verbose=args.verbose, quiet=args.quiet)
    
    # 显示测试覆盖范围
    if args.coverage:
        runner.print_test_coverage()
        return
    
    # 获取测试套件
    if args.test:
        test_suite = runner.run_specific_test(args.test, args.test_class, args.test_method)
        if not test_suite:
            print(f"未找到测试: {args.test}")
            return
    else:
        test_suite = runner.discover_tests()
    
    # 运行测试
    if not args.quiet:
        print("医保接口SDK单元测试")
        print("=" * 70)
    
    test_result = runner.run_tests(test_suite)
    
    # 打印摘要
    runner.print_summary(test_result)
    
    # 返回退出码
    if test_result.failed_tests > 0 or test_result.error_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()