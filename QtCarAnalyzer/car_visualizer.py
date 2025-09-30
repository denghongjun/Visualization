#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车数据可视化工具 - 简约版
基于Qt6开发，支持多种图表类型的汽车数据分析
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.figure import Figure
import seaborn as sns
import tempfile

# 机器学习相关库
try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score, classification_report
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    from sklearn.cluster import KMeans
    ML_AVAILABLE = True
    print("✅ 机器学习模块加载成功")
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ 机器学习模块未安装，请安装scikit-learn: pip install scikit-learn")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame, QFileDialog, QMessageBox, QTextEdit,
    QGroupBox, QProgressBar, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QPixmap, QColor

# 设置中文字体
def setup_chinese_font():
    """设置matplotlib中文字体"""
    try:
        # Windows中文字体
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/simsun.ttc'
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                if 'msyh' in font_path:
                    font_name = 'Microsoft YaHei'
                elif 'simhei' in font_path:
                    font_name = 'SimHei'
                else:
                    font_name = 'SimSun'
                
                # 强制设置所有字体相关参数
                plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans', 'Arial Unicode MS']
                plt.rcParams['axes.unicode_minus'] = False
                plt.rcParams['font.family'] = 'sans-serif'
                
                # 强制刷新字体缓存
                fm.fontManager.findfont(font_name, rebuild_if_missing=True)
                
                print(f"✅ 中文字体设置成功: {font_name}")
                return font_name
        
        # 如果没找到字体文件，尝试系统字体
        system_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi']
        for font_name in system_fonts:
            plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.family'] = 'sans-serif'
            print(f"✅ 尝试系统字体: {font_name}")
            return font_name
            
    except Exception as e:
        print(f"⚠️ 字体设置错误: {e}")
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.family'] = 'sans-serif'
        return 'Microsoft YaHei'

setup_chinese_font()
sns.set_style("whitegrid")
sns.set_palette("husl")

class ChartCanvas(QWidget):
    """图表画布组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建matplotlib图表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        
        # 创建QLabel显示图片
        self.chart_label = QLabel()
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #fafbfc);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
        """)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.chart_label)
        self.setLayout(layout)
        
        # 设置背景颜色
        self.figure.patch.set_facecolor('white')
        
        # 显示欢迎信息
        self.show_welcome()
    
    def update_display(self):
        """更新图表显示"""
        try:
            # 在保存前重新设置字体，确保所有文本都使用正确字体
            for ax in self.figure.get_axes():
                # 设置标题字体
                if ax.get_title():
                    ax.set_title(ax.get_title(), fontfamily='Microsoft YaHei', fontsize=14)
                # 设置轴标签字体
                if ax.get_xlabel():
                    ax.set_xlabel(ax.get_xlabel(), fontfamily='Microsoft YaHei', fontsize=12)
                if ax.get_ylabel():
                    ax.set_ylabel(ax.get_ylabel(), fontfamily='Microsoft YaHei', fontsize=12)
                
                # 设置刻度标签字体
                for label in ax.get_xticklabels():
                    label.set_fontfamily('Microsoft YaHei')
                    label.set_fontsize(10)
                for label in ax.get_yticklabels():
                    label.set_fontfamily('Microsoft YaHei')
                    label.set_fontsize(10)
                
                # 设置图例字体
                legend = ax.get_legend()
                if legend:
                    for text in legend.get_texts():
                        text.set_fontfamily('Microsoft YaHei')
                        text.set_fontsize(10)
                
                # 特别处理饼图等包含文本的图表
                for text in ax.texts:
                    text.set_fontfamily('Microsoft YaHei')
                    text.set_fontsize(10)
            
            # 保存图表到临时文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # 强制设置matplotlib的中文字体参数
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            plt.rcParams['font.family'] = 'sans-serif'
            
            self.figure.savefig(temp_path, format='PNG', dpi=100, bbox_inches='tight',
                              facecolor='white', edgecolor='none')
            
            # 加载并显示图片
            pixmap = QPixmap(temp_path)
            label_size = self.chart_label.size()
            target_width = max(label_size.width() - 40, 800)
            target_height = max(label_size.height() - 40, 600)
            
            scaled_pixmap = pixmap.scaled(target_width, target_height, 
                                        Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.chart_label.setPixmap(scaled_pixmap)
            
            # 删除临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
        except Exception as e:
            self.chart_label.setText(f"图表显示错误: {str(e)}")
    
    def show_welcome(self):
        """显示欢迎信息"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 主标题
        ax.text(0.5, 0.7, '🚗 汽车数据可视化分析平台', 
                ha='center', va='center', fontsize=24, fontweight='bold',
                color='#667eea', fontfamily='Microsoft YaHei')
        
        # 副标题
        ax.text(0.5, 0.5, '智能数据分析 · 专业图表展示 · AI建模预测', 
                ha='center', va='center', fontsize=14,
                color='#64748b', fontfamily='Microsoft YaHei')
        
        # 操作提示
        ax.text(0.5, 0.3, '📂 点击"加载数据"开始您的数据分析之旅\n🎨 支持7种专业图表类型\n🤖 内置机器学习智能建模', 
                ha='center', va='center', fontsize=12,
                color='#374151', fontfamily='Microsoft YaHei',
                bbox=dict(boxstyle='round,pad=1', facecolor='#f8fafc', 
                         edgecolor='#e2e8f0', alpha=0.8))
        
        # 版本信息
        ax.text(0.95, 0.05, 'v1.0.0', 
                ha='right', va='bottom', fontsize=10,
                color='#a0aec0', fontfamily='Microsoft YaHei')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # 设置背景
        ax.set_facecolor('#ffffff')
        
        self.update_display()
    
    def plot_brand_distribution(self, df):
        """品牌分布柱状图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        brand_counts = df['品牌'].value_counts().head(15)
        colors = plt.cm.Set3(np.linspace(0, 1, len(brand_counts)))
        
        bars = ax.bar(range(len(brand_counts)), brand_counts.values, color=colors)
        ax.set_title('汽车品牌分布TOP15', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        ax.set_xlabel('品牌', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_ylabel('数量 (辆)', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_xticks(range(len(brand_counts)))
        ax.set_xticklabels(brand_counts.index, rotation=45, ha='right')
        
        # 添加数值标签
        for bar, value in zip(bars, brand_counts.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                   f'{value}', ha='center', va='bottom', fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        self.update_display()
    
    def plot_price_distribution(self, df):
        """价格分布饼图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        price_counts = df['价格区间'].value_counts()
        
        # 只显示占比超过3%的价格区间，其余合并为"其他"
        total_count = price_counts.sum()
        main_categories = price_counts[price_counts / total_count >= 0.03]
        other_count = price_counts[price_counts / total_count < 0.03].sum()
        
        # 如果有其他类别，添加到主要类别中
        if other_count > 0:
            main_categories['其他'] = other_count
        
        # 限制最多显示6个类别
        if len(main_categories) > 6:
            sorted_categories = main_categories.sort_values(ascending=False)
            top_5 = sorted_categories.head(5)
            others_sum = sorted_categories.tail(len(sorted_categories) - 5).sum()
            if others_sum > 0:
                top_5['其他'] = others_sum
            main_categories = top_5
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB6C1', '#98FB98']
        
        # 创建饼图，添加阴影和分离效果
        explode = [0.05 if cat == '其他' else 0.02 for cat in main_categories.index]  # 突出显示"其他"类别
        
        wedges, texts, autotexts = ax.pie(main_categories.values, labels=main_categories.index,
                                         autopct='%1.1f%%', startangle=90, colors=colors[:len(main_categories)],
                                         explode=explode, shadow=True)
        
        # 显式设置所有文本的字体
        ax.set_title('价格区间分布', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        
        # 设置饼图标签字体
        for text in texts:
            text.set_fontfamily('Microsoft YaHei')
            text.set_fontsize(11)
        
        # 设置百分比文本字体
        for autotext in autotexts:
            autotext.set_fontfamily('Microsoft YaHei')
            autotext.set_fontsize(11)
            autotext.set_color('white')
            autotext.set_weight('bold')
        
        plt.tight_layout()
        self.update_display()
    
    def plot_price_vs_year_scatter(self, df):
        """价格vs年份散点图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 清理数据
        data = df[['价格', '年份', '燃料类型']].dropna()
        
        # 按燃料类型分组
        fuel_types = data['燃料类型'].unique()
        colors = plt.cm.Set1(np.linspace(0, 1, len(fuel_types)))
        
        for i, fuel in enumerate(fuel_types):
            fuel_data = data[data['燃料类型'] == fuel]
            ax.scatter(fuel_data['年份'], fuel_data['价格'], 
                      label=fuel, alpha=0.7, s=50, c=[colors[i]])
        
        ax.set_title('汽车价格与年份关系 (按燃料类型分组)', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        ax.set_xlabel('年份', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_ylabel('价格 (万元)', fontsize=12, fontfamily='Microsoft YaHei')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.update_display()
    
    def plot_year_trend(self, df):
        """年份趋势折线图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 按年份统计车辆数量
        year_counts = df['年份'].value_counts().sort_index()
        
        ax.plot(year_counts.index, year_counts.values, 
               marker='o', linewidth=3, markersize=8, color='#2E86AB')
        ax.fill_between(year_counts.index, year_counts.values, alpha=0.3, color='#2E86AB')
        
        ax.set_title('汽车年份分布趋势', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        ax.set_xlabel('年份', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_ylabel('车辆数量', fontsize=12, fontfamily='Microsoft YaHei')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.update_display()
    
    def plot_fuel_type_comparison(self, df):
        """燃料类型对比柱状图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        fuel_counts = df['燃料类型'].value_counts()
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        bars = ax.bar(fuel_counts.index, fuel_counts.values, color=colors[:len(fuel_counts)])
        ax.set_title('燃料类型分布对比', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        ax.set_xlabel('燃料类型', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_ylabel('车辆数量', fontsize=12, fontfamily='Microsoft YaHei')
        
        # 添加百分比标签
        total = fuel_counts.sum()
        for bar, value in zip(bars, fuel_counts.values):
            height = bar.get_height()
            percentage = (value / total) * 100
            ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                   f'{value}\n({percentage:.1f}%)', ha='center', va='bottom', fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        self.update_display()
    
    def plot_price_histogram(self, df):
        """价格分布直方图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        price_data = df['价格'].dropna()
        
        n, bins, patches = ax.hist(price_data, bins=25, alpha=0.7, 
                                  edgecolor='white', linewidth=1)
        
        # 渐变色
        for i, patch in enumerate(patches):
            patch.set_facecolor(plt.cm.viridis(i / len(patches)))
        
        ax.set_title('汽车价格分布直方图', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        ax.set_xlabel('价格 (万元)', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_ylabel('车辆数量', fontsize=12, fontfamily='Microsoft YaHei')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        self.update_display()
    
    def plot_mileage_boxplot(self, df):
        """里程箱线图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 按车辆类型分组的里程分布
        vehicle_types = df['车辆类型'].unique()
        box_data = []
        labels = []
        
        for vtype in vehicle_types:
            mileage_data = df[df['车辆类型'] == vtype]['里程'].dropna()
            if len(mileage_data) > 5:
                box_data.append(mileage_data)
                labels.append(vtype)
        
        bp = ax.boxplot(box_data, tick_labels=labels, patch_artist=True)
        
        # 美化箱线图
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        for i, patch in enumerate(bp['boxes']):
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.7)
        
        ax.set_title('不同车辆类型的里程分布', fontsize=16, fontweight='bold', pad=20,
                    fontfamily='Microsoft YaHei')
        ax.set_xlabel('车辆类型', fontsize=12, fontfamily='Microsoft YaHei')
        ax.set_ylabel('里程 (公里)', fontsize=12, fontfamily='Microsoft YaHei')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        self.update_display()
    
    def plot_ml_price_prediction(self, y_test, y_pred, mae, r2):
        """绘制价格预测模型效果图"""
        self.figure.clear()
        
        # 创建子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 预测值vs真实值散点图
        ax1.scatter(y_test, y_pred, alpha=0.6, color='#4ECDC4', s=30)
        
        # 添加理想预测线(y=x)
        min_val = min(min(y_test), min(y_pred))
        max_val = max(max(y_test), max(y_pred))
        ax1.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='理想预测线')
        
        ax1.set_xlabel('真实价格 (万元)', fontfamily='Microsoft YaHei', fontsize=12)
        ax1.set_ylabel('预测价格 (万元)', fontfamily='Microsoft YaHei', fontsize=12)
        ax1.set_title('价格预测效果对比', fontfamily='Microsoft YaHei', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 添加模型性能指标
        ax1.text(0.05, 0.95, f'MAE: {mae:.2f}万元\nR²: {r2:.3f}', 
                transform=ax1.transAxes, fontsize=11, 
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                verticalalignment='top', fontfamily='Microsoft YaHei')
        
        # 2. 预测误差分布直方图
        errors = y_pred - y_test
        ax2.hist(errors, bins=30, alpha=0.7, color='#FF6B6B', edgecolor='white')
        ax2.axvline(x=0, color='black', linestyle='--', linewidth=2, label='零误差线')
        ax2.set_xlabel('预测误差 (万元)', fontfamily='Microsoft YaHei', fontsize=12)
        ax2.set_ylabel('频次', fontfamily='Microsoft YaHei', fontsize=12)
        ax2.set_title('预测误差分布', fontfamily='Microsoft YaHei', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 添加误差统计
        ax2.text(0.05, 0.95, f'误差均值: {errors.mean():.2f}\n误差标准差: {errors.std():.2f}', 
                transform=ax2.transAxes, fontsize=11,
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8),
                verticalalignment='top', fontfamily='Microsoft YaHei')
        
        # 3. 残差图
        ax3.scatter(y_pred, errors, alpha=0.6, color='#96CEB4', s=30)
        ax3.axhline(y=0, color='red', linestyle='--', linewidth=2)
        ax3.set_xlabel('预测价格 (万元)', fontfamily='Microsoft YaHei', fontsize=12)
        ax3.set_ylabel('残差 (万元)', fontfamily='Microsoft YaHei', fontsize=12)
        ax3.set_title('残差分析图', fontfamily='Microsoft YaHei', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # 4. 模型性能评估指标
        ax4.axis('off')
        
        # 计算更多评估指标
        import numpy as np
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        
        performance_text = f"""
🎯 模型性能评估

📊 核心指标:
• 平均绝对误差(MAE): {mae:.2f} 万元
• 决定系数(R²): {r2:.3f}
• 均方根误差(RMSE): {rmse:.2f} 万元
• 平均绝对百分比误差(MAPE): {mape:.1f}%

⭐ 模型表现: {'优秀' if r2 > 0.8 else '良好' if r2 > 0.6 else '一般'}

💡 解读说明:
• R² = {r2:.1%} 的变异能被模型解释
• 平均预测误差约 {mae:.1f} 万元
• {'模型拟合效果很好' if r2 > 0.8 else '模型拟合效果良好' if r2 > 0.6 else '模型还需优化'}

📈 应用建议:
• 适用于车辆估值参考
• 可用于定价策略制定
• 支持投资决策分析
        """
        
        ax4.text(0.1, 0.9, performance_text, transform=ax4.transAxes, 
                fontsize=12, fontfamily='Microsoft YaHei',
                bbox=dict(boxstyle='round,pad=1', facecolor='lightgreen', alpha=0.8),
                verticalalignment='top')
        
        # 调整布局
        plt.tight_layout(pad=3.0)
        self.figure = fig
        self.update_display()
    
    def plot_ml_feature_importance(self, feature_importance, model_type):
        """绘制特征重要性图表"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 强制设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 排序特征重要性
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        features, importances = zip(*sorted_features)
        
        # 创建颜色渐变
        colors = plt.cm.viridis(np.linspace(0, 1, len(features)))
        
        # 绘制水平条形图
        bars = ax.barh(range(len(features)), importances, color=colors)
        
        # 设置标签
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features, fontfamily='Microsoft YaHei')
        ax.set_xlabel('特征重要性', fontfamily='Microsoft YaHei', fontsize=12)
        ax.set_title(f'{model_type} - 特征重要性分析', 
                    fontfamily='Microsoft YaHei', fontsize=14, fontweight='bold')
        
        # 添加数值标签
        for i, (bar, importance) in enumerate(zip(bars, importances)):
            ax.text(importance + 0.01, i, f'{importance:.3f}', 
                   va='center', fontfamily='Microsoft YaHei', fontsize=10)
        
        # 美化图表
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(0, max(importances) * 1.2)
        
        # 添加说明文字
        explanation = f"""
💡 特征重要性解读:
• 数值越大，该特征对{model_type.split('(')[0]}的影响越大
• 图中显示了影响预测结果的关键因素排名
• 可用于指导业务决策和特征工程
        """
        
        ax.text(0.02, 0.98, explanation, transform=ax.transAxes,
               fontfamily='Microsoft YaHei', fontsize=10,
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
               verticalalignment='top')
        
        plt.tight_layout()
        self.update_display()

class CarPredictionModel:
    """汽车数据预测模型"""
    
    def __init__(self):
        self.price_model = None
        self.category_model = None
        self.cluster_model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self, df):
        """准备特征数据"""
        # 选择有用的特征
        feature_columns = ['品牌', '年份', '里程', '燃料类型', '车辆类型', '车龄']
        available_columns = [col for col in feature_columns if col in df.columns]
        
        if len(available_columns) < 3:
            raise ValueError("可用特征太少，需要至少3个特征进行建模")
        
        # 准备特征数据
        X = df[available_columns].copy()
        
        # 处理分类变量
        categorical_columns = X.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].astype(str))
            else:
                # 处理未见过的类别
                X[col] = X[col].astype(str)
                unique_values = X[col].unique()
                for val in unique_values:
                    if val not in self.label_encoders[col].classes_:
                        # 对于未见过的类别，使用最常见的类别替代
                        most_common = df[col].mode()[0] if not df[col].mode().empty else 'unknown'
                        X.loc[X[col] == val, col] = most_common
                X[col] = self.label_encoders[col].transform(X[col])
        
        # 处理缺失值
        X = X.fillna(X.mean())
        
        return X, available_columns
    
    def train_price_prediction(self, df):
        """训练价格预测模型"""
        if '价格' not in df.columns:
            raise ValueError("数据中没有价格字段")
        
        # 准备数据
        X, feature_cols = self.prepare_features(df)
        y = df['价格'].fillna(df['价格'].mean())
        
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 训练模型
        self.price_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.price_model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = self.price_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # 特征重要性
        feature_importance = dict(zip(feature_cols, self.price_model.feature_importances_))
        
        return {
            'mae': mae,
            'r2': r2,
            'feature_importance': feature_importance,
            'model_type': '价格预测(随机森林回归)',
            'y_test': y_test,
            'y_pred': y_pred,
            'feature_names': feature_cols
        }
    
    def train_category_classification(self, df):
        """训练车辆分类模型"""
        if '价格' not in df.columns:
            raise ValueError("数据中没有价格字段用于分类")
        
        # 根据价格创建分类标签
        price_data = df['价格'].fillna(df['价格'].mean())
        price_quantiles = price_data.quantile([0.33, 0.67])
        
        def categorize_price(price):
            if price <= price_quantiles.iloc[0]:
                return '经济型'
            elif price <= price_quantiles.iloc[1]:
                return '中档型'
            else:
                return '豪华型'
        
        # 准备数据
        X, feature_cols = self.prepare_features(df)
        y = price_data.apply(categorize_price)
        
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 训练模型
        self.category_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.category_model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = self.category_model.predict(X_test)
        accuracy = (y_pred == y_test).mean()
        
        # 特征重要性
        feature_importance = dict(zip(feature_cols, self.category_model.feature_importances_))
        
        return {
            'accuracy': accuracy,
            'feature_importance': feature_importance,
            'categories': ['经济型', '中档型', '豪华型'],
            'model_type': '车辆分类(随机森林分类)'
        }
    
    def train_clustering(self, df):
        """训练聚类模型"""
        # 准备数值特征
        numeric_columns = ['价格', '年份', '里程', '车龄']
        available_numeric = [col for col in numeric_columns if col in df.columns]
        
        if len(available_numeric) < 2:
            raise ValueError("可用数值特征太少，需要至少2个数值特征进行聚类")
        
        X = df[available_numeric].fillna(df[available_numeric].mean())
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # K-means聚类
        self.cluster_model = KMeans(n_clusters=4, random_state=42)
        clusters = self.cluster_model.fit_predict(X_scaled)
        
        # 分析聚类结果
        cluster_analysis = {}
        for i in range(4):
            cluster_data = df[clusters == i]
            cluster_analysis[f'聚类{i+1}'] = {
                '数量': len(cluster_data),
                '平均价格': cluster_data['价格'].mean() if '价格' in cluster_data.columns else 0,
                '特征': f"样本数: {len(cluster_data)}"
            }
        
        return {
            'clusters': clusters,
            'cluster_analysis': cluster_analysis,
            'model_type': 'K-Means聚类分析'
        }
    
    def predict_price(self, features):
        """预测价格"""
        if self.price_model is None:
            raise ValueError("价格预测模型未训练")
        
        return self.price_model.predict([features])[0]
    
    def predict_category(self, features):
        """预测车辆类别"""
        if self.category_model is None:
            raise ValueError("分类模型未训练")
        
        return self.category_model.predict([features])[0]

class DataLoadThread(QThread):
    """数据加载线程"""
    progress_updated = Signal(int)
    data_loaded = Signal(pd.DataFrame)
    error_occurred = Signal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            self.progress_updated.emit(20)
            df = pd.read_csv(self.file_path, encoding='utf-8-sig')
            
            self.progress_updated.emit(60)
            # 数据清洗
            df = df.dropna(how='all')
            
            self.progress_updated.emit(80)
            # 数据类型转换
            df['价格'] = pd.to_numeric(df['价格'], errors='coerce')
            df['年份'] = pd.to_numeric(df['年份'], errors='coerce')
            df['里程'] = pd.to_numeric(df['里程'], errors='coerce')
            df['车龄'] = pd.to_numeric(df['车龄'], errors='coerce')
            
            self.progress_updated.emit(100)
            self.data_loaded.emit(df)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class CarDataVisualizer(QMainWindow):
    """汽车数据可视化主窗口"""
    
    def __init__(self):
        super().__init__()
        self.df = None
        self.ml_model = CarPredictionModel() if ML_AVAILABLE else None
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("🚗 汽车数据可视化分析平台")
        self.setGeometry(80, 80, 1500, 950)
        self.setMinimumSize(1200, 800)
        
        # 中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 使用更优雅的间距
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 顶部工具栏
        self.create_toolbar(main_layout)
        
        # 主要内容区域
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(3)
        content_splitter.setChildrenCollapsible(False)
        
        # 左侧控制面板
        self.create_control_panel(content_splitter)
        
        # 右侧可视化区域
        self.create_visualization_area(content_splitter)
        
        # 设置分割器比例 - 左侧稍微窄一些，右侧更宽
        content_splitter.setSizes([320, 1180])
        content_splitter.setStretchFactor(0, 0)  # 左侧不拉伸
        content_splitter.setStretchFactor(1, 1)  # 右侧可拉伸
        
        main_layout.addWidget(content_splitter)
        
        # 状态栏
        self.create_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def create_toolbar(self, layout):
        """创建工具栏"""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setStyleSheet("""
            QFrame#toolbar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border: 1px solid #e2e8f0;
                border-radius: 15px;
                padding: 8px;
                margin-bottom: 5px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 10, 15, 10)
        toolbar_layout.setSpacing(12)
        
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(12)
        
        # 加载数据按钮
        self.load_btn = QPushButton("📂 加载数据")
        self.load_btn.setMinimumHeight(45)
        self.load_btn.setMinimumWidth(130)
        self.load_btn.setObjectName("primaryBtn")
        
        # 导出图表按钮
        self.export_btn = QPushButton("💾 导出图表")
        self.export_btn.setMinimumHeight(45)
        self.export_btn.setMinimumWidth(130)
        self.export_btn.setEnabled(False)
        
        # 数据概览按钮
        self.overview_btn = QPushButton("📊 数据概览")
        self.overview_btn.setMinimumHeight(45)
        self.overview_btn.setMinimumWidth(130)
        self.overview_btn.setEnabled(False)
        
        # 机器学习按钮
        self.ml_btn = QPushButton("🤖 智能建模")
        self.ml_btn.setMinimumHeight(45)
        self.ml_btn.setMinimumWidth(130)
        self.ml_btn.setEnabled(ML_AVAILABLE)
        if not ML_AVAILABLE:
            self.ml_btn.setToolTip("需要安装scikit-learn: pip install scikit-learn")
        
        # 添加按钮到布局
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.overview_btn)
        button_layout.addWidget(self.ml_btn)
        
        # 右侧状态区域
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(15)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(220)
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setVisible(False)
        
        # 状态指示器
        self.status_indicator = QLabel("🔴 未连接")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-weight: 500;
                font-size: 11px;
                padding: 5px 10px;
                background: rgba(255,255,255,0.8);
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_indicator)
        
        # 添加到主工具栏布局
        toolbar_layout.addWidget(button_container)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(status_container)
        
        layout.addWidget(toolbar)
    
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_widget = QWidget()
        control_widget.setObjectName("controlPanel")
        control_widget.setStyleSheet("""
            QWidget#controlPanel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border-radius: 15px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(20)
        
        # 数据信息组
        info_group = QGroupBox("📊 数据概况")
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(15, 25, 15, 15)
        info_layout.setSpacing(10)
        
        self.data_info_label = QLabel("🔍 请加载汽车数据文件开始分析")
        self.data_info_label.setWordWrap(True)
        self.data_info_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                line-height: 1.6;
                padding: 8px;
                background: rgba(102, 126, 234, 0.05);
                border-radius: 8px;
                border: 1px dashed #cbd5e0;
            }
        """)
        info_layout.addWidget(self.data_info_label)
        
        control_layout.addWidget(info_group)
        
        # 图表选择组
        chart_group = QGroupBox("📈 可视化选择")
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(15, 25, 15, 15)
        chart_layout.setSpacing(12)
        
        # 图表类型标签
        chart_label = QLabel("🎨 选择图表类型:")
        chart_label.setStyleSheet("""
            QLabel {
                font-weight: 600;
                color: #374151;
                font-size: 13px;
                margin-bottom: 5px;
            }
        """)
        chart_layout.addWidget(chart_label)
        
        self.chart_combo = QComboBox()
        chart_items = [
            "品牌分布 (柱状图)",
            "价格分布 (饼图)", 
            "价格vs年份 (散点图)",
            "年份趋势 (折线图)",
            "燃料类型对比 (柱状图)",
            "价格分布 (直方图)",
            "里程分布 (箱线图)"
        ]
        
        # 如果机器学习可用，添加ML图表选项
        if ML_AVAILABLE:
            chart_items.extend([
                "--- 智能分析 ---",
                "价格预测效果图",
                "特征重要性分析"
            ])
        
        self.chart_combo.addItems(chart_items)
        chart_layout.addWidget(self.chart_combo)
        
        # 生成图表按钮
        self.generate_btn = QPushButton("🎨 生成可视化图表")
        self.generate_btn.setMinimumHeight(42)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        chart_layout.addWidget(self.generate_btn)
        
        control_layout.addWidget(chart_group)
        
        # 统计信息组
        stats_group = QGroupBox("📋 数据洞察")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setContentsMargins(15, 25, 15, 15)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(220)
        self.stats_text.setPlainText("📈 数据加载后将显示详细统计信息和趋势分析...")
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background: #fafbfc;
                border: 1px solid #f1f5f9;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 11px;
                line-height: 1.5;
                color: #374151;
            }
        """)
        stats_layout.addWidget(self.stats_text)
        
        control_layout.addWidget(stats_group)
        control_layout.addStretch()
        
        parent.addWidget(control_widget)
    
    def create_visualization_area(self, parent):
        """创建右侧可视化区域"""
        viz_widget = QWidget()
        viz_widget.setObjectName("vizWidget")
        viz_widget.setStyleSheet("""
            QWidget#vizWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border-radius: 15px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        viz_layout = QVBoxLayout(viz_widget)
        viz_layout.setContentsMargins(15, 15, 15, 15)
        viz_layout.setSpacing(10)
        
        # 标签页容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background-color: white;
                margin-top: 5px;
            }
            
            QTabBar::tab {
                background: transparent;
                padding: 15px 25px;
                margin-right: 6px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-weight: 500;
                color: #64748b;
                min-width: 120px;
                font-size: 13px;
            }
            
            QTabBar::tab:selected {
                background: white;
                color: #667eea;
                border-bottom: 3px solid #667eea;
                font-weight: 600;
            }
            
            QTabBar::tab:hover {
                background: rgba(102, 126, 234, 0.08);
                color: #667eea;
            }
        """)
        
        # 图表标签页
        chart_tab = QWidget()
        chart_layout = QVBoxLayout(chart_tab)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        
        # 图表画布
        self.chart_canvas = ChartCanvas()
        chart_layout.addWidget(self.chart_canvas)
        
        self.tab_widget.addTab(chart_tab, "📊 可视化图表")
        
        # 数据表格标签页
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        table_layout.setContentsMargins(20, 20, 20, 20)
        
        # 表格头部信息
        table_header = QLabel("📋 数据表格浏览")
        table_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #374151;
                padding: 10px 0;
                border-bottom: 2px solid #e2e8f0;
                margin-bottom: 15px;
            }
        """)
        table_layout.addWidget(table_header)
        
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                gridline-color: #f1f5f9;
                font-size: 11px;
                alternate-background-color: #fafbfc;
            }
            
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.1), stop:1 rgba(118, 75, 162, 0.1));
                color: #1a202c;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 12px;
                border: none;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        table_layout.addWidget(self.data_table)
        
        self.tab_widget.addTab(table_tab, "📋 数据表格")
        
        # 机器学习标签页
        if ML_AVAILABLE:
            ml_tab = QWidget()
            ml_layout = QVBoxLayout(ml_tab)
            ml_layout.setContentsMargins(20, 20, 20, 20)
            
            # ML头部信息
            ml_header = QLabel("🤖 智能建模分析")
            ml_header.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: 600;
                    color: #374151;
                    padding: 10px 0;
                    border-bottom: 2px solid #e2e8f0;
                    margin-bottom: 15px;
                }
            """)
            ml_layout.addWidget(ml_header)
            
            # 模型结果显示
            self.ml_results = QTextEdit()
            self.ml_results.setPlainText("""🤖 AI智能建模平台

欢迎使用汽车数据智能分析系统！

📊 支持的智能模型:
• 🎯 价格预测模型 - 基于随机森林回归算法
• 🏷️ 车辆分类模型 - 智能车型分类系统  
• 🔍 聚类分析模型 - 发现数据中的隐藏模式

🚀 使用步骤:
1. 加载汽车数据文件
2. 点击"智能建模"按钮开始训练
3. 查看详细的模型分析结果
4. 切换到图表视图查看可视化效果

⭐ 等待数据加载完成后开始您的AI之旅...""")
            
            self.ml_results.setStyleSheet("""
                QTextEdit {
                    background: #fafbfc;
                    border: 1px solid #f1f5f9;
                    border-radius: 8px;
                    padding: 20px;
                    font-family: 'Microsoft YaHei', sans-serif;
                    font-size: 12px;
                    line-height: 1.8;
                    color: #374151;
                }
            """)
            ml_layout.addWidget(self.ml_results)
            
            self.tab_widget.addTab(ml_tab, "🤖 智能建模")
        
        viz_layout.addWidget(self.tab_widget)
        parent.addWidget(viz_widget)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8fafc);
                border-top: 1px solid #e2e8f0;
                padding: 5px;
                font-size: 11px;
                color: #64748b;
            }
            QStatusBar QLabel {
                font-size: 11px;
                color: #64748b;
                padding: 2px 8px;
                font-weight: 500;
            }
        """)
        
        self.status_label = QLabel("🚗 系统就绪 - 请加载汽车数据文件")
        self.status_bar.addWidget(self.status_label)
        
        self.data_status = QLabel("数据: 未加载")
        self.status_bar.addPermanentWidget(self.data_status)
        
        # 时间显示
        self.time_label = QLabel()
        self.update_time()
        self.status_bar.addPermanentWidget(self.time_label)
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
    
    def apply_styles(self):
        """应用现代化简约样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #e2e8f0);
                font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                color: #1a202c;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                margin-top: 20px;
                padding-top: 20px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 8px 16px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                padding: 12px 24px;
                font-size: 13px;
                min-height: 20px;
                letter-spacing: 0.5px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b46c1);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(90, 103, 216, 0.4);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c51bf, stop:1 #553c9a);
                transform: translateY(0px);
            }
            
            QPushButton:disabled {
                background: #e2e8f0;
                color: #a0aec0;
                box-shadow: none;
            }
            
            QComboBox {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 15px;
                background: white;
                font-size: 13px;
                min-width: 200px;
                selection-background-color: #667eea;
            }
            
            QComboBox:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #667eea;
                margin-right: 10px;
            }
            
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background-color: white;
                gridline-color: #f1f5f9;
                font-size: 12px;
                alternate-background-color: #fafbfc;
            }
            
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f5f9;
            }
            
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.1), stop:1 rgba(118, 75, 162, 0.1));
                color: #1a202c;
            }
            
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 12px;
                border: none;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', 'SF Mono', monospace;
                line-height: 1.5;
            }
            
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background-color: white;
                margin-top: -1px;
            }
            
            QTabBar::tab {
                background: transparent;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
                color: #64748b;
                min-width: 100px;
            }
            
            QTabBar::tab:selected {
                background: white;
                color: #667eea;
                border-bottom: 3px solid #667eea;
                font-weight: 600;
            }
            
            QTabBar::tab:hover {
                background: rgba(102, 126, 234, 0.05);
                color: #667eea;
            }
            
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #e2e8f0;
                text-align: center;
                font-weight: 600;
                color: white;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                margin: 1px;
            }
            
            QLabel {
                color: #2d3748;
                font-size: 12px;
                line-height: 1.5;
            }
            
            QSplitter::handle {
                background-color: #e2e8f0;
                width: 2px;
                border-radius: 1px;
            }
            
            QSplitter::handle:hover {
                background-color: #667eea;
            }
            
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: #cbd5e0;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a0aec0;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0;
            }
        """)
    
    def setup_connections(self):
        """设置信号连接"""
        self.load_btn.clicked.connect(self.load_data)
        self.generate_btn.clicked.connect(self.generate_chart)
        self.export_btn.clicked.connect(self.export_chart)
        self.overview_btn.clicked.connect(self.show_overview)
        if ML_AVAILABLE:
            self.ml_btn.clicked.connect(self.run_machine_learning)
    
    def load_data(self):
        """加载数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择汽车数据文件", "", 
            "CSV文件 (*.csv);;Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        
        if file_path:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("正在加载数据...")
            
            self.load_thread = DataLoadThread(file_path)
            self.load_thread.progress_updated.connect(self.progress_bar.setValue)
            self.load_thread.data_loaded.connect(self.on_data_loaded)
            self.load_thread.error_occurred.connect(self.on_load_error)
            self.load_thread.start()
    
    def on_data_loaded(self, df):
        """数据加载完成"""
        self.df = df
        self.progress_bar.setVisible(False)
        
        # 更新界面
        self.update_data_info()
        self.update_data_table()
        self.update_statistics()
        
        # 启用按钮
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.overview_btn.setEnabled(True)
        if ML_AVAILABLE:
            self.ml_btn.setEnabled(True)
        
        # 更新状态指示器
        self.status_indicator.setText("🟢 数据已加载")
        self.status_label.setText("✅ 数据加载完成，可以开始分析")
        self.data_status.setText(f"数据: {len(self.df):,}行×{len(self.df.columns)}列")
        
        QMessageBox.information(self, "✅ 加载成功", 
                               f"🎉 汽车数据加载成功！\n\n📊 数据规模:\n• 记录数: {len(self.df):,} 条\n• 字段数: {len(self.df.columns)} 个\n\n🚀 现在可以开始生成图表和AI建模分析了！")
    
    def on_load_error(self, error_msg):
        """数据加载错误"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ 数据加载失败")
        QMessageBox.critical(self, "❌ 加载失败", f"数据加载失败：\n{error_msg}")
    
    def update_data_info(self):
        """更新数据信息"""
        if self.df is None:
            return
        
        info_text = f"""📊 数据集概览

🎯 规模统计
• 数据记录: {len(self.df):,} 条
• 字段数量: {len(self.df.columns)} 个
• 数值字段: {len(self.df.select_dtypes(include=[np.number]).columns)} 个
• 文本字段: {len(self.df.select_dtypes(include=['object']).columns)} 个

💎 质量指标
• 数据完整率: {((len(self.df) * len(self.df.columns) - self.df.isnull().sum().sum()) / (len(self.df) * len(self.df.columns)) * 100):.1f}%
• 缺失值数量: {self.df.isnull().sum().sum():,} 个

📋 字段列表
{', '.join(self.df.columns.tolist()[:6])}{'...' if len(self.df.columns) > 6 else ''}"""
        
        self.data_info_label.setText(info_text)
        self.data_info_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 11px;
                line-height: 1.8;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(102, 126, 234, 0.05), stop:1 rgba(118, 75, 162, 0.03));
                border-radius: 10px;
                border: 1px solid #e2e8f0;
                font-family: 'Microsoft YaHei', sans-serif;
            }
        """)
    
    def update_data_table(self):
        """更新数据表格"""
        if self.df is None:
            return
        
        # 限制显示行数
        display_rows = min(100, len(self.df))
        display_df = self.df.head(display_rows)
        
        self.data_table.setRowCount(len(display_df))
        self.data_table.setColumnCount(len(display_df.columns))
        self.data_table.setHorizontalHeaderLabels(display_df.columns.tolist())
        
        # 填充数据
        for i in range(len(display_df)):
            for j, col in enumerate(display_df.columns):
                value = display_df.iloc[i, j]
                display_value = str(value)
                
                if len(display_value) > 30:
                    display_value = display_value[:27] + "..."
                
                item = QTableWidgetItem(display_value)
                
                if display_df[col].dtype in ['int64', 'float64']:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if pd.notna(value):
                        item.setForeground(QColor(0, 100, 200))
                elif pd.isna(value):
                    item.setText("--")
                    item.setForeground(QColor(150, 150, 150))
                
                self.data_table.setItem(i, j, item)
        
        # 调整列宽
        self.data_table.resizeColumnsToContents()
        
        # 限制最大列宽
        for j in range(self.data_table.columnCount()):
            current_width = self.data_table.columnWidth(j)
            if current_width > 200:
                self.data_table.setColumnWidth(j, 200)
            elif current_width < 100:
                self.data_table.setColumnWidth(j, 100)
    
    def update_statistics(self):
        """更新统计信息"""
        if self.df is None:
            return
        
        stats_text = "📊 汽车数据统计摘要:\n\n"
        
        # 品牌统计
        if '品牌' in self.df.columns:
            brand_count = self.df['品牌'].nunique()
            top_brands = self.df['品牌'].value_counts().head(3)
            stats_text += f"🚗 品牌统计:\n"
            stats_text += f"• 品牌总数: {brand_count} 个\n"
            stats_text += f"• TOP3品牌: {', '.join(top_brands.index.tolist())}\n\n"
        
        # 价格统计
        if '价格' in self.df.columns:
            price_data = self.df['价格'].dropna()
            stats_text += f"💰 价格统计:\n"
            stats_text += f"• 平均价格: {price_data.mean():.1f} 万元\n"
            stats_text += f"• 价格中位数: {price_data.median():.1f} 万元\n"
            stats_text += f"• 价格范围: {price_data.min():.1f} - {price_data.max():.1f} 万元\n\n"
        
        # 年份统计
        if '年份' in self.df.columns:
            year_data = self.df['年份'].dropna()
            stats_text += f"📅 年份统计:\n"
            stats_text += f"• 年份范围: {year_data.min():.0f} - {year_data.max():.0f}\n"
            stats_text += f"• 平均年份: {year_data.mean():.0f}\n\n"
        
        # 燃料类型统计
        if '燃料类型' in self.df.columns:
            fuel_counts = self.df['燃料类型'].value_counts()
            stats_text += f"⛽ 燃料类型:\n"
            for fuel, count in fuel_counts.head(4).items():
                percentage = count / len(self.df) * 100
                stats_text += f"• {fuel}: {count}辆 ({percentage:.1f}%)\n"
        
        self.stats_text.setPlainText(stats_text)
    
    def generate_chart(self):
        """生成图表"""
        if self.df is None:
            QMessageBox.warning(self, "提示", "请先加载数据")
            return
        
        chart_type = self.chart_combo.currentText()
        
        try:
            if "品牌分布" in chart_type:
                self.chart_canvas.plot_brand_distribution(self.df)
            elif "价格分布" in chart_type and "饼图" in chart_type:
                self.chart_canvas.plot_price_distribution(self.df)
            elif "价格vs年份" in chart_type:
                self.chart_canvas.plot_price_vs_year_scatter(self.df)
            elif "年份趋势" in chart_type:
                self.chart_canvas.plot_year_trend(self.df)
            elif "燃料类型对比" in chart_type:
                self.chart_canvas.plot_fuel_type_comparison(self.df)
            elif "价格分布" in chart_type and "直方图" in chart_type:
                self.chart_canvas.plot_price_histogram(self.df)
            elif "里程分布" in chart_type:
                self.chart_canvas.plot_mileage_boxplot(self.df)
            elif "价格预测效果图" in chart_type:
                if hasattr(self, 'price_prediction_results'):
                    self.chart_canvas.plot_ml_price_prediction(
                        self.price_prediction_results['y_test'],
                        self.price_prediction_results['y_pred'],
                        self.price_prediction_results['mae'],
                        self.price_prediction_results['r2']
                    )
                else:
                    QMessageBox.warning(self, "提示", "请先运行智能建模生成价格预测模型")
                    return
            elif "特征重要性分析" in chart_type:
                if hasattr(self, 'price_prediction_results'):
                    self.chart_canvas.plot_ml_feature_importance(
                        self.price_prediction_results['feature_importance'],
                        self.price_prediction_results['model_type']
                    )
                else:
                    QMessageBox.warning(self, "提示", "请先运行智能建模生成价格预测模型")
                    return
            elif "--- 智能分析 ---" in chart_type:
                QMessageBox.information(self, "提示", "请选择具体的智能分析图表类型")
                return
            
            # 切换到图表标签页
            self.tab_widget.setCurrentIndex(0)
            
            QMessageBox.information(self, "✅ 图表生成成功", f"🎨 {chart_type} 生成完成！")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 生成失败", f"图表生成失败:\n{str(e)}")
    
    def export_chart(self):
        """导出图表"""
        if self.df is None:
            QMessageBox.warning(self, "提示", "请先生成图表")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图表", "car_chart.png", 
            "PNG文件 (*.png);;PDF文件 (*.pdf)"
        )
        
        if file_path:
            try:
                self.chart_canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight',
                                               facecolor='white', edgecolor='none')
                QMessageBox.information(self, "✅ 导出成功", f"图表已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "❌ 导出失败", f"导出失败:\n{str(e)}")
    
    def show_overview(self):
        """显示数据概览"""
        if self.df is None:
            QMessageBox.warning(self, "提示", "请先加载数据")
            return
        
        overview_text = f"""📊 汽车数据概览报告

📈 数据规模:
• 总记录数: {len(self.df):,} 条
• 字段数量: {len(self.df.columns)} 个
• 数据完整率: {((len(self.df) * len(self.df.columns) - self.df.isnull().sum().sum()) / (len(self.df) * len(self.df.columns)) * 100):.1f}%

🚗 品牌分析:
• 品牌总数: {self.df['品牌'].nunique()} 个
• 热门品牌: {', '.join(self.df['品牌'].value_counts().head(5).index.tolist())}

💰 价格分析:
• 平均价格: {self.df['价格'].mean():.1f} 万元
• 价格中位数: {self.df['价格'].median():.1f} 万元
• 价格范围: {self.df['价格'].min():.1f} - {self.df['价格'].max():.1f} 万元

📅 年份分析:
• 年份范围: {self.df['年份'].min():.0f} - {self.df['年份'].max():.0f}
• 平均年份: {self.df['年份'].mean():.0f}

⛽ 燃料类型分布:"""
        
        fuel_counts = self.df['燃料类型'].value_counts()
        for fuel, count in fuel_counts.items():
            percentage = count / len(self.df) * 100
            overview_text += f"\n• {fuel}: {count}辆 ({percentage:.1f}%)"
        
        # 创建概览对话框
        overview_dialog = QMessageBox(self)
        overview_dialog.setWindowTitle("📊 数据概览")
        overview_dialog.setText("🎉 汽车数据概览报告")
        overview_dialog.setDetailedText(overview_text)
        overview_dialog.setIcon(QMessageBox.Information)
        overview_dialog.exec()
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"🕐 {current_time}")
    
    def run_machine_learning(self):
        """运行机器学习分析"""
        if self.df is None:
            QMessageBox.warning(self, "提示", "请先加载数据")
            return
        
        if not ML_AVAILABLE:
            QMessageBox.warning(self, "功能不可用", "机器学习功能需要安装scikit-learn库\n\n安装命令: pip install scikit-learn")
            return
        
        try:
            self.status_label.setText("🤖 正在训练机器学习模型...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            results_text = "🤖 汽车数据智能建模分析报告\n"
            results_text += "=" * 50 + "\n\n"
            
            # 1. 价格预测模型
            self.progress_bar.setValue(25)
            try:
                price_results = self.ml_model.train_price_prediction(self.df)
                results_text += f"📊 {price_results['model_type']}\n"
                results_text += f"• 平均绝对误差(MAE): {price_results['mae']:.2f} 万元\n"
                results_text += f"• 决定系数(R²): {price_results['r2']:.3f}\n"
                results_text += f"• 模型表现: {'优秀' if price_results['r2'] > 0.8 else '良好' if price_results['r2'] > 0.6 else '一般'}\n"
                
                # 特征重要性
                results_text += "\n🎯 特征重要性排名:\n"
                sorted_features = sorted(price_results['feature_importance'].items(), 
                                       key=lambda x: x[1], reverse=True)
                for i, (feature, importance) in enumerate(sorted_features[:5], 1):
                    results_text += f"  {i}. {feature}: {importance:.3f}\n"
                results_text += "\n"
                
                # 生成价格预测效果图表
                results_text += "📈 已生成价格预测效果图表，请切换到图表视图查看详细分析\n\n"
                
                # 保存价格预测结果用于图表绘制
                self.price_prediction_results = price_results
                
            except Exception as e:
                results_text += f"❌ 价格预测模型训练失败: {str(e)}\n\n"
            
            # 2. 车辆分类模型
            self.progress_bar.setValue(50)
            try:
                category_results = self.ml_model.train_category_classification(self.df)
                results_text += f"📋 {category_results['model_type']}\n"
                results_text += f"• 分类准确率: {category_results['accuracy']:.3f}\n"
                results_text += f"• 分类类别: {', '.join(category_results['categories'])}\n"
                results_text += f"• 模型表现: {'优秀' if category_results['accuracy'] > 0.85 else '良好' if category_results['accuracy'] > 0.75 else '一般'}\n"
                
                # 特征重要性
                results_text += "\n🎯 分类特征重要性:\n"
                sorted_features = sorted(category_results['feature_importance'].items(), 
                                       key=lambda x: x[1], reverse=True)
                for i, (feature, importance) in enumerate(sorted_features[:5], 1):
                    results_text += f"  {i}. {feature}: {importance:.3f}\n"
                results_text += "\n"
                
            except Exception as e:
                results_text += f"❌ 车辆分类模型训练失败: {str(e)}\n\n"
            
            # 3. 聚类分析
            self.progress_bar.setValue(75)
            try:
                cluster_results = self.ml_model.train_clustering(self.df)
                results_text += f"🔍 {cluster_results['model_type']}\n"
                results_text += "• 聚类结果分析:\n"
                
                for cluster_name, info in cluster_results['cluster_analysis'].items():
                    results_text += f"  {cluster_name}: {info['数量']}辆车, "
                    if '平均价格' in info and info['平均价格'] > 0:
                        results_text += f"平均价格 {info['平均价格']:.1f}万元\n"
                    else:
                        results_text += f"{info['特征']}\n"
                results_text += "\n"
                
            except Exception as e:
                results_text += f"❌ 聚类分析失败: {str(e)}\n\n"
            
            # 4. 应用建议
            self.progress_bar.setValue(90)
            results_text += "💡 智能建议:\n"
            results_text += "• 价格预测: 可用于车辆估值和定价参考\n"
            results_text += "• 车辆分类: 有助于市场细分和产品定位\n"
            results_text += "• 聚类分析: 发现车辆的自然分组模式\n"
            results_text += "• 特征重要性: 指导业务决策的关键因素\n\n"
            
            results_text += "📈 模型训练完成！可用于新车预测和分析。\n"
            results_text += f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 显示结果
            self.ml_results.setPlainText(results_text)
            
            # 切换到机器学习标签页
            for i in range(self.tab_widget.count()):
                if "智能建模" in self.tab_widget.tabText(i):
                    self.tab_widget.setCurrentIndex(i)
                    break
            
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            self.status_label.setText("✅ 机器学习建模完成")
            
            # 自动生成价格预测效果图表
            if hasattr(self, 'price_prediction_results'):
                self.chart_canvas.plot_ml_price_prediction(
                    self.price_prediction_results['y_test'],
                    self.price_prediction_results['y_pred'],
                    self.price_prediction_results['mae'],
                    self.price_prediction_results['r2']
                )
            
            QMessageBox.information(self, "✅ 建模成功", 
                                   "🤖 智能建模完成！\n\n已训练完成:\n• 价格预测模型\n• 车辆分类模型\n• 聚类分析模型\n\n📊 价格预测效果图已自动生成\n请查看图表视图和建模结果标签页")
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            self.status_label.setText("❌ 建模失败")
            QMessageBox.critical(self, "❌ 建模失败", f"机器学习建模失败:\n{str(e)}")

def main():
    """主函数"""
    try:
        print("🚀 启动汽车数据可视化工具...")
        app = QApplication(sys.argv)
        
        app.setApplicationName("汽车数据可视化工具")
        app.setApplicationDisplayName("汽车数据可视化")
        app.setApplicationVersion("1.0.0")
        
        window = CarDataVisualizer()
        window.show()
        
        print("✅ 启动成功！")
        print("📊 支持7种图表类型")
        print("🎨 简约现代化界面")
        print("🔤 完美中文支持")
        print("💡 请点击'加载数据'开始使用...")
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
