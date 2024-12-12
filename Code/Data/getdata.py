import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}
url = 'https://m.maoyan.com/asgard/asgardapi/mmdb/movieboard/moviedetail/fixedboard/39.json?ci=1&year=0&term=0&limit=100&offset=0'
req = requests.get(url, headers=headers).json()['data']['movies']
# print(req)

def generate_markdown_table(header, data):
    # 生成表头
    table = "| " + " | ".join(header) + " |\n"
    # 生成分隔线
    table += "| " + " | ".join(["---"] * len(header)) + " |\n"
    # 生成数据行
    for row in data:
        table += "| " + " | ".join(str(cell) for cell in row) + " |\n"
    return table


header_list = ["封面", "电影名称", "电影评分", "电影类型", "上映时间", "主演","想看人数"]
data_list = []
for movie in req:
    movie_data = ['![{0}]({1})'.format(movie['nm'], movie['img'].replace('2500x2500', '300x500')), movie['nm'], movie['label']['number'], movie['cat'], movie['pubDesc'], movie['star'],movie['wish']]
    data_list.append(movie_data)

# 生成Markdown表格
markdown_table = generate_markdown_table(header_list, data_list)
with open("maoyantop100.md", "w", encoding='utf8') as file:
    file.write(markdown_table)