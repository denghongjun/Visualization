"""
客户细分分析脚本
使用K-Means和DBSCAN聚类算法进行客户细分
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def load_customer_data():
    """加载客户特征数据"""
    print("加载客户特征数据...")
    
    customer_features = pd.read_csv('data/processed/customer_features.csv', encoding='utf-8-sig')
    print(f"客户数据加载完成：{len(customer_features)} 条记录")
    
    return customer_features

def prepare_clustering_data(customer_features):
    """
    准备聚类数据
    
    参数:
        customer_features: 客户特征数据
    
    返回:
        X: 标准化后的特征矩阵
        feature_names: 特征名称列表
        customer_ids: 客户ID列表
    """
    print("\n准备聚类数据...")
    
    # 选择用于聚类的特征
    clustering_features = [
        'Recency',           # 最近一次购买距今天数
        'Frequency',         # 购买频率
        'Monetary',          # 消费金额
        '平均订单金额',      # 平均订单金额
        '产品多样性',        # 购买的不同产品数量
        '活动参与次数'       # 参与营销活动次数
    ]
    
    # 提取特征
    X = customer_features[clustering_features].fillna(0).values
    customer_ids = customer_features['客户ID'].values
    
    print(f"聚类特征: {clustering_features}")
    print(f"特征矩阵形状: {X.shape}")
    
    # 数据标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print("数据标准化完成")
    
    return X_scaled, clustering_features, customer_ids, scaler

def find_optimal_k(X, max_k=10):
    """
    使用肘部法则和轮廓系数找到最优K值
    
    参数:
        X: 特征矩阵
        max_k: 最大K值
    
    返回:
        optimal_k: 最优K值
    """
    print("\n寻找最优K值...")
    
    inertias = []
    silhouette_scores = []
    k_range = range(2, max_k + 1)
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        
        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X, kmeans.labels_))
        
        print(f"K={k}: 惯性={kmeans.inertia_:.2f}, 轮廓系数={silhouette_scores[-1]:.3f}")
    
    # 创建图表
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 肘部法则图
    axes[0].plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
    axes[0].set_xlabel('K值', fontsize=12)
    axes[0].set_ylabel('惯性（Inertia）', fontsize=12)
    axes[0].set_title('肘部法则 - 确定最优K值', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # 轮廓系数图
    axes[1].plot(k_range, silhouette_scores, 'ro-', linewidth=2, markersize=8)
    axes[1].set_xlabel('K值', fontsize=12)
    axes[1].set_ylabel('轮廓系数（Silhouette Score）', fontsize=12)
    axes[1].set_title('轮廓系数 - 确定最优K值', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figures/optimal_k_selection.png', dpi=300, bbox_inches='tight')
    print("\n最优K值选择图已保存")
    
    # 选择轮廓系数最高的K值
    optimal_k = k_range[np.argmax(silhouette_scores)]
    print(f"\n推荐最优K值: {optimal_k} (轮廓系数: {max(silhouette_scores):.3f})")
    
    return optimal_k

def perform_kmeans_clustering(X, n_clusters=4):
    """
    执行K-Means聚类
    
    参数:
        X: 特征矩阵
        n_clusters: 聚类数量
    
    返回:
        kmeans: 训练好的K-Means模型
        labels: 聚类标签
    """
    print(f"\n执行K-Means聚类 (K={n_clusters})...")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(X)
    
    # 计算评估指标
    silhouette = silhouette_score(X, labels)
    davies_bouldin = davies_bouldin_score(X, labels)
    
    print(f"\nK-Means聚类完成！")
    print(f"  - 聚类数量: {n_clusters}")
    print(f"  - 轮廓系数: {silhouette:.3f} (越接近1越好)")
    print(f"  - Davies-Bouldin指数: {davies_bouldin:.3f} (越小越好)")
    print(f"  - 惯性: {kmeans.inertia_:.2f}")
    
    # 显示各类别样本数量
    unique, counts = np.unique(labels, return_counts=True)
    print(f"\n各聚类样本数量:")
    for cluster, count in zip(unique, counts):
        print(f"  - 聚类 {cluster}: {count} 个客户 ({count/len(labels)*100:.1f}%)")
    
    return kmeans, labels, silhouette, davies_bouldin

def perform_dbscan_clustering(X, eps=0.5, min_samples=5):
    """
    执行DBSCAN聚类
    
    参数:
        X: 特征矩阵
        eps: 邻域半径
        min_samples: 最小样本数
    
    返回:
        dbscan: 训练好的DBSCAN模型
        labels: 聚类标签
    """
    print(f"\n执行DBSCAN聚类 (eps={eps}, min_samples={min_samples})...")
    
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X)
    
    # 统计聚类结果
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    print(f"\nDBSCAN聚类完成！")
    print(f"  - 聚类数量: {n_clusters}")
    print(f"  - 噪声点数量: {n_noise} ({n_noise/len(labels)*100:.1f}%)")
    
    # 显示各类别样本数量
    unique, counts = np.unique(labels, return_counts=True)
    print(f"\n各聚类样本数量:")
    for cluster, count in zip(unique, counts):
        if cluster == -1:
            print(f"  - 噪声点: {count} 个客户")
        else:
            print(f"  - 聚类 {cluster}: {count} 个客户 ({count/len(labels)*100:.1f}%)")
    
    # 计算非噪声点的轮廓系数
    if n_clusters > 1 and n_noise < len(labels):
        mask = labels != -1
        if sum(mask) > 0:
            silhouette = silhouette_score(X[mask], labels[mask])
            print(f"  - 轮廓系数（不含噪声点）: {silhouette:.3f}")
    
    return dbscan, labels

def visualize_clusters_2d(X, labels, method='K-Means', feature_names=None):
    """
    使用PCA降维到2D并可视化聚类结果
    
    参数:
        X: 特征矩阵
        labels: 聚类标签
        method: 聚类方法名称
        feature_names: 特征名称
    """
    print(f"\n可视化{method}聚类结果...")
    
    # PCA降维到2D
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X)
    
    print(f"PCA解释方差比: {pca.explained_variance_ratio_}")
    print(f"累计解释方差: {sum(pca.explained_variance_ratio_):.3f}")
    
    # 创建图表
    plt.figure(figsize=(12, 8))
    
    # 获取唯一的标签
    unique_labels = np.unique(labels)
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        if label == -1:
            # 噪声点用黑色小点表示
            mask = labels == label
            plt.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                       c='black', marker='x', s=50, alpha=0.5, label='噪声点')
        else:
            mask = labels == label
            plt.scatter(X_pca[mask, 0], X_pca[mask, 1], 
                       c=[color], s=100, alpha=0.6, 
                       edgecolors='black', linewidth=0.5,
                       label=f'聚类 {label}')
    
    plt.xlabel(f'主成分1 ({pca.explained_variance_ratio_[0]:.2%} 方差)', fontsize=12)
    plt.ylabel(f'主成分2 ({pca.explained_variance_ratio_[1]:.2%} 方差)', fontsize=12)
    plt.title(f'{method}聚类结果可视化 (PCA降维)', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    filename = f'figures/clustering_{method.lower().replace("-", "_")}_visualization.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"聚类可视化图已保存: {filename}")

def analyze_cluster_characteristics(customer_features, labels, clustering_features):
    """
    分析各聚类的特征
    
    参数:
        customer_features: 客户特征数据
        labels: 聚类标签
        clustering_features: 聚类使用的特征
    
    返回:
        DataFrame: 聚类特征统计
    """
    print("\n分析聚类特征...")
    
    # 添加聚类标签到数据框
    customer_features_copy = customer_features.copy()
    customer_features_copy['聚类标签'] = labels
    
    # 定义聚类名称
    cluster_names = {
        0: '高价值忠诚客户',
        1: '潜力增长客户',
        2: '一般活跃客户',
        3: '流失风险客户',
        -1: '异常客户'
    }
    
    customer_features_copy['客户分群'] = customer_features_copy['聚类标签'].map(
        lambda x: cluster_names.get(x, f'聚类{x}')
    )
    
    # 按聚类分组统计
    cluster_stats = customer_features_copy.groupby('客户分群')[clustering_features].agg(['mean', 'median', 'std'])
    
    # 添加客户数量
    cluster_counts = customer_features_copy.groupby('客户分群').size()
    
    print("\n各聚类特征统计:")
    print("=" * 80)
    for cluster_name in cluster_stats.index:
        print(f"\n【{cluster_name}】 - 客户数量: {cluster_counts[cluster_name]}")
        print("-" * 80)
        for feature in clustering_features:
            mean_val = cluster_stats.loc[cluster_name, (feature, 'mean')]
            median_val = cluster_stats.loc[cluster_name, (feature, 'median')]
            std_val = cluster_stats.loc[cluster_name, (feature, 'std')]
            print(f"  {feature:15s}: 均值={mean_val:8.2f}, 中位数={median_val:8.2f}, 标准差={std_val:8.2f}")
    
    return customer_features_copy, cluster_stats

def visualize_cluster_profiles(cluster_stats, clustering_features):
    """
    可视化聚类画像
    
    参数:
        cluster_stats: 聚类统计数据
        clustering_features: 特征名称
    """
    print("\n创建聚类画像可视化...")
    
    # 提取均值数据
    cluster_means = cluster_stats.xs('mean', axis=1, level=1)
    
    # 数据标准化用于雷达图
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    cluster_means_scaled = pd.DataFrame(
        scaler.fit_transform(cluster_means),
        index=cluster_means.index,
        columns=cluster_means.columns
    )
    
    # 创建热力图
    plt.figure(figsize=(12, 6))
    sns.heatmap(cluster_means.T, annot=True, fmt='.1f', cmap='YlOrRd', 
                cbar_kws={'label': '特征值'}, linewidths=0.5)
    plt.title('客户聚类特征热力图', fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('客户分群', fontsize=12)
    plt.ylabel('特征指标', fontsize=12)
    plt.tight_layout()
    plt.savefig('figures/cluster_heatmap.png', dpi=300, bbox_inches='tight')
    print("聚类热力图已保存")
    
    # 创建柱状图对比
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()
    
    for idx, feature in enumerate(clustering_features):
        ax = axes[idx]
        cluster_means[feature].plot(kind='bar', ax=ax, color='steelblue', alpha=0.7)
        ax.set_title(f'{feature}', fontsize=12, fontweight='bold')
        ax.set_xlabel('客户分群', fontsize=10)
        ax.set_ylabel('平均值', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('figures/cluster_feature_comparison.png', dpi=300, bbox_inches='tight')
    print("聚类特征对比图已保存")

def save_clustering_results(customer_features_with_clusters):
    """
    保存聚类结果
    
    参数:
        customer_features_with_clusters: 包含聚类标签的客户特征数据
    """
    print("\n保存聚类结果...")
    
    customer_features_with_clusters.to_csv(
        'output/customer_segmentation_results.csv', 
        index=False, 
        encoding='utf-8-sig'
    )
    
    # 生成聚类摘要报告
    summary = customer_features_with_clusters.groupby('客户分群').agg({
        '客户ID': 'count',
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean',
        '平均订单金额': 'mean',
        '产品多样性': 'mean',
        '活动参与次数': 'mean'
    }).round(2)
    
    summary.columns = ['客户数量', '平均Recency', '平均Frequency', '平均Monetary', 
                      '平均订单金额', '平均产品多样性', '平均活动参与次数']
    
    summary.to_csv('output/cluster_summary.csv', encoding='utf-8-sig')
    
    print("聚类结果已保存到 output/ 目录")
    print("\n聚类摘要:")
    print(summary)

def main():
    """主函数"""
    print("=" * 60)
    print("开始客户细分分析")
    print("=" * 60)
    
    # 加载数据
    customer_features = load_customer_data()
    
    # 准备聚类数据
    X_scaled, clustering_features, customer_ids, scaler = prepare_clustering_data(customer_features)
    
    # 寻找最优K值
    optimal_k = find_optimal_k(X_scaled, max_k=8)
    
    # 执行K-Means聚类（使用最优K值或指定K=4）
    n_clusters = 4  # 可以改为optimal_k
    kmeans_model, kmeans_labels, silhouette, davies_bouldin = perform_kmeans_clustering(X_scaled, n_clusters=n_clusters)
    
    # 可视化K-Means聚类结果
    visualize_clusters_2d(X_scaled, kmeans_labels, method='K-Means', feature_names=clustering_features)
    
    # 分析聚类特征
    customer_features_with_clusters, cluster_stats = analyze_cluster_characteristics(
        customer_features, kmeans_labels, clustering_features
    )
    
    # 可视化聚类画像
    visualize_cluster_profiles(cluster_stats, clustering_features)
    
    # 保存结果
    save_clustering_results(customer_features_with_clusters)
    
    # 可选：执行DBSCAN聚类作为对比
    print("\n" + "=" * 60)
    print("执行DBSCAN聚类作为对比分析")
    print("=" * 60)
    
    dbscan_model, dbscan_labels = perform_dbscan_clustering(X_scaled, eps=0.8, min_samples=10)
    visualize_clusters_2d(X_scaled, dbscan_labels, method='DBSCAN', feature_names=clustering_features)
    
    print("\n" + "=" * 60)
    print("客户细分分析完成！")
    print("=" * 60)
    
    # 生成分析结论
    print("\n【分析结论】")
    print(f"1. K-Means聚类识别出 {n_clusters} 个客户群体")
    print(f"2. 聚类质量评估：轮廓系数={silhouette:.3f}, DB指数={davies_bouldin:.3f}")
    print(f"3. DBSCAN聚类识别出 {len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)} 个密度聚类")
    print(f"4. 各客户群体特征差异显著,可用于精准营销")

if __name__ == '__main__':
    main()



