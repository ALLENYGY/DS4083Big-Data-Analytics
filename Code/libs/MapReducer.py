import pandas as pd
import jieba
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from wordcloud import WordCloud
from snownlp import SnowNLP
import matplotlib.pyplot as plt

class MapReducer:
    def __init__(self,stopwords_file = 'stopwords.txt'):
        with open(stopwords_file, 'r', encoding='utf-8') as file:
            self.stopwords = set(file.read().splitlines())

    def word_count(self,file_path = 'MovieComments.xlsx',num_threads=4,low=1,high=5):
        data = pd.read_excel(file_path)
        filtered_data = data[(data['rate'] >= low) & (data['rate'] <= high)]
        comments = filtered_data['comment'].astype(str)
        chunks = [comments[i::num_threads] for i in range(num_threads)]
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            res = list(executor.map(self.process_comments, chunks))
        self.word_counts = self.reduce_counters(res)
        return self.word_counts
    
    def get_sentiment_score(self):
        num=0
        res=0
        for key in self.word_counts.keys():
            try:
                snlp = SnowNLP(key)
                score = snlp.sentiments*self.word_counts[key]
                res+=score
                num+=self.word_counts[key]
            except:
                continue
        return res/num if num!=0 else 0
    
    def generate_img(self,save_path="wordcloud.png",font_path='simhei.ttf',width=800, height=800):
        wordcloud = WordCloud(font_path=font_path, width=width, height=height, background_color='white').generate_from_frequencies(self.word_counts)
        plt.figure(figsize=(10, 10))
        plt.imshow(wordcloud)
        plt.axis('off')
        plt.savefig(save_path)
        plt.close()

    def process_comments(self,comments):
        words = []
        for comment in comments:
            words.extend([word.strip() for word in jieba.cut(comment) if word.strip() not in self.stopwords])
        return Counter(words)

    def reduce_counters(self,counters):
        total_counter = Counter()
        for counter in counters:
            total_counter.update(counter)
        return total_counter