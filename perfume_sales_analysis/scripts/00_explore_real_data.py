"""
探索真实数据集脚本
读取并分析用户提供的Excel数据文件
"""

import pandas as pd
import os

def explore_excel_file(file_path, file_name):
    """探索单个Excel文件"""
    print("\n" + "=" * 80)
    print(f"文件: {file_name}")
    print("=" * 80)
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 基本信息
        print(f"\n数据形状: {df.shape[0]} 行 x {df.shape[1]} 列")
        print(f"\n列名:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        # 数据类型
        print(f"\n数据类型:")
        print(df.dtypes)
        
        # 缺失值
        print(f"\n缺失值统计:")
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(missing[missing > 0])
        else:
            print("  无缺失值")
        
        # 前几行数据
        print(f"\n数据预览（前5行）:")
        print(df.head())
        
        # 数值型列的统计信息
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            print(f"\n数值列统计:")
            print(df[numeric_cols].describe())
        
        return df
        
    except Exception as e:
        print(f"读取文件失败: {e}")
        return None

def main():
    """主函数"""
    print("=" * 80)
    print("探索真实数据集")
    print("=" * 80)
    
    # 数据文件路径
    data_dir = "数据"
    files = {
        '香水': '香水.xlsx',
        '申请客户信息': '申请客户信息.xlsx',
        '消费历史记录': '消费历史记录.xlsx',
        '客户信用记录': '客户信用记录.xlsx',
        '拖欠历史记录': '拖欠历史记录.xlsx'
    }
    
    # 存储读取的数据
    datasets = {}
    
    # 读取所有文件
    for name, filename in files.items():
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            df = explore_excel_file(file_path, name)
            if df is not None:
                datasets[name] = df
        else:
            print(f"\n文件不存在: {file_path}")
    
    # 数据关系分析
    print("\n" + "=" * 80)
    print("数据关系分析")
    print("=" * 80)
    
    # 分析可能的关联字段
    if datasets:
        print("\n各数据集的关键字段:")
        for name, df in datasets.items():
            print(f"\n{name}:")
            # 查找可能的ID字段
            id_cols = [col for col in df.columns if 'ID' in col.upper() or '编号' in col or '代码' in col]
            if id_cols:
                print(f"  可能的关键字段: {id_cols}")
                for col in id_cols:
                    print(f"    - {col}: {df[col].nunique()} 个唯一值")
    
    print("\n" + "=" * 80)
    print("数据探索完成！")
    print("=" * 80)
    
    return datasets

if __name__ == '__main__':
    datasets = main()



