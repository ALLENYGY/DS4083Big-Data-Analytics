import json
from libs.CommentScraper import CommentScraper
from libs.MapReducer import MapReducer

CONFIG_FILE = 'config.json'

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def auto_get_comments():
    config = load_json(CONFIG_FILE)
    tmp_path='./tmp'
    output='MovieComments.xlsx'
    douban_tasks=config.get("douban")
    maoyan_tasks=config.get("maoyan")
    scraper=CommentScraper(save_dir=tmp_path)
    for task in douban_tasks:
        scraper.config(movie_id=task,platform="douban")
        scraper.run()
    for task in maoyan_tasks:
        scraper.config(movie_id=task, platform="maoyan")
        scraper.run()
    scraper.merge_comment_excels(output_path=output)



if __name__ == "__main__":
    # auto_get_comments()
    mp=MapReducer(stopwords_file='./src/stopwords.txt')
    for rate in range(1,6,2):
        lo,hi=rate,min(5,rate+1)
        wc=mp.word_count(low=lo,high=hi)
        mp.generate_img(save_path=f"cloud_{lo}-{hi}.png",font_path='./src/simhei.ttf')
        print(mp.get_sentiment_score())