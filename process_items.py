import json
import os
from collections import defaultdict

def load_json_file(filepath):
    """加载JSON文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件未找到: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON解析错误 {filepath}: {e}")
        return []

def process_and_classify_items():
    """处理并分类物品数据"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 加载中英文数据文件
    en_file = os.path.join(script_dir, "items_en_full.json")
    zh_file = os.path.join(script_dir, "items_zh-hans_full.json")
    
    items_en = load_json_file(en_file)
    items_zh = load_json_file(zh_file)
    
    if not items_en:
        print("英文数据文件为空或无法加载")
        return
    
    # 创建ID到物品的映射
    en_dict = {item['id']: item for item in items_en}
    zh_dict = {item['id']: item for item in items_zh} if items_zh else {}
    
    # 按类别分组
    categorized_items = defaultdict(list)
    
    # 处理每个英文物品
    for item_id, en_item in en_dict.items():
        # 创建统合后的物品结构
        combined_item = {
            "id": item_id,
            "slug": en_item.get("slug", ""),
            "gameRef": en_item.get("gameRef", ""),
            "tags": en_item.get("tags", []),
            "ducats": en_item.get("ducats"),
            "bulkTradable": en_item.get("bulkTradable"),
            "maxRank": en_item.get("maxRank"),
            "subtypes": en_item.get("subtypes"),
            "names": {
                "en": en_item.get("i18n", {}).get("en", {}).get("name", ""),
                "zh-hans": ""
            },
            "icons": {
                "en": en_item.get("i18n", {}).get("en", {}).get("icon", ""),
                "zh-hans": ""
            },
            "thumbs": {
                "en": en_item.get("i18n", {}).get("en", {}).get("thumb", ""),
                "zh-hans": ""
            }
        }
        
        # 如果存在对应的中文数据，填充中文信息
        if item_id in zh_dict:
            zh_item = zh_dict[item_id]
            combined_item["names"]["zh-hans"] = zh_item.get("i18n", {}).get("zh-hans", {}).get("name", "")
            combined_item["icons"]["zh-hans"] = zh_item.get("i18n", {}).get("zh-hans", {}).get("icon", "")
            combined_item["thumbs"]["zh-hans"] = zh_item.get("i18n", {}).get("zh-hans", {}).get("thumb", "")
        
        # 根据tags进行分类，如果没有tags则归为"other"
        tags = en_item.get("tags", [])
        if tags:
            # 使用第一个tag作为主要分类
            category = tags[0]
        else:
            category = "other"
        
        categorized_items[category].append(combined_item)
    
    # 创建输出目录
    output_dir = os.path.join(script_dir, "categorized_items")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存每个类别的文件
    files_created = 0
    for category, items in categorized_items.items():
        # 清理文件名中的非法字符
        safe_category = "".join(c for c in category if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_category:
            safe_category = "other"
            
        filename = f"{safe_category}.json"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            files_created += 1
            print(f"已保存分类文件: {filename} ({len(items)} 个物品)")
        except Exception as e:
            print(f"保存文件 {filepath} 失败: {e}")
    
    print(f"\n总共生成了 {files_created} 个分类文件。")
    print(f"分类文件保存在: {output_dir}")

if __name__ == "__main__":
    process_and_classify_items()