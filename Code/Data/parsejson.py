import json

# JSON 文件路径
json_file_path = "allMovies.json"

# 读取 JSON 文件
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# 构建目标格式
result = {"movies": []}

for record in data["RECORDS"]:
    movie = {
        "name": record["title"],  # 提取电影名
        "douban": int(record["id"]),  # 提取豆瓣ID并转换为整数
    }
    result["movies"].append(movie)

print(f"Total movies: {len(result['movies'])}")
# 去重
result["movies"] = [dict(t) for t in {tuple(d.items()) for d in result["movies"]}]
print(f"Total movies: {len(result['movies'])}")


# 转换为 JSON 字符串
formatted_json = json.dumps(result, ensure_ascii=False, indent=4)

# 打印结果
# print(formatted_json)

# 可选：将结果保存为新的 JSON 文件
output_file_path = "formatted_movies.json"
with open(output_file_path, "w", encoding="utf-8") as output_file:
    output_file.write(formatted_json)
