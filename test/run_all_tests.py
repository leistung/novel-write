#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有测试
"""

import os
import sys
import subprocess

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test(test_file):
    """运行单个测试文件"""
    print(f"\n{'='*60}")
    print(f"运行测试: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        print(f"测试完成，返回码: {result.returncode}")
    except Exception as e:
        print(f"运行测试失败: {str(e)}")


def run_all_tests():
    """运行所有测试"""
    print("开始运行所有测试...")
    
    # 获取测试文件列表
    test_files = [
        "test_llm.py",
        "test_database.py",
        "test_export.py",
        "test_pipeline.py",
        "test_full_workflow.py"
    ]
    
    # 运行每个测试文件
    for test_file in test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            run_test(test_path)
        else:
            print(f"测试文件不存在: {test_file}")
    
    print(f"\n{'='*60}")
    print("所有测试运行完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_all_tests()
