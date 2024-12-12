import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import logging
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


class MovieInfoScraper:
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    MAOYAN_MOVIE_LIST_URL = 'https://www.maoyan.com/films?showType=3&offset={offset}'
    MAOYAN_MOVIE_INFO_URL = 'https://apis.netstart.cn/maoyan/movie/detail?movieId={movie_id}'
    MAOYAN_BASE_URL = 'https://m.maoyan.com/mmdb/comments/movie/{id}.json?_v_=yes&offset={offset}'

    # https://apis.netstart.cn/maoyan/movie/detail?movieId=1443567

    def __init__(self, save_dir='.tmp'):
        self.save_dir = save_dir
        logging.basicConfig(level=logging.INFO, filename='maoyan_scraper.log', filemode='a',
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def get_maoyan_movie_list(self, offset=0):
        url = self.MAOYAN_MOVIE_LIST_URL.format(offset=offset)
        headers = {'User-Agent': self.USER_AGENT}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for URL: {url}, Error: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        movie_items = soup.find_all('dd')
        movie_list = []

        for item in movie_items:
            try:
                link = item.find('a', href=True)
                movie_id = link['href'].split('/')[-1] if link else "Unknown"
                title = item.find('div', class_='channel-detail movie-item-title').text.strip() if item.find('div', class_='channel-detail movie-item-title') else "Unknown"
                genre = item.find('div', class_='movie-hover-info').find_all('span', class_='hover-tag')[1].next_sibling.strip() if item.find('div', class_='movie-hover-info') else "Unknown"
                release_date = item.find('div', class_='movie-hover-title movie-hover-brief').text.split('上映时间:')[-1].strip() if item.find('div', class_='movie-hover-title movie-hover-brief') else "Unknown"
                movie_list.append({
                    'movie_id': movie_id,
                    'title': title,
                    'genre': genre,
                    'release_date': release_date,
                })
            except Exception as e:
                logging.error(f"Error extracting movie details: {e}")

        return movie_list

    def save_movie_list_to_excel(self, data, offset):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        filename = os.path.join(self.save_dir, f"maoyan_movie_list_offset_{offset}.xlsx")
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        logging.info(f"Saving to {filename}")

    def run_list_scraper(self, start_offset=0, step=30, max_pages=10):
        for i in range(max_pages):
            offset = start_offset + i * step
            logging.info(f"Scraping page with offset {offset}")
            movie_list = self.get_maoyan_movie_list(offset=offset)
            if movie_list:
                self.save_movie_list_to_excel(movie_list, offset)
            else:
                logging.warning("Failed to retrieve movie list or no more data available.")
            # Add delay to prevent being blocked
            time.sleep(random.uniform(1, 3))

    def merge_all_excels(self, output_path='Maoyan_Movie_Info.xlsx'):
        all_dataframes = []
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                file_path = os.path.join(self.save_dir, filename)
                df = pd.read_excel(file_path)
                all_dataframes.append(df)
        movie_id_list = []

        if all_dataframes:
            combined_dataframe = pd.concat(all_dataframes, ignore_index=True)
            combined_dataframe.to_excel(output_path, index=False)
            movie_id_list = combined_dataframe['movie_id'].tolist()
            logging.info(f"All Excel files merged and saved to {output_path}")
        else:
            logging.warning("No Excel files found to merge.")

        return movie_id_list

    def get_movie_details(self, movie_id):
        url = self.MAOYAN_MOVIE_INFO_URL.format(movie_id=movie_id)
        headers = {'User-Agent': self.USER_AGENT}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for movie ID {movie_id}, Error: {e}")
            return {}

        try:
            data = response.json()
            movie_data = data.get('$share', {}).get('wechat', {}).get('message', {})
            mbox_data = data.get('mbox', {}).get('mbox', {})
            movie_details = {
                'movie_id': movie_id,
                'title': movie_data.get('title', 'Unknown'),
                'dra': movie_data.get('desc', 'No description available'),
                'sumBox': mbox_data.get('sumBox', 0),
                'firstWeekBox': mbox_data.get('firstWeekBox', 0),
                'release_date': data.get('movie', {}).get('pubDesc', 'Unknown'),
                'genre': data.get('movie', {}).get('cat', 'Unknown')
            }
            return movie_details
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response for movie ID {movie_id}, Error: {e}")
            return {}

    def scrape_movie_details(self, movie_id_list, batch_size=100, output_path='movie_details.xlsx'):
        movie_details_list = []
        batch_counter = 0

        for index, movie_id in enumerate(movie_id_list, start=1):
            logging.info(f"Scraping details for movie ID {movie_id}")
            details = self.get_movie_details(movie_id)
            if details:
                movie_details_list.append(details)
                print(f"Successfully scraped details for movie ID {movie_id} ({index}/{len(movie_id_list)})")

            # Save every batch_size records to avoid high memory usage
            if len(movie_details_list) >= batch_size:
                batch_counter += 1
                batch_filename = os.path.join(self.save_dir, f"movie_details_batch_{batch_counter}.xlsx")
                self.save_movie_details_to_excel(movie_details_list, batch_filename)
                print(f"Saved batch {batch_counter} to {batch_filename}")
                movie_details_list = []  # Reset list after saving

        # Save any remaining movie details
        if movie_details_list:
            batch_counter += 1
            batch_filename = os.path.join(self.save_dir, f"movie_details_batch_{batch_counter}.xlsx")
            self.save_movie_details_to_excel(movie_details_list, batch_filename)

        # Merge all saved Excel files
        self.merge_all_excels(output_path)
    
    def get_movie_info(self, movie_id):
        """
        从电影详情 API 提取所需的字段
        :param movie_id: 电影ID
        :return: 包含所需字段的字典
        """
        headers = {'User-Agent': self.USER_AGENT}
        url = self.MAOYAN_MOVIE_INFO_URL.format(movie_id=movie_id)
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # 提取所需字段
            movie_data = data.get("movie", {})
            movie_info = {
                "movie_id": movie_id,
                "cat": movie_data.get("cat"),  # 类别
                "dra": movie_data.get("dra"),  # 剧情简介
                "oriLang": movie_data.get("oriLang"),  # 原语言
                "nm": movie_data.get("nm"),  # 电影名称
                "sc": movie_data.get("sc"),  # 评分
                "star": movie_data.get("star"),  # 主演
                "pubDesc": movie_data.get("pubDesc"),  # 上映日期
                "dur": movie_data.get("dur"),  # 时长
                "src": movie_data.get("src"),  # 制片地区
            }
            return movie_info
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch movie info for movie ID {movie_id}, Error: {e}")
            return {}

    def get_movie_comments(self, movie_id, max_pages=10):
        """
        获取电影的评论（普通评论和热门评论）
        :param movie_id: 电影ID
        :param max_pages: 最大页数（每页20条评论）
        :return: 合并的评论列表
        """
        headers = {'User-Agent': self.USER_AGENT}
        all_comments = []
        print(f"Fetching comments for movie ID {movie_id}")
        for page in range(max_pages):
            offset = page * 20
            url = self.MAOYAN_BASE_URL.format(id=movie_id, offset=offset)
            print(f"Fetching comments for movie ID {movie_id}, offset {offset}")
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                # 提取普通评论并标记类型
                if "cmts" in data:
                    for comment in data["cmts"]:
                        comment["comment_type"] = "normal"
                        all_comments.append(comment)
                # 提取热门评论并标记类型（只需第一页）
                if page == 0 and "hcmts" in data:
                    for hot_comment in data["hcmts"]:
                        hot_comment["comment_type"] = "hot"
                        all_comments.append(hot_comment)
                # 如果当前页没有普通评论，提前结束
                if not data.get("cmts"):
                    break
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to fetch comments for movie ID {movie_id}, offset {offset}, Error: {e}")
                break
            # 延时，防止反爬
            time.sleep(random.uniform(1, 3))

        return all_comments

    def save_movie_details_to_excel(self, movie_details_list, filename):
        df = pd.DataFrame(movie_details_list)
        df.to_excel(filename, index=False)
        logging.info(f"Movie details saved to {filename}")
    
    def save_comments_to_csv(self, comments, movie_id, comment_type='comments'):
        """
        保存评论到 CSV 文件
        :param comments: 评论列表
        :param movie_id: 电影ID
        :param comment_type: 评论类型（comments 或 hot_comments）
        """
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        filename = os.path.join(self.save_dir, f"movie_{movie_id}_{comment_type}.csv")
        # 提取所需字段
        cleaned_data = [
            {
                "comment_id": comment.get("id"),
                "user_id": comment.get("userId"),
                "nick": comment.get("nick"),
                "content": comment.get("content"),
                "score": comment.get("score"),
                "cityName": comment.get("cityName"),
                "startTime": comment.get("startTime"),
                "approve": comment.get("approve"),
                "oppose": comment.get("oppose"),
                "reply": comment.get("reply"),
                "userLevel": comment.get("userLevel"),
            }
            for comment in comments
        ]
        df = pd.DataFrame(cleaned_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logging.info(f"Saved {comment_type} for movie ID {movie_id} to {filename}")

    def fetch_and_save_comments(self, movie_id, max_pages=10):
        """
        获取电影评论并保存到 CSV 文件
        :param movie_id: 电影ID
        :param max_pages: 最大页数
        """
        comments = self.get_movie_comments(movie_id, max_pages)
        if comments:
            self.save_comments_to_csv(comments, movie_id, comment_type='comments')
            print(f"Successfully saved comments for movie ID {movie_id}")
        else:
            logging.warning(f"No comments found for movie ID {movie_id}")

if __name__ == '__main__':
    scraper = MovieInfoScraper()

    # 从文件加载电影ID列表
    df = pd.read_excel('../src/Maoyan_Movie_Info.xlsx')
    movie_id_list = df['movie_id'].tolist()

    # find specific movie_id index 
    index = movie_id_list.index(723)
    movie_id_list = movie_id_list[index:]

    # 设置最大线程数
    max_threads = 10  # 可根据系统资源调整


    with ThreadPoolExecutor(max_threads) as executor:
        futures = [
            executor.submit(scraper.fetch_and_save_comments, movie_id, 10)
            for movie_id in movie_id_list
        ]

        # 显示进度条
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                future.result()  # 捕获可能的异常
            except Exception as e:
                logging.error(f"An error occurred: {e}")

# if __name__ == '__main__':
#     scraper = MovieInfoScraper()
#     # scraper.run_list_scraper(start_offset=0, step=30, max_pages=10)
#     # movie_id_list = scraper.merge_all_excels()
#     # read Maoyan_Movie_Info.xlsx
#     df=pd.read_excel('../src/Maoyan_Movie_Info.xlsx')
#     movie_id_list = df['movie_id'].tolist()
#     for id in tqdm(movie_id_list):
#         comments=scraper.get_movie_comments(movie_id=id, max_pages=10)
#         scraper.save_comments_to_csv(comments=comments, movie_id=id, comment_type='comments')

