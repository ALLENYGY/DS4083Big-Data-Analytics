import pandas as pd
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import spacy

class KnowledgeGraph:
    def __init__(self, file_path=None,pd_data=None,has_rate=True, stopwords_file='./src/stopwords.txt'):
        if file_path:
            self.data = pd.read_excel(file_path)
        elif pd_data:
            self.data = pd_data
        else:
            raise "No Data"
        self.has_rate = has_rate
        self.nlp = spacy.load("zh_core_web_md")
        self.interested_deps = {"nsubj", "dobj", "iobj", "amod", "mark", "compound", "attr", "pobj"}
        self.graph = defaultdict(set)
        plt.rcParams['font.sans-serif'] = ['SimHei'] 
        plt.rcParams['font.family']='sans-serif'
        with open(stopwords_file, 'r', encoding='utf-8') as file:
            self.stopwords = set(file.read().splitlines())

    def filter_comments(self, low=1, high=5):
        filtered_data = self.data[(self.data['rate'] >= low) & (self.data['rate'] <= high)]
        return filtered_data['comment'].astype(str)

    def build_graph(self, low=1, high=5):
        if self.has_rate:
            comments = self.filter_comments(low, high)
        comments=self.data.astype(str)
        for comment in comments:
            doc = self.nlp(comment)
            entities = {ent.text: ent for ent in doc.ents if ent.text not in self.stopwords}
            for entity_text, entity in entities.items():
                head_token = entity.root.head
                if head_token.text in self.stopwords or head_token.dep_ not in self.interested_deps:
                    continue
                self.graph[head_token.text].add(entity_text)
        pagerank_scores = self.calculate_pagerank()
        # Sorted by PageRank scores
        a=[]
        words=[]
        for word,v in pagerank_scores.items():
            a.append([v,word])
            words.append(word)
        a=sorted(a,key=lambda x:x[0],reverse=True)
        # sorted_pagerank_scores = sorted(pagerank_scores, key=pagerank_scores.get, reverse=True)
        # with open('pagerank.txt','w',encoding='utf-8') as f:
        #     for i in a:
        #         f.write(i[1]+' '+str(i[0])+'\n')
        # only return words
        return words
        
        
        # print(sorted_pagerank_scores)

        
        # self.visualize_graph(pagerank_scores)

    def visualize_graph(self, pagerank_scores=None, top_n=100):
        G = nx.DiGraph()
        for head, edges in self.graph.items():
            for dep in edges:
                G.add_edge(head,dep)
        if pagerank_scores:
            top_nodes = sorted(pagerank_scores, key=pagerank_scores.get, reverse=True)[:top_n]
            G = G.subgraph(top_nodes)
            node_sizes = [pagerank_scores[node] * 50000 for node in G.nodes()]
        else:
            node_sizes = [30000] * G.number_of_nodes()
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, with_labels=True, node_size=node_sizes, node_color='lightblue', edge_color='gray', 
                font_size=10)
        plt.title("Top Nodes by PageRank")
        plt.savefig('top_knowledge_graph.png', format='png')
        plt.show()

    def calculate_pagerank(self):
        G = nx.DiGraph()
        for head, edges in self.graph.items():
            for dep in edges:
                G.add_edge(head, dep)
        pagerank_scores = nx.pagerank(G, alpha=0.85)
        # print("PageRank Scores:", pagerank_scores)
        return pagerank_scores
