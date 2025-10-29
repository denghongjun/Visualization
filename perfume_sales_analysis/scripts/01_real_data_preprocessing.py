"""
真实数据预处理脚本
将用户提供的真实数据集转换为香水销售分析所需的格式
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def load_real_data():
    """加载真实数据集"""
    print("=" * 80)
    print("加载真实数据集")
    print("=" * 80)
    
    # 读取所有数据文件
    perfumes = pd.read_excel('数据/香水.xlsx')
    customers_apply = pd.read_excel('数据/申请客户信息.xlsx')
    consumption = pd.read_excel('数据/消费历史记录.xlsx')
    credit = pd.read_excel('数据/客户信用记录.xlsx')
    overdue = pd.read_excel('数据/拖欠历史记录.xlsx')
    
    print(f"✓ 香水产品数据: {len(perfumes)} 条")
    print(f"✓ 申请客户信息: {len(customers_apply)} 条")
    print(f"✓ 消费历史记录: {len(consumption)} 条")
    print(f"✓ 客户信用记录: {len(credit)} 条")
    print(f"✓ 拖欠历史记录: {len(overdue)} 条")
    
    return perfumes, customers_apply, consumption, credit, overdue

def process_customer_data(customers_apply, credit):
    """
    处理客户数据
    整合申请客户信息和信用记录
    """
    print("\n" + "=" * 80)
    print("处理客户数据")
    print("=" * 80)
    
    # 从信用记录中获取有实际交易的客户
    active_customers = credit[['客户号', '客户姓名', '性别', '年龄_连续', 
                              '婚姻状态', '户籍', '教育程度', '信用等级',
                              '个人收入_连续', '工作年限']].copy()
    
    # 重命名列
    active_customers.columns = ['客户ID', '客户姓名', '性别', '年龄', 
                                '婚姻状态', '城市', '教育程度', '会员等级',
                                '个人年收入', '工作年限']
    
    # 生成注册日期（随机分配在过去2年内）
    np.random.seed(42)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 1, 1)
    date_range = (end_date - start_date).days
    
    active_customers['注册日期'] = [
        start_date + timedelta(days=np.random.randint(0, date_range))
        for _ in range(len(active_customers))
    ]
    
    # 转换客户ID为字符串格式
    active_customers['客户ID'] = 'C' + active_customers['客户ID'].astype(str)
    
    print(f"处理完成：{len(active_customers)} 个活跃客户")
    print(f"\n客户数据预览:")
    print(active_customers.head())
    
    return active_customers

def process_product_data(perfumes):
    """
    处理产品数据
    从香水数据集中提取核心产品信息
    """
    print("\n" + "=" * 80)
    print("处理产品数据")
    print("=" * 80)
    
    # 选择有价格的产品，去除异常值
    valid_perfumes = perfumes[
        (perfumes['价格'].notna()) & 
        (perfumes['价格'] > 0) & 
        (perfumes['价格'] < 3000)
    ].copy()
    
    # 随机选择部分产品作为主要销售产品
    np.random.seed(42)
    if len(valid_perfumes) > 50:
        products = valid_perfumes.sample(n=50, random_state=42).reset_index(drop=True)
    else:
        products = valid_perfumes.reset_index(drop=True)
    
    # 创建产品表
    products_df = pd.DataFrame({
        '产品ID': ['P' + str(i+1).zfill(3) for i in range(len(products))],
        '产品名称': products['商品名称'].values,
        '品牌': products['商品名称'].str.extract(r'([\u4e00-\u9fa5]+)')[0].fillna('其他品牌').values,
        '分类': products['性别'].fillna('中性香水').values,
        '容量ml': products['净含量'].str.extract(r'(\d+)')[0].fillna(50).astype(int).values,
        '价格': products['价格'].values,
        '评价数': products['评价'].fillna(0).astype(int).values,
        '适用场合数': products['适用场合数量'].fillna(3).astype(int).values
    })
    
    print(f"处理完成：{len(products_df)} 个产品")
    print(f"\n产品数据预览:")
    print(products_df.head(10))
    
    return products_df

def generate_transactions(customers, products, consumption):
    """
    生成销售交易数据
    基于消费历史记录生成香水购买交易
    """
    print("\n" + "=" * 80)
    print("生成销售交易数据")
    print("=" * 80)
    
    transactions = []
    
    # 为每个有消费记录的客户生成交易
    customer_ids = customers['客户ID'].tolist()
    
    # 设置随机种子
    np.random.seed(42)
    
    # 时间范围
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 9, 30)
    date_range = (end_date - start_date).days
    
    order_id = 1
    
    # 遍历消费记录
    for idx, row in consumption.iterrows():
        customer_id_num = row['客户号']
        customer_id = 'C' + str(customer_id_num)
        
        # 只处理在客户列表中的客户
        if customer_id not in customer_ids:
            continue
        
        # 根据日均次数生成交易次数（模拟）
        avg_freq = row['日均次数']
        # 假设记录了3个月的数据，计算总交易次数
        num_transactions = max(1, int(avg_freq * 90 / 30))  # 转换为大约的月度交易
        num_transactions = min(num_transactions, 20)  # 限制最大交易次数
        
        # 日均消费金额
        avg_amount = row['日均消费金额']
        min_amount = row['单笔消费最小金额']
        max_amount = row['单笔消费最大金额']
        
        # 生成该客户的多笔交易
        for _ in range(num_transactions):
            # 随机选择产品
            product = products.sample(n=1).iloc[0]
            product_id = product['产品ID']
            product_price = product['价格']
            
            # 生成交易日期
            transaction_date = start_date + timedelta(days=np.random.randint(0, date_range))
            
            # 计算数量（大多数情况买1件）
            quantity = np.random.choice([1, 2], p=[0.9, 0.1])
            
            # 计算金额（基于产品价格，添加一些随机性）
            price_factor = np.random.uniform(0.8, 1.2)
            unit_price = round(product_price * price_factor, 2)
            total_amount = round(unit_price * quantity, 2)
            
            # 计算利润（假设利润率30-50%）
            profit_rate = np.random.uniform(0.3, 0.5)
            profit = round(total_amount * profit_rate, 2)
            
            transaction = {
                '订单ID': f'O{str(order_id).zfill(8)}',
                '客户ID': customer_id,
                '产品ID': product_id,
                '交易日期': transaction_date,
                '数量': quantity,
                '单价': unit_price,
                '总金额': total_amount,
                '利润': profit,
                '活动ID': None,  # 先不设置活动
                '折扣率': 0.0
            }
            
            transactions.append(transaction)
            order_id += 1
    
    transactions_df = pd.DataFrame(transactions)
    
    print(f"生成完成：{len(transactions_df)} 条交易记录")
    print(f"涉及客户数：{transactions_df['客户ID'].nunique()}")
    print(f"涉及产品数：{transactions_df['产品ID'].nunique()}")
    print(f"\n交易数据预览:")
    print(transactions_df.head(10))
    
    return transactions_df

def add_marketing_campaigns(transactions):
    """
    添加营销活动标识
    """
    print("\n" + "=" * 80)
    print("添加营销活动信息")
    print("=" * 80)
    
    # 创建营销活动
    campaigns = pd.DataFrame([
        {'活动ID': 'M001', '活动名称': '春季新品促销', '开始日期': '2023-03-01', '结束日期': '2023-03-31', '折扣率': 0.15},
        {'活动ID': 'M002', '活动名称': '618年中大促', '开始日期': '2023-06-01', '结束日期': '2023-06-18', '折扣率': 0.20},
        {'活动ID': 'M003', '活动名称': '七夕情人节', '开始日期': '2023-08-15', '结束日期': '2023-08-22', '折扣率': 0.10},
        {'活动ID': 'M004', '活动名称': '双十一狂欢', '开始日期': '2023-11-01', '结束日期': '2023-11-11', '折扣率': 0.25},
        {'活动ID': 'M005', '活动名称': '双十二盛典', '开始日期': '2023-12-01', '结束日期': '2023-12-12', '折扣率': 0.18},
        {'活动ID': 'M006', '活动名称': '新年特惠', '开始日期': '2024-01-01', '结束日期': '2024-01-15', '折扣率': 0.12},
        {'活动ID': 'M007', '活动名称': '情人节专场', '开始日期': '2024-02-10', '结束日期': '2024-02-14', '折扣率': 0.08},
        {'活动ID': 'M008', '活动名称': '女神节优惠', '开始日期': '2024-03-01', '结束日期': '2024-03-08', '折扣率': 0.15},
    ])
    
    campaigns['开始日期'] = pd.to_datetime(campaigns['开始日期'])
    campaigns['结束日期'] = pd.to_datetime(campaigns['结束日期'])
    
    # 为交易添加活动标识
    np.random.seed(42)
    transactions = transactions.copy()
    
    for idx, row in transactions.iterrows():
        transaction_date = pd.to_datetime(row['交易日期'])
        
        # 检查是否在活动期间
        for _, campaign in campaigns.iterrows():
            if campaign['开始日期'] <= transaction_date <= campaign['结束日期']:
                # 70%概率参与活动
                if np.random.random() < 0.7:
                    transactions.at[idx, '活动ID'] = campaign['活动ID']
                    transactions.at[idx, '折扣率'] = campaign['折扣率']
                    # 重新计算折扣后价格
                    original_amount = transactions.at[idx, '总金额']
                    transactions.at[idx, '总金额'] = round(original_amount * (1 - campaign['折扣率']), 2)
                break
    
    print(f"营销活动数：{len(campaigns)}")
    print(f"参与活动的交易：{transactions['活动ID'].notna().sum()} 条")
    
    return transactions, campaigns

def save_processed_data(customers, products, transactions, campaigns):
    """
    保存处理后的数据
    """
    print("\n" + "=" * 80)
    print("保存处理后的数据")
    print("=" * 80)
    
    # 创建目录
    os.makedirs('data/raw', exist_ok=True)
    
    # 保存数据
    customers.to_csv('data/raw/customers.csv', index=False, encoding='utf-8-sig')
    products.to_csv('data/raw/products.csv', index=False, encoding='utf-8-sig')
    transactions.to_csv('data/raw/sales_transactions.csv', index=False, encoding='utf-8-sig')
    campaigns.to_csv('data/raw/marketing_campaigns.csv', index=False, encoding='utf-8-sig')
    
    print("✓ 客户数据已保存: data/raw/customers.csv")
    print("✓ 产品数据已保存: data/raw/products.csv")
    print("✓ 交易数据已保存: data/raw/sales_transactions.csv")
    print("✓ 营销活动已保存: data/raw/marketing_campaigns.csv")
    
    # 打印统计信息
    print("\n" + "=" * 80)
    print("数据处理完成！统计信息：")
    print("=" * 80)
    print(f"客户总数: {len(customers)}")
    print(f"产品总数: {len(products)}")
    print(f"交易总数: {len(transactions)}")
    print(f"营销活动: {len(campaigns)}")
    print(f"总销售额: ¥{transactions['总金额'].sum():,.2f}")
    print(f"总利润: ¥{transactions['利润'].sum():,.2f}")
    print(f"平均客单价: ¥{transactions['总金额'].mean():,.2f}")

def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "真实数据预处理流程" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # 1. 加载真实数据
    perfumes, customers_apply, consumption, credit, overdue = load_real_data()
    
    # 2. 处理客户数据
    customers = process_customer_data(customers_apply, credit)
    
    # 3. 处理产品数据
    products = process_product_data(perfumes)
    
    # 4. 生成交易数据
    transactions = generate_transactions(customers, products, consumption)
    
    # 5. 添加营销活动
    transactions, campaigns = add_marketing_campaigns(transactions)
    
    # 6. 保存数据
    save_processed_data(customers, products, transactions, campaigns)
    
    print("\n" + "=" * 80)
    print("✓ 所有数据处理完成！可以继续执行后续分析步骤")
    print("=" * 80)

if __name__ == '__main__':
    main()



