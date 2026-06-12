
"""
server_usage_demo.py - 模拟后端 API 调用

这个脚本演示了如何在 Web 框架（如 Flask/FastAPI）中使用 LifeKlineService。
模拟接收前端 JSON 请求，并返回处理后的 JSON 响应。
"""

import sys
import os
import json

# 将项目根目录添加到 python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from life_kline.service import LifeKlineService

def simulate_api_request(request_data):
    """
    模拟 API 处理函数
    """
    print(f"收到请求: {json.dumps(request_data, ensure_ascii=False)}")
    
    # 1. 初始化服务 (通常在应用启动时做一次)
    service = LifeKlineService()
    
    # 2. 从请求中提取参数
    try:
        birth_time = request_data.get('birth_time')
        lat = request_data.get('lat')
        lon = request_data.get('lon')
        tz = request_data.get('timezone', 8.0)
        
        # 3. 调用业务逻辑
        response_data = service.generate_report(
            birth_time_iso=birth_time,
            lat=lat,
            lon=lon,
            timezone_offset=tz
        )
        
        return {
            "status": "success",
            "data": response_data
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def main():
    # 模拟前端发送的 JSON 数据
    # 阳历 1991年3月21日 9点25分, 山西晋城
    mock_frontend_payload = {
        "birth_time": "1991-03-21T09:25:00",
        "lat": 35.783333,
        "lon": 113.283333,
        "timezone": 8.0
    }
    
    print("=== 模拟后端 API 处理流程 ===")
    
    # 调用模拟 API
    result = simulate_api_request(mock_frontend_payload)
    
    # 输出结果
    print("\n=== 返回给前端的 JSON 数据 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 验证关键数据
    if result['status'] == 'success':
        periods = result['data']['kline_data']['periods']
        print(f"\n验证成功: 生成了 {len(periods)} 个周期数据")
        
        # 检查是否包含牛市/熊市
        bull_periods = [p for p in periods if p['trend']['type'] == 'bull']
        print(f"检测到 {len(bull_periods)} 个牛市周期")
        if bull_periods:
            print(f"示例牛市: {bull_periods[0]['lords']['major']} 大运 ({bull_periods[0]['timing']['start_date']})")

if __name__ == "__main__":
    main()
