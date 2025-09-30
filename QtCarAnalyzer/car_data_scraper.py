#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车数据爬虫系统 - 车168专版
从车168网站爬取真实汽车数据，目标20000+条数据
专注于车168一个数据源，确保数据质量和稳定性
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import logging
from fake_useragent import UserAgent
import json
import re
from urllib.parse import urljoin, urlparse, quote
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading
from tqdm import tqdm
from datetime import datetime
import pickle

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CarDataScraper:
    """汽车数据爬虫类 - 车168专版"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.data = []
        self.driver = None
        self.scraped_urls = set()  # 防重复爬取
        
        # 动态延迟配置
        self.request_delay = (0.5, 2.0)
        self.page_delay = (1.0, 3.0)
        
        # 设置通用请求头
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        self.session.headers.update(self.headers)
        
        # 代理池
        self.proxies = []
        self.proxy_index = 0
        self.load_proxies_from_file()
        
        # 检查点文件
        self.checkpoint_file = 'scraper_checkpoint.pkl'
        
    def load_checkpoint(self):
        """加载检查点"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'rb') as f:
                    checkpoint = pickle.load(f)
                    self.data = checkpoint.get('data', [])
                    self.scraped_urls = checkpoint.get('scraped_urls', set())
                    logger.info(f"从检查点恢复: {len(self.data)} 条数据, {len(self.scraped_urls)} 个已爬取URL")
                    return True
        except Exception as e:
            logger.warning(f"加载检查点失败: {e}")
        return False
    
    def save_checkpoint(self):
        """保存检查点"""
        try:
            checkpoint = {
                'data': self.data,
                'scraped_urls': self.scraped_urls,
                'timestamp': datetime.now()
            }
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint, f)
            logger.info(f"检查点已保存: {len(self.data)} 条数据")
        except Exception as e:
            logger.warning(f"保存检查点失败: {e}")
    
    def setup_driver(self):
        """设置Selenium WebDriver"""
        if self.driver is None:
            try:
                options = Options()
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--disable-images')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-popup-blocking')
                options.add_argument(f'--user-agent={self.ua.random}')
                options.add_experimental_option('useAutomationExtension', False)
                options.add_experimental_option('excludeSwitches', ['enable-automation'])

                self.driver = webdriver.Chrome(options=options)
                self.driver.set_page_load_timeout(30)
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                logger.info("WebDriver 初始化成功")
                return True
            except Exception as e:
                logger.error(f"WebDriver 初始化失败: {str(e)}")
                return False
        return True
    
    def close_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("WebDriver 已关闭")
            except Exception as e:
                logger.warning(f"关闭WebDriver时出错: {str(e)}")
        
    def get_random_delay(self, min_delay=None, max_delay=None):
        """获取随机延迟时间"""
        if min_delay is None or max_delay is None:
            min_delay, max_delay = self.request_delay
        return random.uniform(min_delay, max_delay)
        
    def safe_request(self, url, max_retries=3):
        """安全的网络请求"""
        for attempt in range(max_retries):
            try:
                # 随机延迟
                delay = self.get_random_delay()
                time.sleep(delay)
                
                # 更新User-Agent
                self.session.headers['User-Agent'] = self.ua.random

                # 轮换代理
                proxies = self._get_next_proxy()

                response = self.session.get(url, timeout=15, proxies=proxies)
                response.raise_for_status()
                
                # 自动检测编码
                if response.encoding == 'ISO-8859-1':
                    response.encoding = response.apparent_encoding
                elif not response.encoding:
                    response.encoding = 'utf-8'
                    
                return response
                
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {url} - {str(e)}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(self.get_random_delay(2, 5) * (attempt + 1))
        
        return None
    
    def load_proxies_from_file(self, filename='proxies.txt'):
        """从文件加载代理列表"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        proxy = line.strip()
                        if proxy and not proxy.startswith('#'):
                            if '://' not in proxy:
                                proxy = f'http://{proxy}'
                            self.proxies.append({'http': proxy, 'https': proxy})
                logger.info(f"加载了 {len(self.proxies)} 个代理")
            else:
                logger.info("代理文件不存在，使用直连")
        except Exception as e:
            logger.warning(f"加载代理文件失败: {e}")
    
    def _get_next_proxy(self):
        """获取下一个代理"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _city_name_map(self, city_code):
        """城市代码转中文名"""
        city_map = {
            'beijing': '北京', 'bj': '北京',
            'shanghai': '上海', 'sh': '上海',
            'guangzhou': '广州', 'gz': '广州',
            'shenzhen': '深圳', 'sz': '深圳',
            'hangzhou': '杭州', 'hz': '杭州',
            'nanjing': '南京', 'nj': '南京',
            'wuhan': '武汉', 'wh': '武汉',
            'chengdu': '成都', 'cd': '成都',
            'xian': '西安', 'xa': '西安',
            'chongqing': '重庆', 'cq': '重庆',
            'tianjin': '天津', 'tj': '天津',
            'qingdao': '青岛', 'qd': '青岛',
            'dalian': '大连', 'dl': '大连',
            'suzhou': '苏州', 'su': '苏州',
            'dongguan': '东莞', 'dg': '东莞',
            'foshan': '佛山', 'fs': '佛山',
            'zhengzhou': '郑州', 'zz': '郑州',
            'changsha': '长沙', 'cs': '长沙',
            'jinan': '济南', 'jn': '济南',
            'hefei': '合肥', 'hf': '合肥',
            'shenyang': '沈阳', 'sy': '沈阳',
            'changchun': '长春', 'cc': '长春',
            'harbin': '哈尔滨', 'hrb': '哈尔滨',
            'taiyuan': '太原', 'ty': '太原',
            'taizhou': '台州', 'tz': '台州',
            'ningbo': '宁波', 'nb': '宁波',
            'wuxi': '无锡', 'wx': '无锡',
            'changzhou': '常州',
            'xuzhou': '徐州',
            'yantai': '烟台',
            'weifang': '潍坊',
            'linyi': '临沂',
            'zibo': '淄博',
            'weihai': '威海',
            'dongying': '东营',
            'binzhou': '滨州',
            'dezhou': '德州',
            'liaocheng': '聊城',
            'heze': '菏泽',
            'zaozhuang': '枣庄',
            'jining': '济宁',
            'taian': '泰安',
            'rizhao': '日照',
            'laiwu': '莱芜',
            'huaian': '淮安',
            'yancheng': '盐城',
            'yangzhou': '扬州',
            'zhenjiang': '镇江',
            'suqian': '宿迁',
            'lianyungang': '连云港',
            'shaoxing': '绍兴',
            'jiaxing': '嘉兴',
            'huzhou': '湖州',
            'lishui': '丽水',
            'quzhou': '衢州',
            'zhoushan': '舟山',
            'taizhou_zj': '台州',
            'wenzhou': '温州',
            'kunming': '昆明', 'km': '昆明',
            'lanzhou': '兰州', 'lz': '兰州',
            'urumqi': '乌鲁木齐',
            'guiyang': '贵阳', 'gy': '贵阳',
            'nanning': '南宁', 'nn': '南宁',
            'haikou': '海口', 'hk': '海口',
            'shijiazhuang': '石家庄', 'sjz': '石家庄',
            'taiyuan': '太原',
            'hohhot': '呼和浩特',
            'changchun': '长春'
        }
        return city_map.get(city_code, city_code)
    
    def _extract_number(self, text, pattern, default=None):
        """提取数字"""
        try:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
            return default
        except:
            return default
    
    def _extract_year(self, text):
        """提取年份"""
        patterns = [r'(\d{4})款', r'(\d{4})年', r'(\d{4})-']
        for pattern in patterns:
            year = self._extract_number(text, pattern)
            if year and 2000 <= year <= 2025:
                return int(year)
        return None
    
    def _extract_mileage(self, text):
        """提取里程"""
        # 万公里
        mileage = self._extract_number(text, r'([\d.]+)万公里')
        if mileage is not None:
            return int(mileage * 10000)
        
        # 公里
        mileage = self._extract_number(text, r'([\d.]+)公里')
        if mileage is not None:
            return int(mileage)
        
        return None
    
    def _extract_displacement(self, text):
        """提取排量"""
        displacement = self._extract_number(text, r'([\d.]+)[LT]')
        if displacement and 0.5 <= displacement <= 8.0:
            return displacement
        return None
    
    def _extract_transmission(self, text):
        """提取变速器类型"""
        if '自动' in text or 'AT' in text:
            return '自动'
        if '手动' in text or 'MT' in text:
            return '手动'
        if 'CVT' in text:
            return 'CVT'
        if '双离合' in text or 'DCT' in text:
            return '双离合'
        return '自动'
    
    def _parse_car_title(self, title):
        """解析车辆标题获取品牌和车型"""
        brands = [
            '奥迪', '宝马', '奔驰', '大众', '丰田', '本田', '日产', '马自达', '现代', '起亚', 
            '福特', '雪佛兰', '别克', '凯迪拉克', '沃尔沃', '捷豹', '路虎', '保时捷', '特斯拉',
            '比亚迪', '吉利', '长城', '奇瑞', '长安', '荣威', '名爵', '传祺', '红旗', '领克',
            '蔚来', '小鹏', '理想', '威马', '零跑', '哪吒', '极氪', '岚图', '高合', '智己',
            '雷克萨斯', '英菲尼迪', '讴歌', '林肯', '凯迪拉克', '克莱斯勒', 'Jeep', '道奇',
            '菲亚特', '阿尔法罗密欧', '玛莎拉蒂', '法拉利', '兰博基尼', '宾利', '劳斯莱斯',
            '阿斯顿马丁', '迈凯伦', '布加迪', '帕加尼', '柯尼塞格', '五菱', '宝骏', '东风',
            '一汽', '北汽', '江淮', '海马', '众泰', '力帆', '观致', '启辰', '思铭', '理念'
        ]
        
        for brand in brands:
            if brand in title:
                return brand, title
        
        # 如果没有匹配到品牌，尝试从标题开头提取
        parts = title.split()
        if parts:
            return parts[0], title
        
        return '未知品牌', title
    
    def _parse_price(self, price_text):
        """解析价格文本"""
        try:
            price_match = re.search(r'([\d.]+)', price_text.replace(',', ''))
            if price_match:
                return float(price_match.group(1))
            return None
        except:
            return None
    
    def _infer_fuel_type(self, brand, model):
        """根据品牌和车型推断燃料类型"""
        if brand in ['特斯拉', '蔚来', '小鹏', '理想', '威马', '零跑', '哪吒']:
            return '电动'
        elif 'EV' in model or '电' in model:
            return '电动'
        elif 'PHEV' in model or 'DM' in model or '插电' in model:
            return '插电混动'
        elif 'HEV' in model or '混动' in model:
            return '混动'
        else:
            return '汽油'
    
    def _infer_car_type(self, model):
        """根据车型推断车辆类型"""
        suv_keywords = ['SUV', 'X', 'Q', 'GL', 'GLE', 'RX', 'NX', 'CX', 'CR', 'RAV', 'XC', 'QX']
        mpv_keywords = ['MPV', 'GL8', 'ODYSSEY', 'SIENNA', 'ALPHARD', 'ELYSION']
        
        model_upper = model.upper()
        
        if any(keyword in model_upper for keyword in suv_keywords):
            return 'SUV'
        elif any(keyword in model_upper for keyword in mpv_keywords):
            return 'MPV'
        else:
            return '轿车'
    
    def _extract_color(self, text):
        """提取车辆颜色"""
        colors = ['白色', '黑色', '银色', '灰色', '红色', '蓝色', '金色', '棕色', '绿色', '黄色', '橙色', '紫色']
        for color in colors:
            if color in text:
                return color
        return None
    
    def _extract_condition_score(self, text):
        """提取车况评分"""
        score_match = re.search(r'车况[：:]?([\d.]+)分', text)
        if score_match:
            return float(score_match.group(1))
        
        # 尝试其他模式
        score_match = re.search(r'评分[：:]?([\d.]+)', text)
        if score_match:
            return float(score_match.group(1))
        
        # 不生成模拟数据，返回None
        return None
    
    def _extract_fuel_consumption(self, text):
        """提取油耗"""
        consumption_match = re.search(r'油耗[：:]?([\d.]+)L', text)
        if consumption_match:
            return float(consumption_match.group(1))
        
        consumption_match = re.search(r'([\d.]+)L/100km', text)
        if consumption_match:
            return float(consumption_match.group(1))
        
        return None
    
    def _extract_max_speed(self, text):
        """提取最高时速"""
        speed_match = re.search(r'最高时速[：:]?([\d.]+)', text)
        if speed_match:
            return float(speed_match.group(1))
        
        speed_match = re.search(r'([\d.]+)km/h', text)
        if speed_match:
            return float(speed_match.group(1))
        
        # 不生成模拟数据，返回None
        return None
    
    def _extract_acceleration(self, text):
        """提取加速时间"""
        acc_match = re.search(r'加速[：:]?([\d.]+)秒', text)
        if acc_match:
            return float(acc_match.group(1))
        
        acc_match = re.search(r'0-100km/h[：:]?([\d.]+)s', text)
        if acc_match:
            return float(acc_match.group(1))
        
        # 不生成模拟数据，返回None
        return None
    
    def _get_price_range(self, price):
        """获取价格区间"""
        if price < 10:
            return '10万以下'
        elif price < 20:
            return '10-20万'
        elif price < 30:
            return '20-30万'
        elif price < 50:
            return '30-50万'
        elif price < 100:
            return '50-100万'
        else:
            return '100万以上'
    
    def _get_mileage_range(self, mileage):
        """获取里程区间"""
        if mileage < 10000:
            return '1万公里以下'
        elif mileage < 30000:
            return '1-3万公里'
        elif mileage < 50000:
            return '3-5万公里'
        elif mileage < 100000:
            return '5-10万公里'
        else:
            return '10万公里以上'
    
    def scrape_che168_enhanced(self, cities=None, max_pages_per_city=50, target_count=20000):
        """增强版车168爬虫 - 多城市全覆盖"""
        logger.info("开始增强版车168数据爬取...")
        
        if cities is None:
            # 扩展城市列表，确保有足够数据源达到20000+目标
            cities = [
                # 一线城市
                "bj", "sh", "gz", "sz",
                # 新一线城市  
                "hz", "nj", "wh", "cd", "xa", "cq", "tj", "qd", "dl", "su",
                # 二线城市
                "dg", "fs", "zz", "cs", "jn", "hf", "sy", "cc", "hrb", "nb", "wx", "tz",
                # 补充城市（确保足够数据源）
                "km", "lz", "urumqi", "gy", "nn", "hk", "sjz", "taiyuan", "hohhot", "changchun"
            ]
        
        total_scraped = 0
        
        with tqdm(total=target_count, desc="爬取进度") as pbar:
            # 动态调整每个城市的目标数量
            per_city_min = 200  # 每个城市最少爬取200条
            per_city_max = 1500  # 每个城市最多爬取1500条
            per_city_target = max(per_city_min, min(per_city_max, target_count // len(cities)))
            
            # 如果目标数量很大，适当增加每个城市的目标
            if target_count > 15000:
                per_city_target = max(per_city_target, target_count // (len(cities) - 5))  # 预留5个城市的缓冲
            
            logger.info(f"📋 分配策略: 每城市目标 {per_city_target} 条 (最少{per_city_min}, 最多{per_city_max})")
            
            for city_idx, city in enumerate(cities):
                if total_scraped >= target_count:
                    break
                
                # 动态调整剩余城市的目标
                remaining_cities = len(cities) - city_idx
                remaining_target = target_count - total_scraped
                adjusted_target = min(per_city_max, max(per_city_min, remaining_target // max(1, remaining_cities - 1)))
                
                logger.info(f"🏙️ 开始爬取城市 ({city_idx+1}/{len(cities)}): {self._city_name_map(city)} (目标: {adjusted_target}条, 剩余: {remaining_target})")
                city_scraped = 0
                
                # 多个分类页面，确保覆盖更全面
                categories = ['', 'suv/', 'mpv/', 'pickup/', 'coupe/']
                
                for category in categories:
                    # 修改条件：确保每个城市都能爬到数据
                    if total_scraped >= target_count:
                        break
                    if city_scraped >= adjusted_target and city_scraped >= per_city_min:
                        break
                        
                    for page in range(1, max_pages_per_city + 1):
                        if total_scraped >= target_count:
                            break
                        if city_scraped >= adjusted_target and city_scraped >= per_city_min:
                            break
                            
                        try:
                            url = f"https://www.che168.com/{city}/list/{category}?page={page}"
                            
                            if url in self.scraped_urls:
                                continue
                                
                            response = self.safe_request(url)
                            if not response:
                                continue
                            
                            soup = BeautifulSoup(response.text, 'lxml')
                            
                            # 多种选择器尝试
                            selectors = [
                                "li.cards-li",
                                ".list-item",
                                ".car-item",
                                ".item-info"
                            ]
                            
                            cards = []
                            for selector in selectors:
                                cards = soup.select(selector)
                                if cards:
                                    break
                            
                            if not cards:
                                logger.debug(f"页面无数据: {url}")
                                break
                            
                            new_records = 0
                            for card in cards:
                                if total_scraped >= target_count:
                                    break
                                    
                                car_data = self._parse_che168_card_enhanced(card, city)
                                if car_data and self._is_valid_data(car_data):
                                    self.data.append(car_data)
                                    new_records += 1
                                    total_scraped += 1
                                    city_scraped += 1
                                    pbar.update(1)
                            
                            self.scraped_urls.add(url)
                            
                            if new_records > 0:
                                logger.info(f"✅ {self._city_name_map(city)} {category} 第{page}页: +{new_records}条")
                            
                            # 定期保存检查点
                            if len(self.data) % 1000 == 0:
                                self.save_checkpoint()
                            
                            # 如果连续几页没数据，跳出分类
                            if new_records == 0:
                                break
                                
                            time.sleep(self.get_random_delay(*self.page_delay))
                            
                        except Exception as e:
                            logger.error(f"爬取页面出错 {url}: {str(e)}")
                            continue
                
                logger.info(f"🏁 {self._city_name_map(city)} 完成，获得 {city_scraped} 条数据")
                
                # 如果这个城市没有获取到足够数据，记录警告
                if city_scraped < per_city_min:
                    logger.warning(f"⚠️ {self._city_name_map(city)} 数据量不足: {city_scraped} < {per_city_min}")
                elif city_scraped >= adjusted_target:
                    logger.info(f"✅ {self._city_name_map(city)} 达到目标: {city_scraped} >= {adjusted_target}")
                
                # 城市间休息
                if city_scraped > 0:
                    time.sleep(self.get_random_delay(2, 5))
                else:
                    time.sleep(self.get_random_delay(1, 2))  # 没数据的城市休息时间短一些
        
        logger.info(f"🎉 车168爬取完成，总共获得 {total_scraped} 条数据")
        return total_scraped
    
    def _parse_che168_card_enhanced(self, card, city_code):
        """增强版车168卡片解析"""
        try:
            # 多种方式提取标题
            title = ''
            title_selectors = ['[carname]', 'h4', '.card-name', '.car-name', '.title']
            for selector in title_selectors:
                elem = card.select_one(selector)
                if elem:
                    title = elem.get('carname') or elem.get_text(strip=True)
                    if title:
                        break
            
            if not title:
                return None
            
            full_text = card.get_text(strip=True)
            
            # 提取价格
            price = None
            price_patterns = [
                r'([\d.]+)万',
                r'¥([\d.]+)万',
                r'售价[：:]?([\d.]+)万'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, full_text)
                if match:
                    price = float(match.group(1))
                    break
            
            if not price or price <= 0:
                return None
            
            # 解析基本信息
            brand, model = self._parse_car_title(title)
            year = self._extract_year(full_text)
            mileage = self._extract_mileage(full_text)
            displacement = self._extract_displacement(full_text)
            transmission = self._extract_transmission(full_text)
            
            # 基本验证
            if not year or not mileage:
                return None
            
            # 提取更多字段
            color = self._extract_color(full_text)
            condition_score = self._extract_condition_score(full_text)
            fuel_consumption = self._extract_fuel_consumption(full_text)
            max_speed = self._extract_max_speed(full_text)
            acceleration = self._extract_acceleration(full_text)
            
            # 构建数据字典，只包含有值的字段
            data = {
                '品牌': brand,
                '车型': model,
                '价格': price,
                '年份': year,
                '里程': mileage,
                '燃料类型': self._infer_fuel_type(brand, model),
                '变速器': transmission or '自动',
                '车辆类型': self._infer_car_type(model),
                '数据来源': '车168',
                '所在城市': self._city_name_map(city_code),
            }
            
            # 只添加有值的可选字段
            if displacement is not None:
                data['排量'] = displacement
            if color:
                data['颜色'] = color
            if condition_score is not None:
                data['车况评分'] = condition_score
            if fuel_consumption is not None:
                data['油耗'] = fuel_consumption
            if max_speed is not None:
                data['最高时速'] = max_speed
            if acceleration is not None:
                data['加速时间'] = acceleration
            if year:
                data['车龄'] = 2024 - year
            
            data['价格区间'] = self._get_price_range(price)
            data['里程区间'] = self._get_mileage_range(mileage)
            
            return data
            
        except Exception as e:
            logger.debug(f"解析车168卡片失败: {e}")
            return None
    
    
    
    
    
    def _is_valid_data(self, data):
        """验证数据有效性"""
        required_fields = ['品牌', '车型', '价格', '年份', '里程']
        
        for field in required_fields:
            if not data.get(field):
                return False
        
        # 价格范围检查
        if not (0.1 <= data['价格'] <= 2000):
            return False
        
        # 年份范围检查
        if not (2000 <= data['年份'] <= 2025):
            return False
        
        # 里程范围检查
        if not (0 <= data['里程'] <= 1000000):
            return False
        
        return True
    
    def scrape_all_sources(self, target_count=20000):
        """爬取车168数据源"""
        logger.info(f"开始爬取车168数据，目标: {target_count} 条数据")
        
        # 加载检查点
        self.load_checkpoint()
        
        current_count = len(self.data)
        remaining = target_count - current_count
        
        if remaining <= 0:
            logger.info(f"已达到目标数据量: {current_count} 条")
            return
        
        logger.info(f"当前数据: {current_count} 条，还需: {remaining} 条")
        
        try:
            logger.info(f"爬取计划: 车168({remaining}条)")
            
            # 只爬取车168数据
            scraped = self.scrape_che168_enhanced(target_count=remaining)
            logger.info(f"车168完成: {scraped} 条")
            self.save_checkpoint()
            
        except KeyboardInterrupt:
            logger.info("用户中断爬取...")
            self.save_checkpoint()
            raise
        except Exception as e:
            logger.error(f"爬取过程出错: {e}")
            self.save_checkpoint()
            raise
    
    def preprocess_data(self):
        """数据预处理"""
        logger.info("开始数据预处理...")
        
        if not self.data:
            logger.warning("没有数据需要处理")
            return
        
        df = pd.DataFrame(self.data)
        initial_count = len(df)
        
        # 1. 去重
        df = df.drop_duplicates(subset=['品牌', '车型', '年份', '里程', '价格'], keep='first')
        dedup_count = initial_count - len(df)
        logger.info(f"去重移除: {dedup_count} 条")
        
        # 2. 数据类型转换
        numeric_columns = ['价格', '年份', '里程', '排量']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 3. 移除异常值
        df = df.dropna(subset=['品牌', '车型', '价格', '年份', '里程'])
        df = df[(df['价格'] >= 0.1) & (df['价格'] <= 2000)]
        df = df[(df['年份'] >= 2000) & (df['年份'] <= 2025)]
        df = df[(df['里程'] >= 0) & (df['里程'] <= 1000000)]
        
        # 4. 填充缺失值
        if '排量' in df.columns:
            df['排量'].fillna(0.0, inplace=True)
        
        # 5. 数据标准化
        df['价格'] = df['价格'].round(1)
        df['排量'] = df['排量'].round(1)
        
        self.data = df.to_dict('records')
        final_count = len(self.data)
        
        logger.info(f"数据预处理完成: {initial_count} → {final_count} 条")
        
        # 打印统计信息
        self.print_statistics()
    
    def print_statistics(self):
        """打印数据统计信息"""
        if not self.data:
            return
        
        df = pd.DataFrame(self.data)
        
        logger.info("=== 数据统计信息 ===")
        logger.info(f"总数据量: {len(df)} 条")
        
        # 数据源分布（应该全部来自车168）
        if '数据来源' in df.columns:
            source_counts = df['数据来源'].value_counts()
            logger.info("数据源分布:")
            for source, count in source_counts.items():
                logger.info(f"  {source}: {count} 条")
        
        # 品牌分布
        brand_counts = df['品牌'].value_counts().head(10)
        logger.info("热门品牌 (Top 10):")
        for brand, count in brand_counts.items():
            logger.info(f"  {brand}: {count} 条")
        
        # 价格统计
        logger.info(f"价格范围: {df['价格'].min():.1f} - {df['价格'].max():.1f} 万元")
        logger.info(f"平均价格: {df['价格'].mean():.1f} 万元")
        
        # 年份分布
        logger.info(f"年份范围: {df['年份'].min()} - {df['年份'].max()}")
        
        # 城市分布
        if '所在城市' in df.columns:
            city_counts = df['所在城市'].value_counts().head(10)
            logger.info("城市分布 (Top 10):")
            for city, count in city_counts.items():
                logger.info(f"  {city}: {count} 条")
    
    def save_data(self, filename=None):
        """保存数据到CSV"""
        if not self.data:
            logger.warning("没有数据需要保存")
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"car_data_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(self.data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            file_size = os.path.getsize(filename) / 1024 / 1024
            logger.info(f"数据已保存: {filename}")
            logger.info(f"文件大小: {file_size:.2f} MB")
            logger.info(f"数据条数: {len(df)} 条")
            
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False

def main():
    """主函数"""
    scraper = CarDataScraper()
    
    print("🚗 汽车数据爬虫系统 - 车168专版")
    print("目标: 从车168爬取20000+条真实汽车数据")
    print("=" * 60)
    
    try:
        target_count = 20000
        print(f"开始爬取 {target_count} 条汽车数据...")
        
        start_time = time.time()
        
        # 开始爬取
        scraper.scrape_all_sources(target_count=target_count)
        
        # 数据预处理 - 暂时隐藏
        # scraper.preprocess_data()
        
        # 保存数据
        success = scraper.save_data()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 爬取完成!")
        print(f"⏰ 总耗时: {elapsed_time/60:.1f} 分钟")
        print(f"📊 最终数据量: {len(scraper.data)} 条")
        
        if success:
            print("✅ 数据爬取和保存成功!")
        else:
            print("❌ 数据保存失败!")
        
    except KeyboardInterrupt:
        print("\n用户中断爬取...")
        if scraper.data:
            print(f"已爬取 {len(scraper.data)} 条数据")
            save_choice = input("是否保存已爬取的数据? (y/n): ").lower()
            if save_choice == 'y':
                scraper.save_data()
    
    except Exception as e:
        logger.error(f"爬取过程出现错误: {str(e)}")
        if scraper.data:
            logger.info(f"尝试保存已爬取的 {len(scraper.data)} 条数据...")
            scraper.save_data()
    
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()