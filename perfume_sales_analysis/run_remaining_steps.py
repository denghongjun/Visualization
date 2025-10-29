"""
运行剩余的分析步骤
"""

import subprocess
import time

def run_script(script_path, step_name):
    """运行单个脚本"""
    print("\n" + "=" * 80)
    print(f"执行: {step_name}")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ['python', script_path],
            capture_output=False,
            text=True,
            check=True
        )
        
        elapsed = time.time() - start_time
        print(f"\n✓ {step_name} 完成！耗时: {elapsed:.2f}秒")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {step_name} 失败！")
        print(f"错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("运行剩余分析步骤")
    print("=" * 80)
    
    steps = [
        ('scripts/03_data_warehouse.py', '数据仓库构建'),
        ('scripts/04_customer_segmentation.py', '客户细分分析'),
        ('scripts/05_association_rules.py', '关联规则挖掘'),
        ('scripts/06_visualization.py', '综合数据可视化'),
    ]
    
    results = []
    total_start = time.time()
    
    for script, name in steps:
        success = run_script(script, name)
        results.append((name, success))
        
        if not success:
            print("\n是否继续执行后续步骤？ (y/n)")
            choice = input("> ")
            if choice.lower() != 'y':
                break
    
    total_elapsed = time.time() - total_start
    
    # 打印摘要
    print("\n" + "=" * 80)
    print("执行摘要")
    print("=" * 80)
    
    for name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {name:30s} {status}")
    
    print("=" * 80)
    print(f"总耗时: {total_elapsed:.2f}秒 ({total_elapsed/60:.1f}分钟)")
    print("=" * 80)

if __name__ == '__main__':
    main()



