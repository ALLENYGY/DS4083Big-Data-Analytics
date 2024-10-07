#!/opt/homebrew/Caskroom/miniforge/base/envs/BDA/bin/python3

import sys

current_word = None
current_count = 0

# 从标准输入读取每一行
for line in sys.stdin:
    word, count = line.strip().split('\t')
    count = int(count)

    # 如果遇到新的单词，将前一个单词的计数输出
    if word == current_word:
        current_count += count
    else:
        if current_word is not None:
            print(f"{current_word}\t{current_count}")
        current_word = word
        current_count = count

# 输出最后一个单词的计数
if current_word is not None:
    print(f"{current_word}\t{current_count}")