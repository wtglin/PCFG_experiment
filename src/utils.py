import random

# 读取密码文件
def load_password_records(filepath):
    # 读密码文件，支持三种：
    # 1. 纯密码：password
    # 2. 密码+次数：password 1
    # 3. 次数+密码：1 password
    records = []

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(maxsplit=1)

            if len(parts) == 2:
                # 尝试第一个是否为数字（权重在前）
                if parts[0].isdigit():
                    cnt = int(parts[0])
                    pwd = parts[1]
                # 尝试第二个是否为数字（权重在后）
                elif parts[1].isdigit():
                    pwd = parts[0]
                    cnt = int(parts[1])
                else:
                    pwd = line
                    cnt = 1
            else:
                pwd = line
                cnt = 1

            if pwd:
                records.append((pwd, cnt))

    return records


# 保存密码文件
def save_password_records(records, filepath):

    with open(filepath, "w", encoding="utf-8") as f:
        for pwd, cnt in records:
            f.write(f"{pwd} {cnt}\n")


# 读取字典文件
def load_dictionary_words(filepath, lowercase=True):
    words = []
    seen = set()

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            word = line.strip()
            if not word:
                continue

            if lowercase:
                word = word.lower()

            # 去重，只保留第一次出现的
            if word not in seen:
                seen.add(word)
                words.append(word)

    return words


# 按长度分组
def group_words_by_length(words):
    grouped = {}

    for word in words:
        length = len(word)
        if length not in grouped:
            grouped[length] = []
        grouped[length].append(word)

    return grouped

