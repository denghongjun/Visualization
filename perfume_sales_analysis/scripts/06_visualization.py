"""
综合数据可视化脚本
生成各类分析图表和仪表板
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_all_data():
    """加载所有数据"""
    print("加载数据...")
    
    # 加载原始数据
    customers = pd.read_csv('data/raw/customers.csv', encoding='utf-8-sig')
    products = pd.read_csv('data/raw/products.csv', encoding='utf-8-sig')
    campaigns = pd.read_csv('data/raw/marketing_campaigns.csv', encoding='utf-8-sig')
    
    # 加载处理后的数据
    transactions = pd.read_csv('data/processed/clean_transactions.csv', encoding='utf-8-sig')
    customer_features = pd.read_csv('data/processed/customer_features.csv', encoding='utf-8-sig')
    product_features = pd.read_csv('data/processed/product_features.csv', encoding='utf-8-sig')
    
    # 加载数据仓库
    fact_sales = pd.read_csv('data/warehouse/fact_sales.csv', encoding='utf-8-sig')
    dim_customer = pd.read_csv('data/warehouse/dim_customer.csv', encoding='utf-8-sig')
    dim_product = pd.read_csv('data/warehouse/dim_product.csv', encoding='utf-8-sig')
    dim_time = pd.read_csv('data/warehouse/dim_time.csv', encoding='utf-8-sig')
    
    # 转换日期列
    transactions['交易日期'] = pd.to_datetime(transactions['交易日期'])
    fact_sales['日期'] = pd.to_datetime(fact_sales['日期'])
    dim_time['日期'] = pd.to_datetime(dim_time['日期'])
    
    print("数据加载完成")
    
    return {
        'customers': customers,
        'products': products,
        'campaigns': campaigns,
        'transactions': transactions,
        'customer_features': customer_features,
        'product_features': product_features,
        'fact_sales': fact_sales,
        'dim_customer': dim_customer,
        'dim_product': dim_product,
        'dim_time': dim_time
    }

def visualize_sales_overview(fact_sales, dim_time):
    """
    销售概览可视化
    
    参数:
        fact_sales: 销售事实表
        dim_time: 时间维度表
    """
    print("\n创建销售概览图表...")
    
    # 合并时间维度
    sales_with_time = fact_sales.merge(dim_time, on='日期', how='left')
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 月度销售趋势
    monthly_sales = sales_with_time.groupby(['年份', '月份']).agg({
        '总金额': 'sum',
        '订单ID': 'count'
    }).reset_index()
    monthly_sales['年月'] = monthly_sales['年份'].astype(str) + '-' + monthly_sales['月份'].astype(str).str.zfill(2)
    
    ax1 = axes[0, 0]
    ax1.plot(range(len(monthly_sales)), monthly_sales['总金额'], marker='o', linewidth=2, markersize=8, color='steelblue')
    ax1.set_xlabel('月份', fontsize=12)
    ax1.set_ylabel('销售额（元）', fontsize=12)
    ax1.set_title('月度销售额趋势', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(range(0, len(monthly_sales), 2))
    ax1.set_xticklabels(monthly_sales['年月'].values[::2], rotation=45)
    
    # 2. 季度销售对比
    quarterly_sales = sales_with_time.groupby(['年份', '季度'])['总金额'].sum().reset_index()
    quarterly_sales['年季度'] = quarterly_sales['年份'].astype(str) + '-Q' + quarterly_sales['季度'].astype(str)
    
    ax2 = axes[0, 1]
    bars = ax2.bar(range(len(quarterly_sales)), quarterly_sales['总金额'], 
                   color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'],
                   alpha=0.7, edgecolor='black')
    ax2.set_xlabel('季度', fontsize=12)
    ax2.set_ylabel('销售额（元）', fontsize=12)
    ax2.set_title('季度销售额对比', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(quarterly_sales)))
    ax2.set_xticklabels(quarterly_sales['年季度'].values, rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. 星期销售分析
    weekly_sales = sales_with_time.groupby('星期几')['总金额'].sum().sort_index()
    week_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    ax3 = axes[1, 0]
    ax3.bar(range(7), weekly_sales.values, color='coral', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('星期', fontsize=12)
    ax3.set_ylabel('总销售额（元）', fontsize=12)
    ax3.set_title('一周销售额分布', fontsize=14, fontweight='bold')
    ax3.set_xticks(range(7))
    ax3.set_xticklabels(week_names)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. 销售额和订单量双轴图
    ax4 = axes[1, 1]
    ax4_twin = ax4.twinx()
    
    x = range(len(monthly_sales))
    ax4.bar(x, monthly_sales['总金额'], alpha=0.6, color='steelblue', label='销售额')
    ax4_twin.plot(x, monthly_sales['订单ID'], color='red', marker='o', linewidth=2, markersize=6, label='订单量')
    
    ax4.set_xlabel('月份', fontsize=12)
    ax4.set_ylabel('销售额（元）', fontsize=12, color='steelblue')
    ax4_twin.set_ylabel('订单量', fontsize=12, color='red')
    ax4.set_title('销售额与订单量趋势对比', fontsize=14, fontweight='bold')
    ax4.tick_params(axis='y', labelcolor='steelblue')
    ax4_twin.tick_params(axis='y', labelcolor='red')
    ax4.grid(True, alpha=0.3)
    ax4.set_xticks(range(0, len(monthly_sales), 2))
    ax4.set_xticklabels(monthly_sales['年月'].values[::2], rotation=45)
    
    # 添加图例
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig('figures/sales_overview.png', dpi=300, bbox_inches='tight')
    print("销售概览图表已保存")

def visualize_customer_analysis(dim_customer, customer_features):
    """
    客户分析可视化
    
    参数:
        dim_customer: 客户维度表
        customer_features: 客户特征数据
    """
    print("\n创建客户分析图表...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # 1. 客户性别分布
    gender_counts = dim_customer['性别'].value_counts()
    axes[0].pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%',
                colors=['#FF9999', '#66B2FF'], startangle=90)
    axes[0].set_title('客户性别分布', fontsize=12, fontweight='bold')
    
    # 2. 客户年龄分布
    axes[1].hist(dim_customer['年龄'], bins=20, color='skyblue', alpha=0.7, edgecolor='black')
    axes[1].axvline(dim_customer['年龄'].mean(), color='red', linestyle='--', linewidth=2, label=f'平均年龄: {dim_customer["年龄"].mean():.1f}')
    axes[1].set_xlabel('年龄', fontsize=10)
    axes[1].set_ylabel('客户数量', fontsize=10)
    axes[1].set_title('客户年龄分布', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    # 3. 客户城市分布
    city_counts = dim_customer['城市'].value_counts().head(10)
    axes[2].barh(range(len(city_counts)), city_counts.values, color='teal', alpha=0.7)
    axes[2].set_yticks(range(len(city_counts)))
    axes[2].set_yticklabels(city_counts.index)
    axes[2].set_xlabel('客户数量', fontsize=10)
    axes[2].set_title('客户城市分布 Top10', fontsize=12, fontweight='bold')
    axes[2].invert_yaxis()
    axes[2].grid(True, alpha=0.3, axis='x')
    
    # 4. 会员等级分布
    member_counts = dim_customer['会员等级'].value_counts()
    axes[3].bar(range(len(member_counts)), member_counts.values, 
                color=['#FFD700', '#C0C0C0', '#CD7F32', '#E5E4E2'], alpha=0.7, edgecolor='black')
    axes[3].set_xticks(range(len(member_counts)))
    axes[3].set_xticklabels(member_counts.index, rotation=45)
    axes[3].set_ylabel('客户数量', fontsize=10)
    axes[3].set_title('会员等级分布', fontsize=12, fontweight='bold')
    axes[3].grid(True, alpha=0.3, axis='y')
    
    # 5. RFM总分分布
    rfm_scores = customer_features['RFM_Total'].dropna()
    axes[4].hist(rfm_scores, bins=12, color='lightcoral', alpha=0.7, edgecolor='black')
    axes[4].axvline(rfm_scores.mean(), color='red', linestyle='--', linewidth=2, label=f'平均分: {rfm_scores.mean():.1f}')
    axes[4].set_xlabel('RFM总分', fontsize=10)
    axes[4].set_ylabel('客户数量', fontsize=10)
    axes[4].set_title('客户RFM总分分布', fontsize=12, fontweight='bold')
    axes[4].legend()
    axes[4].grid(True, alpha=0.3, axis='y')
    
    # 6. 客户分群分布
    if '客户分群' in dim_customer.columns:
        segment_counts = dim_customer['客户分群'].value_counts()
        axes[5].bar(range(len(segment_counts)), segment_counts.values, 
                   color=plt.cm.Set3(range(len(segment_counts))), alpha=0.7, edgecolor='black')
        axes[5].set_xticks(range(len(segment_counts)))
        axes[5].set_xticklabels(segment_counts.index, rotation=45, ha='right')
        axes[5].set_ylabel('客户数量', fontsize=10)
        axes[5].set_title('客户分群分布', fontsize=12, fontweight='bold')
        axes[5].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('figures/customer_analysis.png', dpi=300, bbox_inches='tight')
    print("客户分析图表已保存")

def visualize_product_analysis(dim_product, product_features, fact_sales):
    """
    产品分析可视化
    
    参数:
        dim_product: 产品维度表
        product_features: 产品特征数据
        fact_sales: 销售事实表
    """
    print("\n创建产品分析图表...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 产品销售额排行
    top_products = product_features.nlargest(10, '销售额')
    axes[0, 0].barh(range(len(top_products)), top_products['销售额'], color='steelblue', alpha=0.7)
    axes[0, 0].set_yticks(range(len(top_products)))
    axes[0, 0].set_yticklabels(top_products['产品名称'])
    axes[0, 0].set_xlabel('销售额（元）', fontsize=12)
    axes[0, 0].set_title('产品销售额排行 Top10', fontsize=14, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    # 2. 品牌销售额对比
    merged_data = dim_product.merge(product_features, on='产品ID')
    if '品牌' in merged_data.columns:
        brand_sales = merged_data[['品牌', '销售额']].groupby('品牌')['销售额'].sum().sort_values(ascending=False).head(15)
        axes[0, 1].bar(range(len(brand_sales)), brand_sales.values, 
                       color=plt.cm.Set3(range(len(brand_sales))), alpha=0.7, edgecolor='black')
        axes[0, 1].set_xticks(range(len(brand_sales)))
        axes[0, 1].set_xticklabels(brand_sales.index, rotation=45, ha='right')
        axes[0, 1].set_ylabel('销售额（元）', fontsize=12)
        axes[0, 1].set_title('品牌销售额对比 Top15', fontsize=14, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
    else:
        # 如果没有品牌字段，显示产品销售Top10
        top_10_sales = product_features.nlargest(10, '销售额')
        axes[0, 1].bar(range(len(top_10_sales)), top_10_sales['销售额'].values, 
                       color=plt.cm.Set3(range(len(top_10_sales))), alpha=0.7, edgecolor='black')
        axes[0, 1].set_xticks(range(len(top_10_sales)))
        axes[0, 1].set_xticklabels([f'P{i+1}' for i in range(len(top_10_sales))], rotation=45, ha='right')
        axes[0, 1].set_ylabel('销售额（元）', fontsize=12)
        axes[0, 1].set_title('产品销售额对比 Top10', fontsize=14, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 3. 产品分类销售分布
    merged_for_category = dim_product.merge(product_features, on='产品ID', how='left')
    if '分类' in merged_for_category.columns and '销售额' in merged_for_category.columns:
        category_sales = merged_for_category[['分类', '销售额']].groupby('分类')['销售额'].sum()
        if len(category_sales) > 0:
            colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#CC99FF'][:len(category_sales)]
            axes[1, 0].pie(category_sales.values, labels=category_sales.index, autopct='%1.1f%%',
                           colors=colors, startangle=90)
            axes[1, 0].set_title('产品分类销售额占比', fontsize=14, fontweight='bold')
        else:
            axes[1, 0].text(0.5, 0.5, '暂无分类数据', ha='center', va='center')
    else:
        axes[1, 0].text(0.5, 0.5, '暂无分类数据', ha='center', va='center')
    
    # 4. 价格档次销售分析
    if '价格档次' in merged_for_category.columns and '销售额' in merged_for_category.columns:
        price_tier_sales = merged_for_category[['价格档次', '销售额']].groupby('价格档次')['销售额'].sum()
        if len(price_tier_sales) > 0:
            price_tier_order = ['经济型', '中档', '高档']
            # 只保留存在的档次
            existing_tiers = [t for t in price_tier_order if t in price_tier_sales.index]
            if existing_tiers:
                price_tier_sales = price_tier_sales.reindex(existing_tiers, fill_value=0)
                colors_dict = {'经济型': '#90EE90', '中档': '#FFD700', '高档': '#FF6347'}
                colors = [colors_dict.get(t, '#CCCCCC') for t in existing_tiers]
                
                axes[1, 1].bar(range(len(price_tier_sales)), price_tier_sales.values, 
                               color=colors, alpha=0.7, edgecolor='black')
                axes[1, 1].set_xticks(range(len(price_tier_sales)))
                axes[1, 1].set_xticklabels(price_tier_sales.index)
                axes[1, 1].set_ylabel('销售额（元）', fontsize=12)
                axes[1, 1].set_title('价格档次销售额对比', fontsize=14, fontweight='bold')
                axes[1, 1].grid(True, alpha=0.3, axis='y')
            else:
                axes[1, 1].text(0.5, 0.5, '暂无价格档次数据', ha='center', va='center', transform=axes[1, 1].transAxes)
        else:
            axes[1, 1].text(0.5, 0.5, '暂无价格档次数据', ha='center', va='center', transform=axes[1, 1].transAxes)
    else:
        axes[1, 1].text(0.5, 0.5, '暂无价格档次数据', ha='center', va='center', transform=axes[1, 1].transAxes)
    
    plt.tight_layout()
    plt.savefig('figures/product_analysis.png', dpi=300, bbox_inches='tight')
    print("产品分析图表已保存")

def visualize_marketing_analysis(fact_sales, campaigns):
    """
    营销活动分析可视化
    
    参数:
        fact_sales: 销售事实表
        campaigns: 营销活动数据
    """
    print("\n创建营销活动分析图表...")
    
    # 分析有活动和无活动的销售对比
    campaign_sales = fact_sales[fact_sales['活动ID'].notna()].groupby('活动ID').agg({
        '总金额': 'sum',
        '订单ID': 'count',
        '利润': 'sum'
    }).reset_index()
    
    campaign_sales = campaign_sales.merge(campaigns, on='活动ID', how='left')
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 活动销售额对比
    axes[0, 0].barh(range(len(campaign_sales)), campaign_sales['总金额'], color='coral', alpha=0.7)
    axes[0, 0].set_yticks(range(len(campaign_sales)))
    axes[0, 0].set_yticklabels(campaign_sales['活动名称'])
    axes[0, 0].set_xlabel('销售额（元）', fontsize=12)
    axes[0, 0].set_title('营销活动销售额对比', fontsize=14, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    # 2. 活动订单量对比
    axes[0, 1].bar(range(len(campaign_sales)), campaign_sales['订单ID'], 
                   color='steelblue', alpha=0.7, edgecolor='black')
    axes[0, 1].set_xticks(range(len(campaign_sales)))
    axes[0, 1].set_xticklabels(campaign_sales['活动名称'], rotation=45, ha='right')
    axes[0, 1].set_ylabel('订单数量', fontsize=12)
    axes[0, 1].set_title('营销活动订单量对比', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 3. 折扣率与销售额关系
    axes[1, 0].scatter(campaign_sales['折扣率'], campaign_sales['总金额'], 
                      s=200, alpha=0.6, c=range(len(campaign_sales)), cmap='viridis', edgecolors='black')
    for i, row in campaign_sales.iterrows():
        axes[1, 0].annotate(row['活动名称'], (row['折扣率'], row['总金额']), 
                           fontsize=8, ha='center')
    axes[1, 0].set_xlabel('折扣率', fontsize=12)
    axes[1, 0].set_ylabel('销售额（元）', fontsize=12)
    axes[1, 0].set_title('折扣率与销售额关系', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 有活动 vs 无活动销售对比
    with_campaign = fact_sales[fact_sales['活动ID'].notna()]['总金额'].sum()
    without_campaign = fact_sales[fact_sales['活动ID'].isna()]['总金额'].sum()
    
    labels = ['参与活动', '未参与活动']
    values = [with_campaign, without_campaign]
    colors_pie = ['#FF9999', '#66B2FF']
    
    axes[1, 1].pie(values, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    axes[1, 1].set_title('营销活动参与度对销售额的影响', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('figures/marketing_analysis.png', dpi=300, bbox_inches='tight')
    print("营销活动分析图表已保存")

def create_interactive_dashboard(data_dict):
    """
    创建交互式仪表板（使用Plotly）
    
    参数:
        data_dict: 包含所有数据的字典
    """
    print("\n创建交互式仪表板...")
    
    fact_sales = data_dict['fact_sales']
    dim_time = data_dict['dim_time']
    dim_product = data_dict['dim_product']
    
    # 合并数据
    sales_data = fact_sales.merge(dim_time, on='日期', how='left')
    # 只合并存在的字段
    product_cols = ['产品ID', '产品名称']
    if '品牌' in dim_product.columns:
        product_cols.append('品牌')
    sales_data = sales_data.merge(dim_product[product_cols], on='产品ID', how='left')
    
    # 创建月度销售趋势交互图
    monthly_data = sales_data.groupby(['年份', '月份']).agg({
        '总金额': 'sum',
        '订单ID': 'count'
    }).reset_index()
    monthly_data['年月'] = monthly_data['年份'].astype(str) + '-' + monthly_data['月份'].astype(str).str.zfill(2)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('月度销售额趋势', '品牌销售额分布', '产品销售Top10', '日销售额热力图'),
        specs=[[{'type': 'scatter'}, {'type': 'pie'}],
               [{'type': 'bar'}, {'type': 'scatter'}]]
    )
    
    # 1. 月度销售额趋势
    fig.add_trace(
        go.Scatter(x=monthly_data['年月'], y=monthly_data['总金额'],
                  mode='lines+markers', name='销售额',
                  line=dict(color='steelblue', width=3)),
        row=1, col=1
    )
    
    # 2. 品牌销售额分布
    if '品牌' in sales_data.columns:
        brand_sales = sales_data.groupby('品牌')['总金额'].sum().reset_index().nlargest(10, '总金额')
        fig.add_trace(
            go.Pie(labels=brand_sales['品牌'], values=brand_sales['总金额'],
                  name='品牌销售'),
            row=1, col=2
        )
    else:
        # 如果没有品牌字段，显示产品分类
        category_sales = sales_data.groupby('产品ID')['总金额'].sum().reset_index().nlargest(10, '总金额')
        fig.add_trace(
            go.Pie(labels=category_sales['产品ID'], values=category_sales['总金额'],
                  name='产品销售'),
            row=1, col=2
        )
    
    # 3. 产品销售Top10
    product_sales = sales_data.groupby('产品名称')['总金额'].sum().nlargest(10).reset_index()
    fig.add_trace(
        go.Bar(x=product_sales['总金额'], y=product_sales['产品名称'],
              orientation='h', name='产品销售',
              marker=dict(color='coral')),
        row=2, col=1
    )
    
    # 4. 日销售额趋势
    daily_sales = sales_data.groupby('日期')['总金额'].sum().reset_index()
    fig.add_trace(
        go.Scatter(x=daily_sales['日期'], y=daily_sales['总金额'],
                  mode='lines', name='日销售额',
                  line=dict(color='green', width=1)),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=False, title_text="香水销售数据交互式仪表板")
    fig.write_html('figures/interactive_dashboard.html')
    print("交互式仪表板已保存: figures/interactive_dashboard.html")

def main():
    """主函数"""
    print("=" * 60)
    print("开始生成综合可视化图表")
    print("=" * 60)
    
    # 加载所有数据
    data_dict = load_all_data()
    
    # 生成各类可视化图表
    visualize_sales_overview(data_dict['fact_sales'], data_dict['dim_time'])
    visualize_customer_analysis(data_dict['dim_customer'], data_dict['customer_features'])
    visualize_product_analysis(data_dict['dim_product'], data_dict['product_features'], data_dict['fact_sales'])
    visualize_marketing_analysis(data_dict['fact_sales'], data_dict['campaigns'])
    
    # 创建交互式仪表板
    create_interactive_dashboard(data_dict)
    
    print("\n" + "=" * 60)
    print("所有可视化图表生成完成！")
    print("=" * 60)
    print("\n图表保存位置: figures/ 目录")

if __name__ == '__main__':
    main()


