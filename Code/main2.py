from libs.KnowledgeGraph import KnowledgeGraph
import pandas as pd
import os

file_path = '../Data/'

columns = ['movie_id']
movie_data = pd.DataFrame(columns=columns)

all_keywords = set()

movie_keywords = {} 
for root, dirs, files in os.walk(file_path):
    for file in files:
        if file.endswith('.xlsx'):
            print(f"Processing: {file}")
            kg = KnowledgeGraph(os.path.join(root, file))
            keywords = kg.build_graph(low=4) 
            movie_id = file[:-5]  
            movie_keywords[movie_id] = keywords
            all_keywords.update(keywords)

all_keywords = sorted(all_keywords)

binary_matrix = pd.DataFrame(0, index=movie_keywords.keys(), columns=all_keywords)

for movie_id, keywords in movie_keywords.items():
    binary_matrix.loc[movie_id, keywords] = 1

binary_matrix.insert(0, 'movie_id', binary_matrix.index)
binary_matrix.reset_index(drop=True, inplace=True)

print(binary_matrix)

# print the column that with the same value 1
print(binary_matrix.loc[:, (binary_matrix == 1).all()])

binary_matrix.to_csv(f'{file_path}movies_keywords_binary_matrix.csv', index=False)
