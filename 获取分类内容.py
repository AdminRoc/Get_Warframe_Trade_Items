import requests
import json
from datetime import datetime
import os
from collections import defaultdict  # 新增导入，用于方便地按类型分组

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
        print(f"成功获取 {endpoint} ({language}) 数据，状态码: {response.status_code}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误 {response.status_code} for {url}: {e}")
        print(f"响应内容: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 失败: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析失败 {url}: {e}")
        print(f"响应内容: {response.text[:200]}")
    return None

def clean_filename(name):
    """清理文件名中的非法字符"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name.strip()

def main():
    # 只关注 /items 端点，因为 lich/weapons 和 sister/weapons 通常也包含在 items 中或者有特定的 type
    # 根据 V2 API，/items 包含所有可交易物品。
    endpoints = ["items"]
    languages = ["en", "zh-hans"]
    
    all_results = {}
    
    # 1. 获取所有端点和语言的基础数据
    for endpoint in endpoints:
        print(f"\n处理端点: {endpoint}")
        all_results[endpoint] = {}
        
        for lang in languages:
            print(f"获取 {endpoint} ({lang}) 数据...")
            data = fetch_api_data(endpoint, lang)
            
            if data:
                all_results[endpoint][lang] = data
                print(f"成功获取 {endpoint} ({lang}) 数据")
            else:
                print(f"未能获取 {endpoint} ({lang}) 数据")
    
    # 指定输出目录为当前脚本所在文件夹
    output_dir = os.path.dirname(os.path.abspath(__file__))
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 2. 处理数据并按类型分类导出
    for endpoint in endpoints:
        if endpoint not in all_results:
            continue
            
        # 我们只需要处理一次数据结构，因为类型通常在英文数据中更准确，或者两种语言结构一致
        # 这里我们以英文数据的结构来识别类型，然后分别提取两种语言的名称
        
        # 获取英文数据以确定类型分布 (假设英文数据存在)
        en_data = all_results[endpoint].get("en")
        if not en_data:
            print("未获取到英文基础数据，无法进行分类")
            return

        items_list = en_data.get("data", [])
        
        # 用于存储分类结果: { type_name: { "en": [names], "zh-hans": [names] } }
        categorized_items = defaultdict(lambda: {"en": [], "zh-hans": []})
        
        print("正在分析物品类型并分类...")
        
        # 遍历所有物品以建立类型映射
        # 注意：API返回的 items 列表中，每个 item 都有 i18n 和 type/category 信息
        # V2 API 中，物品类型通常在 item['type'] 或 item['category'] 中，具体取决于物品
        # 根据常见 V2 结构，通常有一个 'type' 字段表示大类 (如 Warframe, Primary, etc.)
        
        for item in items_list:
            # 获取物品的唯一标识或内部名，以便在其他语言数据中匹配（如果必要）
            # 但在 V2 中，通常每个语言请求返回的是独立的翻译列表，顺序可能一致也可能不一致
            # 更稳妥的方式：V2 API /items 返回的数据中，每个对象包含 i18n。
            # 让我们重新检查 fetch 的数据结构。
            # 如果 fetch 返回的是完整的带 i18n 的对象，我们可以直接从单个对象中提取所有语言。
            
            # 修正策略：
            # 之前的代码是分别请求 en 和 zh-hans。
            # V2 API 的 /items 端点返回的数据结构中，每个 item 对象包含 `i18n` 字典。
            # 因此，我们只需要请求一次（比如英文），然后从每个 item 的 i18n 中提取 en 和 zh-hans 即可！
            # 这样能保证类型和名称的绝对对应，避免分别请求导致的顺序或过滤差异。
            
            pass # 下面的逻辑将重写以利用 i18n 结构

        # --- 重写核心逻辑：利用单次请求中的 i18n 数据 ---
        print("使用英文请求数据进行分类提取（包含多语言信息）...")
        
        # 清空之前的分类容器
        categorized_items = defaultdict(lambda: {"en": [], "zh-hans": []})
        
        # 新增：用于收集所有唯一的物品类型
        all_types = set()
        
        # 使用英文请求的结果作为主数据源，因为它包含 i18n
        main_lang_data = all_results[endpoint].get("en")
        if not main_lang_data:
             main_lang_data = all_results[endpoint].get("zh-hans") #  fallback

        if main_lang_data:
            data_items = main_lang_data.get("data", [])
            for item in data_items:
                i18n = item.get("i18n", {})
                
                # 获取类型。V2 API 中，类型可能在 'type' 字段，或者对于某些物品在 'category'
                # 常见的 type: Warframe, Primary, Secondary, Melee, Zaw, Kitgun, Archwing, Archmelee, Mod, Resource, Arcane, Companion, Weapon, etc.
                item_type = item.get("type") or item.get("category") or "Unknown"
                
                # 新增：收集唯一类型
                all_types.add(item_type)
                
                # 清理类型名称用于文件名
                safe_type = clean_filename(item_type)
                
                # 提取英文名称
                en_info = i18n.get("en", {})
                en_name = en_info.get("name") if en_info else None
                
                # 提取中文名称
                zh_info = i18n.get("zh-hans", {})
                zh_name = zh_info.get("name") if zh_info else None
                
                if en_name:
                    categorized_items[safe_type]["en"].append(en_name)
                if zh_name:
                    categorized_items[safe_type]["zh-hans"].append(zh_name)
                    
        # 新增：打印类型统计信息
        print(f"\n--- 物品类型统计 ---")
        print(f"发现唯一物品类型数量: {len(all_types)}")
        print(f"具体类型列表: {sorted(list(all_types))}")
        print(f"------------------\n")
                    
        # 3. 生成文件
        print(f"\n发现 {len(categorized_items)} 种物品类型，开始生成文件...")
        
        for item_type, lang_data in categorized_items.items():
            for lang in languages:
                names = lang_data[lang]
                if not names:
                    continue
                
                # 生成文件名: {Type}_{Lang}.txt
                filename = f"{item_type}_{lang}.txt"
                filepath = os.path.join(output_dir, filename)
                
                # 保存名称到文本文件，每行一个
                with open(filepath, "w", encoding="utf-8") as f:
                    for name in names:
                        f.write(name + "\n")
                
                print(f"已保存 [{lang}] {item_type}: {len(names)} 个物品 -> {filepath}")

    return all_results

if __name__ == "__main__":
    results = main()