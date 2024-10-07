#!/opt/homebrew/Caskroom/miniforge/base/envs/BDA/bin/python3
import sys

# 读取标准输入的每一行
for line in sys.stdin:
    # 去除行首尾的空白并拆分成单词
    words = line.strip().split()
    # 输出每个单词及计数 1
    for word in words:
        print(f"{word}\t1")