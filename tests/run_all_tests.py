# tests/run_all_tests.py - 运行所有测试
"""
运行所有测试
"""

import sys
import os

# Fix Unicode emoji output on Windows GBK terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def _run_pytest_module(module_name: str) -> bool:
    """通过 pytest 方式运行一个测试模块，返回是否全部通过。"""
    import subprocess
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{module_name}.py",
        "-v",
        "--override-ini=addopts=-v",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    print(output)
    return result.returncode == 0


def run_tests():
    """运行所有测试"""
    print("🚀 开始运行 Life K-Line Engine 所有测试")
    print("=" * 70)

    # 导入并运行各个测试模块
    test_modules = [
        ('基础功能测试', 'test_basic', 'run_all_tests'),
        ('尊贵度计算测试', 'test_dignities', 'run_dignities_tests'),
        ('集成测试', 'test_integration', 'run_integration_tests'),
        ('星灵触发重构测试', 'test_spirit_trigger_refactor', None),
    ]

    all_passed = True
    results = []

    for test_name, module_name, func_name in test_modules:
        print(f"\n📋 运行 {test_name}...")
        print("-" * 50)

        try:
            if func_name is None:
                # 通过 pytest 运行（适合 pytest 风格用例）
                passed = _run_pytest_module(module_name)
            else:
                # 动态导入测试模块
                module = __import__(module_name)

                # 运行测试函数
                if hasattr(module, func_name):
                    passed = getattr(module, func_name)()
                elif hasattr(module, 'run_all_tests'):
                    passed = module.run_all_tests()
                else:
                    print(f"❓ 未找到测试运行函数")
                    passed = False

            if passed:
                results.append(f"✅ {test_name}: 通过")
            else:
                results.append(f"❌ {test_name}: 失败")
                all_passed = False

        except ImportError as e:
            print(f"❌ 无法导入测试模块 {module_name}: {e}")
            results.append(f"❌ {test_name}: 导入失败")
            all_passed = False
        except Exception as e:
            print(f"❌ 测试运行异常: {e}")
            import traceback
            traceback.print_exc()
            results.append(f"❌ {test_name}: 异常")
            all_passed = False
    
    # 打印总结
    print("\n" + "=" * 70)
    print("测试总结:")
    print("=" * 70)
    
    for result in results:
        print(result)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有测试通过！系统运行正常。")
    else:
        print("⚠️  部分测试失败，请检查问题。")
    
    return all_passed


if __name__ == "__main__":
    # 添加当前目录到Python路径
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    success = run_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)