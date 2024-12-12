import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep

class CommentScraper:
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    MAOYAN_BASE_URL = 'https://m.maoyan.com/mmdb/comments/movie/{id}.json?_v_=yes&offset={offset}'
    DOUBAN_BASE_URL = 'https://movie.douban.com/subject/{id}/comments?start={start_idx}&limit=20&status=P&sort=new_score'
    def __init__(self,cookies=None, start_idx=0, batch_size=10, step=20, save_dir='tmp'):
        self.cookies = cookies
        self.start_idx = start_idx
        self.batch_size = batch_size
        self.step = step
        self.save_dir = save_dir

    def config(self,movie_id, platform):
        self.movie_id = movie_id
        self.platform = platform

    def get_maoyan_comments(self, offset):
        url = self.MAOYAN_BASE_URL.format(id=self.movie_id, offset=offset)
        headers = {'User-Agent': self.USER_AGENT}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return pd.DataFrame(), False
        try:
            ans = response.json()
        except ValueError:
            print("JSON ERROR")
            return pd.DataFrame(), False
        if ans.get("total", 0) == 0:
            return pd.DataFrame(), False
        cmts = ans.get("cmts", [])
        data = [{'user': cmt.get('nickName', ''),
                'rate': cmt.get('score', 0),
                'comment': cmt.get('content', '')} for cmt in cmts]
        return pd.DataFrame(data), True

    def get_douban_comments(self, start_idx):
        url = self.DOUBAN_BASE_URL.format(id=self.movie_id, start_idx=start_idx)
        headers = {'User-Agent': self.USER_AGENT}
        response = requests.get(url, headers=headers, cookies=self.cookies)
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all(class_='comment')
        data = []
        for comment in comments:
            # print(comment)
            username = comment.find(class_='comment-info').find('a').text.strip()
            rating = comment.find(class_='rating').get('title') if comment.find(class_='rating') else ""
            content = comment.find(class_='short').text.strip()
            rating_map = {'力荐': 5, '推荐': 4, '还行': 3, '较差': 2, '很差': 1}
            rating = rating_map.get(rating, 0)
            data.append({'user': username, 'rate': rating, 'comment': content})
        return pd.DataFrame(data), len(data) != 0

    def save_comments_to_excel(self, data, start_index, end_index):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        filename = os.path.join(self.save_dir, f"{self.platform}_{self.movie_id}_{start_index}-{end_index}.xlsx")
        data.to_excel(filename, index=False)
        print(f"Saving to {filename}")
    
    def merge_comment_excels(self, output_path='res.xlsx'):
        all_dataframes = []
        folder_path=self.save_dir
        for filename in os.listdir(folder_path):
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                file_path = os.path.join(folder_path, filename)
                df = pd.read_excel(file_path)
                all_dataframes.append(df)
        combined_dataframe = pd.concat(all_dataframes, ignore_index=True)
        combined_dataframe.to_excel(output_path, index=False)

    def run(self):
        has_next = True
        all_data = []
        while has_next:
            if self.platform == 'maoyan':
                print(f"{self.start_idx}-{self.start_idx + self.step} comments")
                comments, has_next = self.get_maoyan_comments(self.start_idx)
            elif self.platform == 'douban':
                print(f"{self.start_idx + 1}-{self.start_idx + 20} comments")
                comments, has_next = self.get_douban_comments(self.start_idx)
            all_data.append(comments)
            self.start_idx += self.step
            if len(all_data) >= self.batch_size or not has_next:
                combined_data = pd.concat(all_data, ignore_index=True)
                self.save_comments_to_excel(combined_data, self.start_idx - len(all_data) * self.step, self.start_idx)
                all_data.clear()
            print("Sleeping ...")
            sleep(0.1)