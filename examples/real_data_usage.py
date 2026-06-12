# examples/real_data_usage.py - 真实数据接入示例
"""
演示如何使用 Swiss Ephemeris 接入真实数据并计算评分
"""

import sys
import os
from datetime import datetime, timezone

# 设置标准输出编码为 UTF-8
# sys.stdout.reconfigure(encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from life_kline.ephemeris import EphemerisEngine
    from life_kline.constants import Planet
    from life_kline.scoring import compute_node_score, print_score_report
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保已安装 pyswisseph: pip install pyswisseph")
    sys.exit(1)

def decimal_to_dms(deg_float):
    """将小数值转换为度分秒格式 (D°M′S″)"""
    d = int(deg_float)
    m_float = (deg_float - d) * 60
    m = int(m_float)
    s_float = (m_float - m) * 60
    s = round(s_float)
    
    # 处理进位
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
        
    return f"{d}°{m:02d}′{s:02d}″"

def main():
    print("初始化 Swiss Ephemeris 引擎...")
    try:
        engine = EphemerisEngine()
    except ImportError as e:
        print(f"初始化失败: {e}")
        return

    # 目标出生信息：
    # 阳历 1991年3月21日 9点25分
    # 地点：山西省晋城市陵川县附城镇青杨庄村 (东经113°17′ 北纬35°47′)
    # 时区：GMT+08:00 (非夏令时)
    
    # 1. 经纬度转换
    # 113°17′ E = 113 + 17/60 = 113.283333
    # 35°47′ N = 35 + 47/60 = 35.783333
    lon = 113.283333
    lat = 35.783333
    
    # 2. 时间转换 (Local -> UTC)
    # 北京时间 09:25:00 (GMT+8)
    # UTC = 09:25 - 8 = 01:25
    birth_time = datetime(1991, 3, 21, 1, 25, 0)
    
    print(f"计算星盘数据: {birth_time} UTC (对应北京时间 1991-03-21 09:25:00)")
    print(f"地点: Lat {lat:.4f}, Lon {lon:.4f}")

    # 定义要对比的宫位制
    house_systems = {
        # 'P': 'Placidus (普拉西度 - 现代常用)',
        'W': 'Whole Sign (整宫制 - 古典常用)',
    }

    for h_sys_code, h_sys_name in house_systems.items():
        print(f"\n{'='*20} 使用宫位制: {h_sys_name} {'='*20}")
        try:
            # 计算星盘
            chart = engine.calculate_chart(birth_time, lat, lon, house_system=h_sys_code)
            
            print("\n--- 行星位置 (黄经 & 宫位) ---")
            for planet, info in chart.planets.items():
                # 显示格式：Planet: Sign Degree (Total Longitude) -> House
                dms_deg = decimal_to_dms(info.degree)
                dms_lon = decimal_to_dms(info.longitude)
                print(f"{planet.name:<10}: {info.sign.name:<12} {dms_deg:<10} (Abs: {dms_lon:<10}) -> House {info.house}")
                
            print("\n--- 宫位头 (Cusps) ---")
            # House 1 is Ascendant
            asc_info = chart.houses[0]
            print(f"ASC (House 1): {asc_info[0].name} {decimal_to_dms(asc_info[1])}")
            
            for i, (sign, deg) in enumerate(chart.houses):
                if i == 0: continue 
                print(f"House {i+1:<7}: {sign.name:<12} {decimal_to_dms(deg)}")
                
            print(f"\n--- 评分计算示例 (太阳 - {h_sys_name}) ---")
            # 计算太阳的人生层级评分
            result = compute_node_score('life', Planet.SUN, chart)
            
            # 打印报告
            print_score_report({Planet.SUN: result})
            
        except Exception as e:
            print(f"计算过程中出错 ({h_sys_name}): {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
