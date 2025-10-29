"""
关联规则挖掘脚本
使用Apriori算法发现香水购买的关联规则
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_transaction_data():
    """加载交易数据"""
    print("加载交易数据...")
    
    transactions = pd.read_csv('data/processed/clean_transactions.csv', encoding='utf-8-sig')
    products = pd.read_csv('data/raw/products.csv', encoding='utf-8-sig')
    
    print(f"交易数据: {len(transactions)} 条记录")
    print(f"产品数据: {len(products)} 条记录")
    
    return transactions, products

def prepare_transaction_basket(transactions, products):
    """
    准备购物篮数据
    
    参数:
        transactions: 交易数据
        products: 产品数据
    
    返回:
        basket: 购物篮矩阵（One-hot编码）
        product_mapping: 产品ID到产品名称的映射
    """
    print("\n准备购物篮数据...")
    
    # 合并产品信息获取产品名称
    trans_with_product = transactions.merge(
        products[['产品ID', '产品名称', '品牌']], 
        on='产品ID', 
        how='left'
    )
    
    # 按客户ID分组,创建购物篮
    # 这里我们按订单作为一个购物篮（购买行为）
    baskets = trans_with_product.groupby('客户ID')['产品名称'].apply(list).values
    
    print(f"购物篮数量: {len(baskets)}")
    print(f"示例购物篮: {baskets[:3]}")
    
    # 使用TransactionEncoder转换为one-hot编码
    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    basket_df = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"\n购物篮矩阵形状: {basket_df.shape}")
    print(f"商品种类: {len(basket_df.columns)}")
    
    # 创建产品名称到ID的映射
    product_mapping = dict(zip(products['产品名称'], products['产品ID']))
    
    return basket_df, product_mapping, baskets

def mine_frequent_itemsets(basket_df, min_support=0.01):
    """
    使用Apriori算法挖掘频繁项集
    
    参数:
        basket_df: 购物篮矩阵
        min_support: 最小支持度
    
    返回:
        frequent_itemsets: 频繁项集
    """
    print(f"\n使用Apriori算法挖掘频繁项集...")
    print(f"最小支持度: {min_support}")
    
    # 应用Apriori算法
    frequent_itemsets = apriori(basket_df, min_support=min_support, use_colnames=True)
    
    # 添加项集长度列
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
    
    # 按支持度排序
    frequent_itemsets = frequent_itemsets.sort_values('support', ascending=False).reset_index(drop=True)
    
    print(f"\n发现频繁项集: {len(frequent_itemsets)} 个")
    
    # 统计不同长度的项集
    length_counts = frequent_itemsets['length'].value_counts().sort_index()
    print("\n频繁项集长度分布:")
    for length, count in length_counts.items():
        print(f"  - {length}项集: {count} 个")
    
    print("\n支持度最高的前10个频繁项集:")
    print(frequent_itemsets.head(10)[['itemsets', 'support', 'length']])
    
    return frequent_itemsets

def generate_association_rules(frequent_itemsets, metric='lift', min_threshold=1.0):
    """
    生成关联规则
    
    参数:
        frequent_itemsets: 频繁项集
        metric: 评估指标 ('support', 'confidence', 'lift')
        min_threshold: 最小阈值
    
    返回:
        rules: 关联规则
    """
    print(f"\n生成关联规则...")
    print(f"评估指标: {metric}, 最小阈值: {min_threshold}")
    
    # 生成关联规则
    rules = association_rules(frequent_itemsets, metric=metric, min_threshold=min_threshold, num_itemsets=len(frequent_itemsets))
    
    if len(rules) == 0:
        print("未找到满足条件的关联规则，降低阈值重试...")
        rules = association_rules(frequent_itemsets, metric=metric, min_threshold=min_threshold*0.5, num_itemsets=len(frequent_itemsets))
    
    # 添加规则长度信息
    rules['antecedent_len'] = rules['antecedents'].apply(lambda x: len(x))
    rules['consequent_len'] = rules['consequents'].apply(lambda x: len(x))
    
    # 转换frozenset为字符串以便显示
    rules['antecedents_str'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents_str'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    
    # 按lift排序
    rules = rules.sort_values('lift', ascending=False).reset_index(drop=True)
    
    print(f"\n发现关联规则: {len(rules)} 条")
    
    # 显示规则统计
    print("\n关联规则统计:")
    print(f"  - 平均支持度: {rules['support'].mean():.4f}")
    print(f"  - 平均置信度: {rules['confidence'].mean():.4f}")
    print(f"  - 平均提升度: {rules['lift'].mean():.4f}")
    
    print("\n提升度最高的前10条规则:")
    display_rules = rules.head(10)[['antecedents_str', 'consequents_str', 'support', 'confidence', 'lift']]
    display_rules.columns = ['前项', '后项', '支持度', '置信度', '提升度']
    print(display_rules.to_string(index=False))
    
    return rules

def visualize_frequent_itemsets(frequent_itemsets):
    """
    可视化频繁项集
    
    参数:
        frequent_itemsets: 频繁项集
    """
    print("\n可视化频繁项集...")
    
    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. 频繁项集长度分布
    length_counts = frequent_itemsets['length'].value_counts().sort_index()
    axes[0].bar(length_counts.index, length_counts.values, color='steelblue', alpha=0.7, edgecolor='black')
    axes[0].set_xlabel('项集长度', fontsize=12)
    axes[0].set_ylabel('频繁项集数量', fontsize=12)
    axes[0].set_title('频繁项集长度分布', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # 2. 支持度分布
    axes[1].hist(frequent_itemsets['support'], bins=30, color='coral', alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('支持度', fontsize=12)
    axes[1].set_ylabel('频次', fontsize=12)
    axes[1].set_title('频繁项集支持度分布', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('figures/frequent_itemsets_distribution.png', dpi=300, bbox_inches='tight')
    print("频繁项集分布图已保存")
    
    # 可视化支持度最高的单项和二项集
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 单项集Top 10
    single_items = frequent_itemsets[frequent_itemsets['length'] == 1].head(10)
    single_items_names = [list(x)[0] for x in single_items['itemsets']]
    axes[0].barh(range(len(single_items)), single_items['support'].values, color='teal', alpha=0.7)
    axes[0].set_yticks(range(len(single_items)))
    axes[0].set_yticklabels(single_items_names, fontsize=10)
    axes[0].set_xlabel('支持度', fontsize=12)
    axes[0].set_title('支持度最高的10个单品', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3, axis='x')
    axes[0].invert_yaxis()
    
    # 二项集Top 10
    pair_items = frequent_itemsets[frequent_itemsets['length'] == 2].head(10)
    if len(pair_items) > 0:
        pair_items_names = [' & '.join(list(x)) for x in pair_items['itemsets']]
        axes[1].barh(range(len(pair_items)), pair_items['support'].values, color='orange', alpha=0.7)
        axes[1].set_yticks(range(len(pair_items)))
        axes[1].set_yticklabels(pair_items_names, fontsize=9)
        axes[1].set_xlabel('支持度', fontsize=12)
        axes[1].set_title('支持度最高的10个商品组合', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='x')
        axes[1].invert_yaxis()
    
    plt.tight_layout()
    plt.savefig('figures/top_frequent_items.png', dpi=300, bbox_inches='tight')
    print("热门商品图已保存")

def visualize_association_rules(rules):
    """
    可视化关联规则
    
    参数:
        rules: 关联规则
    """
    print("\n可视化关联规则...")
    
    if len(rules) == 0:
        print("没有关联规则可以可视化")
        return
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 支持度 vs 置信度散点图
    scatter = axes[0, 0].scatter(rules['support'], rules['confidence'], 
                                 c=rules['lift'], s=100, alpha=0.6, 
                                 cmap='viridis', edgecolors='black', linewidth=0.5)
    axes[0, 0].set_xlabel('支持度', fontsize=12)
    axes[0, 0].set_ylabel('置信度', fontsize=12)
    axes[0, 0].set_title('关联规则：支持度 vs 置信度 (颜色=提升度)', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[0, 0], label='提升度')
    
    # 2. 提升度分布
    axes[0, 1].hist(rules['lift'], bins=30, color='skyblue', alpha=0.7, edgecolor='black')
    axes[0, 1].axvline(rules['lift'].mean(), color='red', linestyle='--', linewidth=2, label=f'平均值: {rules["lift"].mean():.2f}')
    axes[0, 1].set_xlabel('提升度 (Lift)', fontsize=12)
    axes[0, 1].set_ylabel('规则数量', fontsize=12)
    axes[0, 1].set_title('关联规则提升度分布', fontsize=14, fontweight='bold')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 3. 置信度分布
    axes[1, 0].hist(rules['confidence'], bins=30, color='lightcoral', alpha=0.7, edgecolor='black')
    axes[1, 0].axvline(rules['confidence'].mean(), color='red', linestyle='--', linewidth=2, label=f'平均值: {rules["confidence"].mean():.2f}')
    axes[1, 0].set_xlabel('置信度 (Confidence)', fontsize=12)
    axes[1, 0].set_ylabel('规则数量', fontsize=12)
    axes[1, 0].set_title('关联规则置信度分布', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # 4. Top规则热力图
    top_rules = rules.nsmallest(15, 'lift') if len(rules) > 15 else rules
    top_rules_matrix = top_rules[['support', 'confidence', 'lift']].values.T
    
    im = axes[1, 1].imshow(top_rules_matrix, cmap='YlOrRd', aspect='auto')
    axes[1, 1].set_yticks([0, 1, 2])
    axes[1, 1].set_yticklabels(['支持度', '置信度', '提升度'])
    axes[1, 1].set_xlabel('规则编号', fontsize=12)
    axes[1, 1].set_title('Top规则指标热力图', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=axes[1, 1])
    
    plt.tight_layout()
    plt.savefig('figures/association_rules_analysis.png', dpi=300, bbox_inches='tight')
    print("关联规则分析图已保存")
    
    # 创建规则网络图
    visualize_rules_network(rules.head(20))

def visualize_rules_network(rules):
    """
    可视化关联规则网络图
    
    参数:
        rules: 关联规则（Top规则）
    """
    print("\n创建关联规则网络图...")
    
    if len(rules) == 0:
        print("没有规则可以创建网络图")
        return
    
    # 创建规则可视化表格
    fig, ax = plt.subplots(figsize=(14, max(8, len(rules) * 0.4)))
    ax.axis('tight')
    ax.axis('off')
    
    # 准备表格数据
    table_data = []
    for idx, row in rules.head(15).iterrows():
        table_data.append([
            f"{idx+1}",
            row['antecedents_str'][:30] + '...' if len(row['antecedents_str']) > 30 else row['antecedents_str'],
            row['consequents_str'][:30] + '...' if len(row['consequents_str']) > 30 else row['consequents_str'],
            f"{row['support']:.3f}",
            f"{row['confidence']:.3f}",
            f"{row['lift']:.3f}"
        ])
    
    headers = ['序号', '前项 (If)', '后项 (Then)', '支持度', '置信度', '提升度']
    
    table = ax.table(cellText=table_data, colLabels=headers, 
                    cellLoc='left', loc='center',
                    colWidths=[0.05, 0.35, 0.35, 0.08, 0.08, 0.08])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # 设置表头样式
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # 设置行颜色
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
    
    plt.title('Top 15 关联规则详情表', fontsize=16, fontweight='bold', pad=20)
    plt.savefig('figures/association_rules_table.png', dpi=300, bbox_inches='tight')
    print("关联规则详情表已保存")

def analyze_rules_by_product(rules, products):
    """
    按产品分析关联规则
    
    参数:
        rules: 关联规则
        products: 产品信息
    """
    print("\n按产品分析关联规则...")
    
    # 统计每个产品作为前项或后项出现的次数
    product_stats = {}
    
    for _, rule in rules.iterrows():
        # 统计前项
        for item in rule['antecedents']:
            if item not in product_stats:
                product_stats[item] = {'作为前项': 0, '作为后项': 0, '平均提升度': []}
            product_stats[item]['作为前项'] += 1
            product_stats[item]['平均提升度'].append(rule['lift'])
        
        # 统计后项
        for item in rule['consequents']:
            if item not in product_stats:
                product_stats[item] = {'作为前项': 0, '作为后项': 0, '平均提升度': []}
            product_stats[item]['作为后项'] += 1
            product_stats[item]['平均提升度'].append(rule['lift'])
    
    # 转换为DataFrame
    stats_list = []
    for product, stats in product_stats.items():
        stats_list.append({
            '产品名称': product,
            '作为前项次数': stats['作为前项'],
            '作为后项次数': stats['作为后项'],
            '总出现次数': stats['作为前项'] + stats['作为后项'],
            '平均提升度': np.mean(stats['平均提升度'])
        })
    
    product_rule_stats = pd.DataFrame(stats_list).sort_values('总出现次数', ascending=False)
    
    print("\n产品在关联规则中的表现:")
    print(product_rule_stats.head(10))
    
    return product_rule_stats

def save_association_results(frequent_itemsets, rules, product_rule_stats):
    """
    保存关联规则挖掘结果
    
    参数:
        frequent_itemsets: 频繁项集
        rules: 关联规则
        product_rule_stats: 产品规则统计
    """
    print("\n保存关联规则挖掘结果...")
    
    # 保存频繁项集
    frequent_itemsets_save = frequent_itemsets.copy()
    frequent_itemsets_save['itemsets'] = frequent_itemsets_save['itemsets'].apply(lambda x: ', '.join(list(x)))
    frequent_itemsets_save.to_csv('output/frequent_itemsets.csv', index=False, encoding='utf-8-sig')
    
    # 保存关联规则
    rules_save = rules[['antecedents_str', 'consequents_str', 'support', 'confidence', 'lift']].copy()
    rules_save.columns = ['前项', '后项', '支持度', '置信度', '提升度']
    rules_save.to_csv('output/association_rules.csv', index=False, encoding='utf-8-sig')
    
    # 保存产品规则统计
    product_rule_stats.to_csv('output/product_rule_statistics.csv', index=False, encoding='utf-8-sig')
    
    print("关联规则挖掘结果已保存到 output/ 目录")

def main():
    """主函数"""
    print("=" * 60)
    print("开始关联规则挖掘")
    print("=" * 60)
    
    # 加载数据
    transactions, products = load_transaction_data()
    
    # 准备购物篮数据
    basket_df, product_mapping, baskets = prepare_transaction_basket(transactions, products)
    
    # 挖掘频繁项集
    frequent_itemsets = mine_frequent_itemsets(basket_df, min_support=0.02)
    
    # 生成关联规则
    rules = generate_association_rules(frequent_itemsets, metric='lift', min_threshold=1.0)
    
    # 可视化频繁项集
    visualize_frequent_itemsets(frequent_itemsets)
    
    # 可视化关联规则
    if len(rules) > 0:
        visualize_association_rules(rules)
        
        # 按产品分析规则
        product_rule_stats = analyze_rules_by_product(rules, products)
        
        # 保存结果
        save_association_results(frequent_itemsets, rules, product_rule_stats)
    else:
        print("\n未发现有效的关联规则")
    
    print("\n" + "=" * 60)
    print("关联规则挖掘完成！")
    print("=" * 60)
    
    # 生成业务建议
    print("\n【业务建议】")
    if len(rules) > 0:
        top_rule = rules.iloc[0]
        print(f"1. 最强关联规则: {top_rule['antecedents_str']} -> {top_rule['consequents_str']}")
        print(f"   提升度: {top_rule['lift']:.2f}, 置信度: {top_rule['confidence']:.2%}")
        print(f"2. 可考虑将关联产品进行组合销售或交叉推荐")
        print(f"3. 在购买前项产品的客户中推送后项产品广告")
        print(f"4. 设计产品套装促销活动")

if __name__ == '__main__':
    main()



