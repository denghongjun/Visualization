"""
数据仓库设计与构建脚本
实现星形模型（Star Schema）
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def create_dimension_customer(customers, rfm):
    """
    创建客户维度表
    
    参数:
        customers: 客户基础信息
        rfm: RFM分析结果
    
    返回:
        DataFrame: 客户维度表
    """
    print("\n创建客户维度表...")
    
    # 合并客户信息和RFM
    dim_customer = customers.merge(rfm[['客户ID', 'RFM_Score', 'RFM_Total']], 
                                   on='客户ID', how='left')
    
    # 创建客户分群标签
    def assign_customer_segment(row):
        if pd.isna(row['RFM_Total']):
            return '无交易'
        elif row['RFM_Total'] >= 10:
            return '高价值客户'
        elif row['RFM_Total'] >= 7:
            return '重要客户'
        elif row['RFM_Total'] >= 5:
            return '一般客户'
        else:
            return '低价值客户'
    
    dim_customer['客户分群'] = dim_customer.apply(assign_customer_segment, axis=1)
    
    # 添加年龄段
    def age_group(age):
        if age < 25:
            return '18-24岁'
        elif age < 35:
            return '25-34岁'
        elif age < 45:
            return '35-44岁'
        elif age < 55:
            return '45-54岁'
        else:
            return '55岁以上'
    
    dim_customer['年龄段'] = dim_customer['年龄'].apply(age_group)
    
    print(f"客户维度表创建完成：{len(dim_customer)} 条记录")
    print(f"维度字段: {list(dim_customer.columns)}")
    
    return dim_customer

def create_dimension_product(products):
    """
    创建产品维度表
    
    参数:
        products: 产品信息
    
    返回:
        DataFrame: 产品维度表
    """
    print("\n创建产品维度表...")
    
    dim_product = products.copy()
    
    # 添加价格档次
    def price_tier(price):
        if price < 800:
            return '经济型'
        elif price < 1200:
            return '中档'
        else:
            return '高档'
    
    dim_product['价格档次'] = dim_product['价格'].apply(price_tier)
    
    # 添加容量档次
    def volume_tier(volume):
        if volume <= 50:
            return '小容量'
        elif volume <= 75:
            return '中容量'
        else:
            return '大容量'
    
    dim_product['容量档次'] = dim_product['容量ml'].apply(volume_tier)
    
    print(f"产品维度表创建完成：{len(dim_product)} 条记录")
    print(f"维度字段: {list(dim_product.columns)}")
    
    return dim_product

def create_dimension_time(transactions):
    """
    创建时间维度表
    
    参数:
        transactions: 交易数据
    
    返回:
        DataFrame: 时间维度表
    """
    print("\n创建时间维度表...")
    
    # 获取所有唯一的日期
    dates = pd.DataFrame({'日期': transactions['交易日期'].unique()})
    dates['日期'] = pd.to_datetime(dates['日期'])
    dates = dates.sort_values('日期').reset_index(drop=True)
    
    # 添加时间维度属性
    dates['年份'] = dates['日期'].dt.year
    dates['季度'] = dates['日期'].dt.quarter
    dates['月份'] = dates['日期'].dt.month
    dates['周'] = dates['日期'].dt.isocalendar().week
    dates['日'] = dates['日期'].dt.day
    dates['星期几'] = dates['日期'].dt.dayofweek + 1  # 1=周一, 7=周日
    dates['星期名称'] = dates['日期'].dt.day_name()
    dates['月份名称'] = dates['日期'].dt.month_name()
    
    # 是否为周末
    dates['是否周末'] = dates['星期几'].apply(lambda x: '是' if x >= 6 else '否')
    
    # 是否为月初/月末
    dates['是否月初'] = dates['日'].apply(lambda x: '是' if x <= 10 else '否')
    dates['是否月末'] = dates['日'].apply(lambda x: '是' if x >= 20 else '否')
    
    # 季节
    def get_season(month):
        if month in [3, 4, 5]:
            return '春季'
        elif month in [6, 7, 8]:
            return '夏季'
        elif month in [9, 10, 11]:
            return '秋季'
        else:
            return '冬季'
    
    dates['季节'] = dates['月份'].apply(get_season)
    
    print(f"时间维度表创建完成：{len(dates)} 条记录")
    print(f"维度字段: {list(dates.columns)}")
    
    return dates

def create_dimension_campaign(campaigns):
    """
    创建营销活动维度表
    
    参数:
        campaigns: 营销活动信息
    
    返回:
        DataFrame: 营销活动维度表
    """
    print("\n创建营销活动维度表...")
    
    dim_campaign = campaigns.copy()
    
    # 添加活动持续天数
    dim_campaign['活动天数'] = (dim_campaign['结束日期'] - dim_campaign['开始日期']).dt.days + 1
    
    # 活动类型分类
    def campaign_type(name):
        if '情人节' in name or '七夕' in name:
            return '节日促销'
        elif '双十一' in name or '双十二' in name or '618' in name:
            return '电商大促'
        elif '新品' in name:
            return '新品推广'
        else:
            return '常规促销'
    
    dim_campaign['活动类型'] = dim_campaign['活动名称'].apply(campaign_type)
    
    # 折扣力度分类
    def discount_level(rate):
        if rate >= 0.2:
            return '大力度'
        elif rate >= 0.12:
            return '中等力度'
        else:
            return '小力度'
    
    dim_campaign['折扣力度'] = dim_campaign['折扣率'].apply(discount_level)
    
    print(f"营销活动维度表创建完成：{len(dim_campaign)} 条记录")
    print(f"维度字段: {list(dim_campaign.columns)}")
    
    return dim_campaign

def create_fact_sales(transactions, dim_customer, dim_product, dim_time, dim_campaign):
    """
    创建销售事实表
    
    参数:
        transactions: 交易数据
        dim_customer, dim_product, dim_time, dim_campaign: 维度表
    
    返回:
        DataFrame: 销售事实表
    """
    print("\n创建销售事实表...")
    
    fact_sales = transactions.copy()
    
    # 添加时间键（日期）
    fact_sales = fact_sales.rename(columns={'交易日期': '日期'})
    
    # 关联维度获取额外信息（用于后续分析）
    # 这里保持事实表的简洁性，主要存储度量值和外键
    
    # 选择事实表字段
    fact_columns = [
        '订单ID',
        '客户ID',      # 外键
        '产品ID',      # 外键
        '日期',        # 外键
        '活动ID',      # 外键
        '数量',        # 度量
        '单价',        # 度量
        '总金额',      # 度量
        '利润',        # 度量
        '折扣率'       # 度量
    ]
    
    fact_sales = fact_sales[fact_columns]
    
    print(f"销售事实表创建完成：{len(fact_sales)} 条记录")
    print(f"事实表字段: {list(fact_sales.columns)}")
    
    return fact_sales

def generate_star_schema_diagram():
    """
    生成星形模型结构说明
    """
    schema_description = """
    ╔════════════════════════════════════════════════════════════════════╗
    ║                         星形模型设计                                 ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    ┌─────────────────────┐
    │   客户维度表         │
    │  (DIM_CUSTOMER)     │
    ├─────────────────────┤
    │ 客户ID (PK)         │
    │ 性别                │
    │ 年龄                │
    │ 年龄段              │
    │ 城市                │
    │ 会员等级            │
    │ 注册日期            │
    │ 客户分群            │
    │ RFM_Score          │
    └──────────┬──────────┘
               │
               │
    ┌──────────▼──────────┐      ┌─────────────────────┐
    │   销售事实表         │      │   产品维度表         │
    │  (FACT_SALES)       │◄─────┤  (DIM_PRODUCT)      │
    ├─────────────────────┤      ├─────────────────────┤
    │ 订单ID (PK)         │      │ 产品ID (PK)         │
    │ 客户ID (FK)         │      │ 产品名称            │
    │ 产品ID (FK)         │      │ 品牌                │
    │ 日期 (FK)           │      │ 分类                │
    │ 活动ID (FK)         │      │ 容量ml              │
    │ 数量 (度量)         │      │ 价格                │
    │ 单价 (度量)         │      │ 价格档次            │
    │ 总金额 (度量)       │      │ 容量档次            │
    │ 利润 (度量)         │      └─────────────────────┘
    │ 折扣率 (度量)       │
    └──────────┬──────────┘
               │
               │
    ┌──────────▼──────────┐      ┌─────────────────────┐
    │   时间维度表         │      │  营销活动维度表      │
    │  (DIM_TIME)         │      │  (DIM_CAMPAIGN)     │
    ├─────────────────────┤      ├─────────────────────┤
    │ 日期 (PK)           │      │ 活动ID (PK)         │
    │ 年份                │      │ 活动名称            │
    │ 季度                │      │ 开始日期            │
    │ 月份                │      │ 结束日期            │
    │ 周                  │      │ 折扣率              │
    │ 日                  │      │ 活动天数            │
    │ 星期几              │      │ 活动类型            │
    │ 是否周末            │      │ 折扣力度            │
    │ 季节                │      └─────────────────────┘
    └─────────────────────┘
    
    说明：
    - PK: Primary Key (主键)
    - FK: Foreign Key (外键)
    - 事实表包含业务过程的度量值
    - 维度表提供分析的上下文和属性
    """
    
    return schema_description

def save_star_schema(dim_customer, dim_product, dim_time, dim_campaign, fact_sales):
    """
    保存星形模型各表
    """
    print("\n" + "=" * 60)
    print("保存星形模型...")
    print("=" * 60)
    
    # 创建数据仓库目录
    os.makedirs('data/warehouse', exist_ok=True)
    
    # 保存维度表
    dim_customer.to_csv('data/warehouse/dim_customer.csv', index=False, encoding='utf-8-sig')
    dim_product.to_csv('data/warehouse/dim_product.csv', index=False, encoding='utf-8-sig')
    dim_time.to_csv('data/warehouse/dim_time.csv', index=False, encoding='utf-8-sig')
    dim_campaign.to_csv('data/warehouse/dim_campaign.csv', index=False, encoding='utf-8-sig')
    
    # 保存事实表
    fact_sales.to_csv('data/warehouse/fact_sales.csv', index=False, encoding='utf-8-sig')
    
    print("星形模型保存完成！文件位于 data/warehouse/ 目录")
    
    # 保存模型结构说明
    schema_desc = generate_star_schema_diagram()
    with open('data/warehouse/star_schema_design.txt', 'w', encoding='utf-8') as f:
        f.write(schema_desc)
    
    print("\n星形模型结构:")
    print(schema_desc)

def main():
    """主函数"""
    print("=" * 60)
    print("开始构建数据仓库（星形模型）")
    print("=" * 60)
    
    # 加载处理后的数据
    print("\n加载处理后的数据...")
    customers = pd.read_csv('data/raw/customers.csv', encoding='utf-8-sig')
    products = pd.read_csv('data/raw/products.csv', encoding='utf-8-sig')
    campaigns = pd.read_csv('data/raw/marketing_campaigns.csv', encoding='utf-8-sig')
    transactions = pd.read_csv('data/processed/clean_transactions.csv', encoding='utf-8-sig')
    rfm = pd.read_csv('data/processed/rfm_analysis.csv', encoding='utf-8-sig')
    
    # 转换日期列
    customers['注册日期'] = pd.to_datetime(customers['注册日期'])
    campaigns['开始日期'] = pd.to_datetime(campaigns['开始日期'])
    campaigns['结束日期'] = pd.to_datetime(campaigns['结束日期'])
    transactions['交易日期'] = pd.to_datetime(transactions['交易日期'])
    
    # 创建维度表
    print("\n" + "=" * 60)
    print("创建维度表")
    print("=" * 60)
    
    dim_customer = create_dimension_customer(customers, rfm)
    dim_product = create_dimension_product(products)
    dim_time = create_dimension_time(transactions)
    dim_campaign = create_dimension_campaign(campaigns)
    
    # 创建事实表
    print("\n" + "=" * 60)
    print("创建事实表")
    print("=" * 60)
    
    fact_sales = create_fact_sales(transactions, dim_customer, dim_product, dim_time, dim_campaign)
    
    # 保存星形模型
    save_star_schema(dim_customer, dim_product, dim_time, dim_campaign, fact_sales)
    
    print("\n" + "=" * 60)
    print("数据仓库构建完成！")
    print("=" * 60)
    
    # 显示统计信息
    print("\n数据仓库统计:")
    print(f"  - 客户维度: {len(dim_customer)} 条")
    print(f"  - 产品维度: {len(dim_product)} 条")
    print(f"  - 时间维度: {len(dim_time)} 条")
    print(f"  - 营销活动维度: {len(dim_campaign)} 条")
    print(f"  - 销售事实: {len(fact_sales)} 条")

if __name__ == '__main__':
    main()



