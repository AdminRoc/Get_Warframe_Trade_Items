import requests
import json
from datetime import datetime
import os
from collections import defaultdict

def fetch_api_data(endpoint, language):
    """获取指定API端点的数据"""
    base_url = "https://api.warframe.market/v2/"
    url = f"{base_url}{endpoint.lstrip('/')}"
    headers = {
        "Language": language,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误 {response.status_code} for {url}: {e}")
        if hasattr(response, 'text'):
            print(f"响应内容: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 失败: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析失败 {url}: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"响应内容: {response.text[:200]}")
    return None

def clean_filename(name):
    """清理文件名中的非法字符"""
    if not name:
        return "Unknown_Type"
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def main():
    endpoints = ["items"]
    # 定义需要获取的语言
    languages = ["en", "zh-hans"]
    
    all_results = {}
    
    # 1. 获取基础数据
    # 修改：分别请求英文和中文数据，以确保获取完整的中文名称
    for endpoint in endpoints:
        print(f"\n处理端点: {endpoint}")
        
        endpoint_data = {}
        for lang in languages:
            print(f"获取 {endpoint} ({lang}) 数据...")
            data = fetch_api_data(endpoint, lang)
            if data:
                endpoint_data[lang] = data
                print(f"成功获取 {endpoint} ({lang}) 数据")
            else:
                print(f"警告: 未能获取 {endpoint} ({lang}) 数据")
        
        if endpoint_data:
            all_results[endpoint] = endpoint_data
        else:
            print(f"未能获取 {endpoint} 的任何数据，程序退出")
            return

    # 指定输出目录为当前脚本所在文件夹
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. 处理数据并导出完整字段
    for endpoint in endpoints:
        if endpoint not in all_results:
            continue
            
        data_en = all_results[endpoint].get("en")
        data_zh = all_results[endpoint].get("zh-hans")
        
        if not data_en:
            continue

        items_list_en = data_en.get("data", [])
        items_list_zh = data_zh.get("data", []) if data_zh else []
        
        if not items_list_en:
            print("物品列表为空")
            continue
        
        print(f"正在准备导出 {len(items_list_en)} 个英文物品和 {len(items_list_zh)} 个中文物品...")
        
        # 3. 生成 JSON 文件，保留所有字段以便后续处理
        print("\n开始生成 JSON 数据文件...")
        
        files_created = 0
        
        # 导出英文完整数据
        if items_list_en:
            filename_en = f"{endpoint}_en_full.json"
            filepath_en = os.path.join(output_dir, filename_en)
            try:
                with open(filepath_en, "w", encoding="utf-8") as f:
                    # indent=2 使 JSON 可读性更好
                    json.dump(items_list_en, f, ensure_ascii=False, indent=2)
                files_created += 1
                print(f"已保存英文完整数据: {filename_en} ({len(items_list_en)} 个物品)")
            except Exception as e:
                print(f"保存文件 {filepath_en} 失败: {e}")

        # 导出中文完整数据
        if items_list_zh:
            filename_zh = f"{endpoint}_zh-hans_full.json"
            filepath_zh = os.path.join(output_dir, filename_zh)
            try:
                with open(filepath_zh, "w", encoding="utf-8") as f:
                    json.dump(items_list_zh, f, ensure_ascii=False, indent=2)
                files_created += 1
                print(f"已保存中文完整数据: {filename_zh} ({len(items_list_zh)} 个物品)")
            except Exception as e:
                print(f"保存文件 {filepath_zh} 失败: {e}")

        print(f"\n总共生成了 {files_created} 个 JSON 文件。")
        print("请检查脚本所在目录下的 .json 文件。")
        print("提示: 这些文件包含了物品的所有字段（如 url_name, id, i18n 等），可用于后续通过 url_name 匹配中英文并进行自定义分类。")

    return all_results

if __name__ == "__main__":
    results = main()