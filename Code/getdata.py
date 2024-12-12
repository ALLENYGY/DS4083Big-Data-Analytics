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
    output='../Data/1.xlsx'
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
    auto_get_comments()