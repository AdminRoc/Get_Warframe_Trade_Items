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
        # 仅在调试时打印详细成功信息，避免刷屏
        # print(f"成功获取 {endpoint} ({language}) 数据，状态码: {response.status_code}")
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
    # 我们主要依赖单次请求中的 i18n 字段，但保留 languages 列表用于文件生成循环
    languages = ["en", "zh-hans"]
    
    all_results = {}
    
    # 1. 获取基础数据
    # 注意：Warframe Market V2 API 的 /items 端点返回的每个物品对象中通常包含完整的 i18n 信息
    # 因此我们只需要请求一次（例如默认语言或英文），然后从中解析所有语言即可。
    # 为了保险起见，我们请求英文数据，因为它是基础语言。
    
    for endpoint in endpoints:
        print(f"\n处理端点: {endpoint}")
        
        # 只请求英文数据作为主数据源，因为它包含 i18n 字典
        print(f"获取 {endpoint} (en) 数据以提取多语言信息...")
        data_en = fetch_api_data(endpoint, "en")
        
        if data_en:
            all_results[endpoint] = {"en": data_en}
            print(f"成功获取 {endpoint} 基础数据")
        else:
            print(f"未能获取 {endpoint} 基础数据，程序退出")
            return

    # 指定输出目录为当前脚本所在文件夹
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. 处理数据并按类型分类导出
    for endpoint in endpoints:
        if endpoint not in all_results:
            continue
            
        main_data = all_results[endpoint].get("en")
        if not main_data:
            continue

        items_list = main_data.get("data", [])
        if not items_list:
            print("物品列表为空")
            continue
        
        # 用于存储分类结果: { type_name: { "en": [names], "zh-hans": [names] } }
        categorized_items = defaultdict(lambda: {"en": [], "zh-hans": []})
        
        print("正在分析物品类型并分类...")
        
        processed_count = 0
        missing_zh_count = 0
        
        for item in items_list:
            # 获取类型
            item_type = item.get("type") or item.get("category") or "Unknown"
            safe_type = clean_filename(item_type)
            
            # 获取 i18n 数据
            i18n = item.get("i18n", {})
            
            # 提取英文名称
            en_info = i18n.get("en", {})
            en_name = en_info.get("name") if isinstance(en_info, dict) else None
            
            # 提取中文名称
            zh_info = i18n.get("zh-hans", {})
            zh_name = zh_info.get("name") if isinstance(zh_info, dict) else None
            
            # 如果没有直接的 zh-hans，有时可能是 zh_cn 或其他，但 Warframe Market 通常是 zh-hans
            # 如果 zh_name 仍然为空，可以留空，稍后文件生成时跳过或仅生成英文
            
            if en_name:
                categorized_items[safe_type]["en"].append(en_name)
            
            if zh_name:
                categorized_items[safe_type]["zh-hans"].append(zh_name)
            else:
                # 统计缺失中文的情况，可选
                missing_zh_count += 1
                
            processed_count += 1

        print(f"处理完成。共处理 {processed_count} 个物品。")
        print(f"其中 {missing_zh_count} 个物品可能缺少中文名称。")
        print(f"发现 {len(categorized_items)} 种物品类型。")
        
        # 3. 生成文件
        print("\n开始生成文件...")
        
        files_created = 0
        for item_type, lang_data in categorized_items.items():
            for lang in languages:
                names = lang_data[lang]
                
                # 如果该语言下没有名称，则跳过生成该语言的文件
                if not names:
                    continue
                
                # 生成文件名: {Type}_{Lang}.txt
                filename = f"{item_type}_{lang}.txt"
                filepath = os.path.join(output_dir, filename)
                
                # 保存名称到文本文件，每行一个
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        for name in names:
                            f.write(name + "\n")
                    files_created += 1
                    # 仅打印部分示例，避免输出过多
                    if files_created <= 5 or lang == 'zh-hans':
                         print(f"已保存 [{lang}] {item_type}: {len(names)} 个物品 -> {filename}")
                except Exception as e:
                    print(f"保存文件 {filepath} 失败: {e}")

        print(f"\n总共生成了 {files_created} 个文件。")
        print("请检查脚本所在目录下的 .txt 文件。")

    return all_results

if __name__ == "__main__":
    results = main()