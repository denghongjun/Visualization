# 香水销售客户与营销数据行为分析与决策支持系统

## 项目简介
本项目使用数据仓库与数据挖掘技术，基于Python语言，深入分析香水销售数据，识别客户行为模式，为制定精准营销策略和商业决策提供数据支持。

## 项目结构
```
perfume_sales_analysis/
│
├── data/                   # 数据文件目录
│   ├── raw/               # 原始数据
│   └── processed/         # 处理后的数据
│
├── scripts/               # Python脚本目录
│   ├── 01_data_generation.py      # 数据生成
│   ├── 02_data_preprocessing.py   # 数据预处理
│   ├── 03_data_warehouse.py       # 数据仓库构建
│   ├── 04_customer_segmentation.py # 客户细分
│   ├── 05_association_rules.py    # 关联规则挖掘
│   └── 06_visualization.py        # 数据可视化
│
├── output/                # 输出结果目录
├── figures/               # 图表目录
├── requirements.txt       # 项目依赖
├── main.py               # 主程序入口
└── 课程设计报告.md        # 课程设计报告

```

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行项目
```bash
python main.py
```

## 主要功能
1. **数据采集与预处理**：数据清洗、特征工程、RFM分析
2. **数据仓库设计**：星形模型设计与实现
3. **客户细分**：基于K-Means聚类算法
4. **关联规则挖掘**：基于Apriori算法
5. **可视化分析**：多维度数据可视化展示

## 作者信息
- 姓名：邓宏军
- 学号：2024302726
- 班级：数据科学与大数据技术 1班



