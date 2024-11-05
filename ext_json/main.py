import json

def extract_fields(input_file, output_file):
    # 要提取的欄位名稱
    desired_fields = [
        "id", "catname", "title", "lev_bas_i", "lev_adv_i",
        "lev_exp_i", "lev_mas_i", "lev_ult_i", "version", 
        "date_added", "intl"
    ]

    # 讀取輸入的 JSON 檔案
    with open(input_file, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    # 提取所需欄位
    filtered_data = []
    for item in data:
        filtered_item = {field: item.get(field, "") for field in desired_fields}
        filtered_data.append(filtered_item)

    # 將提取的資料寫入輸出的 JSON 檔案
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(filtered_data, outfile, ensure_ascii=False, indent=4)

# 使用範例
input_file = r'D:\VSCode\python\ChunithmOpSimulator\ext_json\input.json'
output_file = r'D:\VSCode\python\ChunithmOpSimulator\ext_json\output.json'
extract_fields(input_file, output_file)
