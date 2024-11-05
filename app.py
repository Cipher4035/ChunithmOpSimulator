from flask import Flask, request, render_template, redirect, url_for,jsonify
import json
import math

app = Flask(__name__)

# 全局變數，用於儲存所有上傳的分數數據
scores = []

# 用於範例 purposes: 這裡假設 songdata.json 包含歌曲的難度數據
def load_songdata():
    with open("songdata.json", "r", encoding="utf-8") as f:
        return json.load(f)

song_data = load_songdata()

def calculate_rank_and_op(score, const, isAllJustice, isFullCombo):
    if const is None:
        return 'N/A', 'N/A'  # 如果未找到對應的 const 值

    # 計算 Rating
    if score >= 1009000:
        rating = const + 2.15
    elif score >= 1007500:
        rating = const + 2.0 + (score - 1007500) / 10000
    elif score >= 1005000:
        rating = const + 1.5 + (score - 1005000) / 5000
    elif score >= 1000000:
        rating = const + 1.0 + (score - 1000000) / 10000
    elif score >= 975000:
        rating = const + (score - 975000) / 25000
    elif score >= 925000:
        rating = const - 3.0
    elif score >= 900000:
        rating = const - 5.0
    elif score >= 800000:
        rating = (const - 5.0) / 2
    elif score >= 500000:
        rating = 0
    else:
        rating = 0

    # 無條件捨去到小數點後 0.001
    rating = math.floor(rating * 100) / 100

    # 計算補正1
    if score == 1010000:
        correction1 = 1.25
    elif isAllJustice:
        correction1 = 1.0
    elif isFullCombo:
        correction1 = 0.5
    else:
        correction1 = 0

    # 計算 op
    if score > 1007500:
        correction2 = (score - 1007500) * 0.0015
        op = (const + 2) * 5 + correction1 + correction2
    else:
        op = rating * 5 + correction1

    # 無條件捨去到小數點後 2 位
    op = math.floor(op * 1000) / 1000

    # 判斷 Rank
    if score >= 1009000:
        rank = "SSS+"
    elif score >= 1007500:
        rank = "SSS"
    elif score >= 1005000:
        rank = "SS+"
    elif score >= 1000000:
        rank = "SS"
    elif score >= 975000:
        rank = "S"
    elif score >= 925000:
        rank = "AA"
    elif score >= 900000:
        rank = "A"
    elif score >= 800000:
        rank = "BBB"
    elif score >= 500000:
        rank = "C"
    else:
        rank = "C"

    return rank, op

@app.route("/", methods=["GET", "POST"])
def index():
    global scores  # 引入全局變數以存儲上傳的分數數據
    if request.method == "POST":
        file = request.files["file"]
        if file:
            scores = json.load(file)  # 載入上傳的分數數據
            song_data = load_songdata()  # 加載歌曲數據
            
            # 初始化 scores 為上傳的分數數據
            for record in scores["score"]:
                # 根據 title 查找歌曲信息
                song_info = next((song for song in song_data if song["title"] == record["title"]), None)
                if song_info:
                    # 獲取難度對應的 key
                    difficulty_key = f"lev_{record['difficulty'][:3].lower()}_i"
                    const = song_info.get(difficulty_key, None)

                    record["const"] = const

                    # 計算 maxOps
                    max_const = max(
                        float(song_info.get(level, 0)) for level in 
                        ["lev_bas_i", "lev_adv_i", "lev_exp_i", "lev_mas_i", "lev_ult_i"] if song_info.get(level)
                    )
                    record["maxOps"] = round((max_const + 3) * 5, 2)

                    # 計算 Rank 和 op
                    record["Rank"], record["op"] = calculate_rank_and_op(
                        record["score"], const, record.get("isAllJustice", False), record.get("isFullCombo", False)
                    )
                else:
                    record["const"] = None
                    record["maxOps"] = None
                    record["Rank"] = None
                    record["op"] = None

            return render_template("index.html", scores=scores["score"])

    return render_template("index.html")

@app.route("/table")
def table():
    return render_template("table.html", scores=scores["score"])

# 函數：根據 title 和 difficulty 查找 const 值
def get_const_value(title, difficulty):
    song_info = next((item for item in song_data if item["title"] == title), None)
    if not song_info:
        return None
    
    difficulty_map = {
        "Basic": "lev_bas_i",
        "Advanced": "lev_adv_i",
        "Expert": "lev_exp_i",
        "Master": "lev_mas_i",
        "Ultima": "lev_ult_i"
    }
    const_field = difficulty_map.get(difficulty)
    const_value = song_info.get(const_field, "")
    return float(const_value) if const_value else None

# 函數：根據 title 查找 maxOps 值
def get_max_ops_value(title):
    song_info = next((item for item in song_data if item["title"] == title), None)
    if not song_info:
        return None
    
    # 從指定的五個欄位中取最大值
    levels = [
        song_info.get("lev_bas_i", ""),
        song_info.get("lev_adv_i", ""),
        song_info.get("lev_exp_i", ""),
        song_info.get("lev_mas_i", ""),
        song_info.get("lev_ult_i", "")
    ]
    
    # 過濾掉空字串並轉換為浮點數
    numeric_levels = [float(level) for level in levels if level]
    
    if not numeric_levels:
        return None  # 如果五個欄位都是空的，返回 None
    
    max_level = max(numeric_levels)
    max_ops = (max_level + 3) * 5
    return max_ops

@app.route('/upload', methods=['POST'])
def upload():
    global scores
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({'error': 'Invalid file type'}), 400

    data = json.load(file)
    scores = data.get("score", [])

    # 加載歌曲數據
    song_data = load_songdata()

    for record in scores:
        const_value = get_const_value(record["title"], record["difficulty"])
        record["const"] = const_value  # 若無匹配值，設為 None

        # 計算 maxOps 值並添加到每個 record
        max_ops_value = get_max_ops_value(record["title"])
        record["maxOps"] = max_ops_value  # 若無匹配值，設為 None

        # 計算 Rank 和 op
        record["Rank"], record["op"] = calculate_rank_and_op(
            record["score"], const_value, record["isAllJustice"], record["isFullCombo"]
        )

    return jsonify({'scores': scores}), 200  # 返回更新後的分數數據

@app.route('/get_scores', methods=['GET'])
def get_scores():
    print(scores.__len__)
    return jsonify({'scores': scores})  # 返回當前的分數數據

@app.route("/simulator")
def simulator():
    return render_template("index.html")

@app.route('/calculate_op_total', methods=['GET'])
def calculate_op_total():
    # 假設 scores 是存儲所有上傳的分數數據的全局變數
    #scores = []  # 此處應替換為實際的數據存儲結構

    total_op = sum(record.get("op", 0) for record in scores)
    
    return {"total_op": total_op}

@app.route('/calculate_op', methods=['POST'])
def calculate_op():
    global scores  # 確保使用全局變數

    # 取得忽略 0 分紀錄的選項
    # ignore_zero = request.args.get('ignore_zero', 'false').lower() == 'true'
    postData = request.json
    ignore_zero = postData.get('ignoreZero', False)
    
    # 建立一個字典來存儲每個唯一標題的最高 OP 和 maxOps 值
    unique_scores = {}
    op_total = 0
    max_ops_total = 0

    for record in scores:
        title = record["title"]
        op_value = record["op"]
        if op_value=="N/A":
            op_value=0
        else:
            op_value=float(op_value)
        if record.get("maxOps", 0)==None:
            print(record)
        else:
            max_ops_value = float(record.get("maxOps", 0))  # 確保有 maxOps 的值

        # 檢查是否是新標題或更高的 OP 值和 maxOps 值
        if title not in unique_scores:
            unique_scores[title] = {"op": op_value, "maxOps": max_ops_value}
        else:
            # 更新 OP 和 maxOps 值
            if op_value > float(unique_scores[title]["op"]):
                unique_scores[title]["op"] = op_value
            # if max_ops_value==None and unique_scores[title]["maxOps"]==None:
            #     print('hi')
            if max_ops_value > float(unique_scores[title]["maxOps"]):
                unique_scores[title]["maxOps"] = max_ops_value
    # 計算加總
    for unique_score in unique_scores.values():
        # 根據選項決定是否忽略 op 為 0 的記錄
        if ignore_zero and unique_score["op"] == 0:
            continue
        const=max_op_to_const(unique_score["maxOps"])
        #13與以下
        if postData['scores']['row_13_below']['score']!='':
            if const<13.5:
                isFullCombo = True if postData['scores']['row_13_below']['fcaj']=="FC" else False
                isAllJustice = True if postData['scores']['row_13_below']['fcaj']=="AJ" else False
                _,op=calculate_rank_and_op(int(postData['scores']['row_13_below']['score']),const,isAllJustice,isFullCombo)
                unique_score["op"]=max(unique_score["op"],op)
                op_total += unique_score["op"]
                max_ops_total += unique_score["maxOps"]
                continue
        #13+
        if postData['scores']['row_13_plus']['score']!='':
            if const<14:
                isFullCombo = True if postData['scores']['row_13_plus']['fcaj']=="FC" else False
                isAllJustice = True if postData['scores']['row_13_plus']['fcaj']=="AJ" else False
                _,op=calculate_rank_and_op(int(postData['scores']['row_13_plus']['score']),const,isAllJustice,isFullCombo)
                unique_score["op"]=max(unique_score["op"],op)
                op_total += unique_score["op"]
                max_ops_total += unique_score["maxOps"]
                continue
        #14
        if postData['scores']['row_14']['score']!='':
            if const<14.5:
                isFullCombo = True if postData['scores']['row_14']['fcaj']=="FC" else False
                isAllJustice = True if postData['scores']['row_14']['fcaj']=="AJ" else False
                _,op=calculate_rank_and_op(int(postData['scores']['row_14']['score']),const,isAllJustice,isFullCombo)
                unique_score["op"]=max(unique_score["op"],op)
                op_total += unique_score["op"]
                max_ops_total += unique_score["maxOps"]
                continue
        #14+
        if postData['scores']['row_14_plus']['score']!='':
            if const<15:
                isFullCombo = True if postData['scores']['row_14_plus']['fcaj']=="FC" else False
                isAllJustice = True if postData['scores']['row_14_plus']['fcaj']=="AJ" else False
                _,op=calculate_rank_and_op(int(postData['scores']['row_14_plus']['score']),const,isAllJustice,isFullCombo)
                unique_score["op"]=max(unique_score["op"],op)
                op_total += unique_score["op"]
                max_ops_total += unique_score["maxOps"]
                continue
        #15
        if postData['scores']['row_15']['score']!='':
            if const<15.5:
                isFullCombo = True if postData['scores']['row_15']['fcaj']=="FC" else False
                isAllJustice = True if postData['scores']['row_15']['fcaj']=="AJ" else False
                _,op=calculate_rank_and_op(int(postData['scores']['row_15']['score']),const,isAllJustice,isFullCombo)
                unique_score["op"]=max(unique_score["op"],op)
                op_total += unique_score["op"]
                max_ops_total += unique_score["maxOps"]
                continue
        op_total += unique_score["op"]
        max_ops_total += unique_score["maxOps"]
    #print(max_ops_total)
    # 計算百分比
    percentage = (op_total / max_ops_total * 100) if max_ops_total > 0 else 0

    return jsonify({'op_total': op_total, 'percentage': f'{percentage:.2f}%'})

def max_op_to_const(op):
    return op/5-3

if __name__ == "__main__":
    app.run(debug=True)
