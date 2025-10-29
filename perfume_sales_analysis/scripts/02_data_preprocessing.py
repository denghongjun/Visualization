"""
数据预处理脚本
包括数据清洗、转换和特征工程（RFM分析）
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_data():
    """加载原始数据"""
    print("正在加载数据...")
    
    customers = pd.read_csv('data/raw/customers.csv', encoding='utf-8-sig')
    products = pd.read_csv('data/raw/products.csv', encoding='utf-8-sig')
    campaigns = pd.read_csv('data/raw/marketing_campaigns.csv', encoding='utf-8-sig')
    transactions = pd.read_csv('data/raw/sales_transactions.csv', encoding='utf-8-sig')
    
    # 转换日期列
    customers['注册日期'] = pd.to_datetime(customers['注册日期'])
    campaigns['开始日期'] = pd.to_datetime(campaigns['开始日期'])
    campaigns['结束日期'] = pd.to_datetime(campaigns['结束日期'])
    transactions['交易日期'] = pd.to_datetime(transactions['交易日期'])
    
    print("数据加载完成！")
    return customers, products, campaigns, transactions

def data_quality_check(df, df_name):
    """
    数据质量检查
    
    参数:
        df: 数据框
        df_name: 数据框名称
    """
    print(f"\n{df_name} 数据质量检查:")
    print(f"  - 总行数: {len(df)}")
    print(f"  - 总列数: {len(df.columns)}")
    print(f"  - 缺失值:")
    
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("    无缺失值")
    else:
        print(missing[missing > 0])
    
    print(f"  - 重复行数: {df.duplicated().sum()}")

def clean_data(customers, products, campaigns, transactions):
    """
    数据清洗
    
    参数:
        customers, products, campaigns, transactions: 原始数据框
    
    返回:
        清洗后的数据框
    """
    print("\n" + "=" * 60)
    print("开始数据清洗...")
    print("=" * 60)
    
    # 检查数据质量
    data_quality_check(customers, "客户数据")
    data_quality_check(products, "产品数据")
    data_quality_check(campaigns, "营销活动数据")
    data_quality_check(transactions, "销售交易数据")
    
    # 删除重复行
    customers = customers.drop_duplicates(subset=['客户ID'])
    products = products.drop_duplicates(subset=['产品ID'])
    transactions = transactions.drop_duplicates(subset=['订单ID'])
    
    # 处理异常值（示例：价格和数量不能为负）
    transactions = transactions[transactions['总金额'] > 0]
    transactions = transactions[transactions['数量'] > 0]
    
    print("\n数据清洗完成！")
    return customers, products, campaigns, transactions

def calculate_rfm(transactions, reference_date=None):
    """
    计算RFM指标
    
    参数:
        transactions: 交易数据
        reference_date: 参考日期（用于计算Recency）
    
    返回:
        DataFrame: 包含RFM指标的客户数据
    """
    print("\n" + "=" * 60)
    print("开始计算RFM指标...")
    print("=" * 60)
    
    if reference_date is None:
        reference_date = transactions['交易日期'].max()
    
    print(f"参考日期: {reference_date}")
    
    # 按客户分组计算RFM
    rfm = transactions.groupby('客户ID').agg({
        '交易日期': lambda x: (reference_date - x.max()).days,  # Recency
        '订单ID': 'count',  # Frequency
        '总金额': 'sum'  # Monetary
    }).reset_index()
    
    rfm.columns = ['客户ID', 'Recency', 'Frequency', 'Monetary']
    
    # 计算额外的特征
    # 平均订单金额
    avg_order = transactions.groupby('客户ID')['总金额'].mean().reset_index()
    avg_order.columns = ['客户ID', '平均订单金额']
    
    # 购买的不同产品数量
    product_variety = transactions.groupby('客户ID')['产品ID'].nunique().reset_index()
    product_variety.columns = ['客户ID', '产品多样性']
    
    # 参与营销活动次数
    campaign_participation = transactions[transactions['活动ID'].notna()].groupby('客户ID').size().reset_index()
    campaign_participation.columns = ['客户ID', '活动参与次数']
    
    # 合并所有特征
    rfm = rfm.merge(avg_order, on='客户ID', how='left')
    rfm = rfm.merge(product_variety, on='客户ID', how='left')
    rfm = rfm.merge(campaign_participation, on='客户ID', how='left')
    
    # 填充缺失值
    rfm['活动参与次数'] = rfm['活动参与次数'].fillna(0)
    
    # 计算RFM评分（使用四分位数）
    # 使用try-except处理可能的重复值问题
    try:
        rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1], duplicates='drop')
    except ValueError:
        # 如果无法分成4组，使用cut方法
        rfm['R_Score'] = pd.cut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
    
    try:
        rfm['F_Score'] = pd.qcut(rfm['Frequency'], 4, labels=[1, 2, 3, 4], duplicates='drop')
    except ValueError:
        rfm['F_Score'] = pd.cut(rfm['Frequency'], 4, labels=[1, 2, 3, 4])
    
    try:
        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4], duplicates='drop')
    except ValueError:
        rfm['M_Score'] = pd.cut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])
    
    # 计算总分
    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    rfm['RFM_Total'] = rfm['R_Score'].astype(int) + rfm['F_Score'].astype(int) + rfm['M_Score'].astype(int)
    
    print(f"\nRFM指标计算完成！共 {len(rfm)} 个客户")
    print("\nRFM统计信息:")
    print(rfm[['Recency', 'Frequency', 'Monetary']].describe())
    
    return rfm

def create_customer_features(customers, rfm, transactions):
    """
    创建客户特征数据集
    
    参数:
        customers: 客户基础信息
        rfm: RFM数据
        transactions: 交易数据
    
    返回:
        DataFrame: 完整的客户特征数据
    """
    print("\n创建客户特征数据集...")
    
    # 合并客户基础信息和RFM
    customer_features = customers.merge(rfm, on='客户ID', how='left')
    
    # 填充没有交易的客户的RFM值
    customer_features['Recency'] = customer_features['Recency'].fillna(999)
    customer_features['Frequency'] = customer_features['Frequency'].fillna(0)
    customer_features['Monetary'] = customer_features['Monetary'].fillna(0)
    customer_features['平均订单金额'] = customer_features['平均订单金额'].fillna(0)
    customer_features['产品多样性'] = customer_features['产品多样性'].fillna(0)
    customer_features['活动参与次数'] = customer_features['活动参与次数'].fillna(0)
    
    # 计算客户生命周期（天数）
    reference_date = transactions['交易日期'].max()
    customer_features['客户生命周期'] = (reference_date - customer_features['注册日期']).dt.days
    
    print(f"客户特征数据集创建完成！共 {len(customer_features)} 条记录")
    
    return customer_features

def create_product_features(products, transactions):
    """
    创建产品特征数据集
    
    参数:
        products: 产品基础信息
        transactions: 交易数据
    
    返回:
        DataFrame: 完整的产品特征数据
    """
    print("\n创建产品特征数据集...")
    
    # 按产品统计销售信息
    product_stats = transactions.groupby('产品ID').agg({
        '订单ID': 'count',
        '数量': 'sum',
        '总金额': 'sum',
        '利润': 'sum'
    }).reset_index()
    
    product_stats.columns = ['产品ID', '销售次数', '销售数量', '销售额', '总利润']
    
    # 合并产品基础信息
    product_features = products.merge(product_stats, on='产品ID', how='left')
    
    # 填充缺失值
    product_features['销售次数'] = product_features['销售次数'].fillna(0)
    product_features['销售数量'] = product_features['销售数量'].fillna(0)
    product_features['销售额'] = product_features['销售额'].fillna(0)
    product_features['总利润'] = product_features['总利润'].fillna(0)
    
    print(f"产品特征数据集创建完成！共 {len(product_features)} 条记录")
    
    return product_features

def main():
    """主函数"""
    print("=" * 60)
    print("开始数据预处理和特征工程")
    print("=" * 60)
    
    # 加载数据
    customers, products, campaigns, transactions = load_data()
    
    # 数据清洗
    customers, products, campaigns, transactions = clean_data(
        customers, products, campaigns, transactions
    )
    
    # 计算RFM指标
    rfm = calculate_rfm(transactions)
    
    # 创建客户特征数据集
    customer_features = create_customer_features(customers, rfm, transactions)
    
    # 创建产品特征数据集
    product_features = create_product_features(products, transactions)
    
    # 保存处理后的数据
    print("\n" + "=" * 60)
    print("保存处理后的数据...")
    print("=" * 60)
    
    customer_features.to_csv('data/processed/customer_features.csv', index=False, encoding='utf-8-sig')
    product_features.to_csv('data/processed/product_features.csv', index=False, encoding='utf-8-sig')
    rfm.to_csv('data/processed/rfm_analysis.csv', index=False, encoding='utf-8-sig')
    transactions.to_csv('data/processed/clean_transactions.csv', index=False, encoding='utf-8-sig')
    
    print("\n数据预处理完成！文件已保存到 data/processed/ 目录")
    
    # 显示特征数据示例
    print("\n客户特征数据示例:")
    print(customer_features.head())
    
    print("\n产品特征数据示例:")
    print(product_features.head())

if __name__ == '__main__':
    main()

