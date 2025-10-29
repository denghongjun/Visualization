"""
真实数据分析主程序
使用用户提供的真实数据执行完整的分析流程
"""

import os
import sys
import time
from datetime import datetime

def print_banner():
    """打印程序横幅"""
    banner = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║         香水销售客户与营销数据行为分析与决策支持系统             ║
    ║                    (基于真实数据集)                             ║
    ║                                                                ║
    ║              Data Warehouse and Data Mining Project            ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    
    作者: 邓宏军
    学号: 2024302726
    班级: 数据科学与大数据技术 1班
    日期: {}
    
    数据来源: 真实业务数据集
    
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    print(banner)

def run_step(step_num, step_name, script_path):
    """
    执行单个步骤
    """
    print("\n" + "=" * 80)
    print(f"步骤 {step_num}: {step_name}")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 执行脚本
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        exec(code, {'__name__': '__main__'})
        
        elapsed_time = time.time() - start_time
        print(f"\n✓ 步骤 {step_num} 完成！耗时: {elapsed_time:.2f} 秒")
        return True
        
    except Exception as e:
        print(f"\n✗ 步骤 {step_num} 失败！")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查数据文件是否存在
    required_files = [
        '数据/香水.xlsx',
        '数据/申请客户信息.xlsx',
        '数据/消费历史记录.xlsx',
        '数据/客户信用记录.xlsx',
        '数据/拖欠历史记录.xlsx'
    ]
    
    print("=" * 80)
    print("检查数据文件...")
    print("=" * 80)
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (缺失)")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n错误: 缺少{len(missing_files)}个必需的数据文件")
        print("请确保所有数据文件都在'数据'目录下")
        return
    
    # 定义执行步骤
    steps = [
        (1, "真实数据预处理与转换", "scripts/01_real_data_preprocessing.py"),
        (2, "数据清洗与特征工程（RFM分析）", "scripts/02_data_preprocessing.py"),
        (3, "数据仓库构建（星形模型）", "scripts/03_data_warehouse.py"),
        (4, "客户细分分析（K-Means聚类）", "scripts/04_customer_segmentation.py"),
        (5, "关联规则挖掘（Apriori算法）", "scripts/05_association_rules.py"),
        (6, "综合数据可视化", "scripts/06_visualization.py"),
    ]
    
    print("\n" + "=" * 80)
    print("分析流程包含以下步骤:")
    print("=" * 80)
    for num, name, _ in steps:
        print(f"  {num}. {name}")
    
    print("\n" + "=" * 80)
    choice = input("是否开始执行分析流程？ (y/n): ")
    if choice.lower() != 'y':
        print("已取消")
        return
    print("=" * 80)
    
    # 记录开始时间
    total_start_time = time.time()
    
    # 执行所有步骤
    results = []
    for step_num, step_name, script_path in steps:
        success = run_step(step_num, step_name, script_path)
        results.append((step_num, step_name, success))
        
        if not success:
            print(f"\n警告: 步骤 {step_num} 执行失败")
            choice = input("是否继续执行后续步骤？ (y/n): ")
            if choice.lower() != 'y':
                print("分析流程已终止")
                break
    
    # 计算总耗时
    total_elapsed_time = time.time() - total_start_time
    
    # 打印执行摘要
    print("\n" + "=" * 80)
    print("执行摘要")
    print("=" * 80)
    
    for step_num, step_name, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {step_num}. {step_name:50s} {status}")
    
    print("=" * 80)
    print(f"总耗时: {total_elapsed_time:.2f} 秒 ({total_elapsed_time/60:.1f} 分钟)")
    
    # 统计成功和失败的步骤
    success_count = sum(1 for _, _, success in results if success)
    total_count = len(results)
    
    print(f"完成率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    print("=" * 80)
    
    # 显示输出文件位置
    print("\n" + "=" * 80)
    print("输出文件位置:")
    print("=" * 80)
    print("  📁 data/raw/          - 转换后的原始数据")
    print("  📁 data/processed/    - 预处理后的数据")
    print("  📁 data/warehouse/    - 数据仓库（星形模型）")
    print("  📁 output/            - 分析结果（CSV文件）")
    print("  📁 figures/           - 可视化图表（PNG/HTML）")
    
    print("\n" + "=" * 80)
    print("关键输出文件:")
    print("=" * 80)
    print("  📊 figures/optimal_k_selection.png              - K值选择图")
    print("  📊 figures/clustering_kmeans_visualization.png  - 聚类可视化")
    print("  📊 figures/cluster_heatmap.png                  - 客户特征热力图")
    print("  📊 figures/association_rules_analysis.png       - 关联规则分析")
    print("  📊 figures/sales_overview.png                   - 销售概览")
    print("  📊 figures/interactive_dashboard.html           - 交互式仪表板")
    print("  📄 output/customer_segmentation_results.csv     - 客户细分结果")
    print("  📄 output/association_rules.csv                 - 关联规则")
    
    if success_count == total_count:
        print("\n" + "=" * 80)
        print("🎉 恭喜！所有分析步骤已成功完成！")
        print("=" * 80)
        print("\n您现在可以：")
        print("  1. 查看 figures/ 目录中的可视化图表")
        print("  2. 打开 figures/interactive_dashboard.html 查看交互式仪表板")
        print("  3. 阅读 output/ 目录中的分析结果文件")
        print("  4. 参考'课程设计报告.md'撰写最终报告")

if __name__ == '__main__':
    main()



