import pandas as pd
import os,json

def merge_comment_excels(folder_path='tmp', output_path='res.xlsx'):
    all_dataframes = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_excel(file_path)
            all_dataframes.append(df)
    combined_dataframe = pd.concat(all_dataframes, ignore_index=True)
    combined_dataframe.to_excel(output_path, index=False)
