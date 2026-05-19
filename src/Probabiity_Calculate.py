from collections import defaultdict

# 初始化概率字典
base_structure_probabilities = defaultdict(float)
segment_probabilities = {
    'L': defaultdict(float),
    'D': defaultdict(float),
    'S': defaultdict(float)
}
seg_pr_train = defaultdict(float)
seg_pr_train_chr = defaultdict(float)
def parse_structure(password):
    """从密码中提取基础结构"""
    structure = ""
    segments = []
    current_segment = ""

    for char in password:
        if char.isalpha():
            if current_segment and not current_segment.isalpha():
                segments.append(current_segment)
                current_segment = ""
            current_segment += char
        elif char.isdigit():
            if current_segment and not current_segment.isdigit():
                segments.append(current_segment)
                current_segment = ""
            current_segment += char
        else:
            if current_segment and current_segment.isalnum():
                segments.append(current_segment)
                current_segment = ""
            current_segment += char

    if current_segment:
        segments.append(current_segment)

    for seg in segments:
        if seg.isalpha():
            structure += 'L' + str(len(seg))
        elif seg.isdigit():
            structure += 'D' + str(len(seg))
        else:
            structure += 'S' + str(len(seg))

    return structure, segments
# ('L5D3S4L2D1S1', ['dhsac', '214', '&%$#', 'as', '4', '$'])

def learn_probabilities(file_path):
    """从训练集中学习 base structure 和 L, D, S 段的概率"""
    total_passwords = 0
    segment_counts = {
        'L': 0,
        'D': 0,
        'S': 0
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            structure, segments = parse_structure(line)
            base_structure_probabilities[structure] += 1

            for seg in segments:
                seg_pr_train[seg] += 1
                if seg.isalpha():
                    segment_probabilities['L'][len(seg)] += 1
                    segment_counts['L'] += 1
                elif seg.isdigit():
                    segment_probabilities['D'][len(seg)] += 1
                    segment_counts['D'] += 1
                else:
                    segment_probabilities['S'][len(seg)] += 1
                    segment_counts['S'] += 1

            total_passwords += 1

    # 计算 base structure 的概率
    for structure in base_structure_probabilities:
        base_structure_probabilities[structure] /= total_passwords

    # 计算 L, D, S 段的概率
    for seg in seg_pr_train:
        if seg.isdigit():
            seg_pr_train[seg] /= segment_probabilities['D'][len(seg)]
        elif seg.isalpha():
            seg_pr_train[seg] /= segment_probabilities['L'][len(seg)]
            seg_pr_train_chr[seg] = seg_pr_train[seg]
        else:
            seg_pr_train[seg] /= segment_probabilities['S'][len(seg)]

# 从字典中学习
learn_probabilities('myspace_train.txt')
# 对字典按值进行降序排序
sorted_items = sorted(base_structure_probabilities.items(), key=lambda item: item[1], reverse=True)
base_structure_probabilities = dict(sorted_items)
with open('base_structure_probabilities.txt', 'w', encoding='utf-8') as file:
    for key, value in base_structure_probabilities.items():
        file.write(f'{key}: {value}\n')
with open('seg_pr_train.txt', 'w', encoding='utf-8') as file:
    for key, value in seg_pr_train.items():
        file.write(f'{key}: {value}\n')
with open('seg_pr_train_chr.txt', 'w', encoding='utf-8') as file:
    for key, value in seg_pr_train_chr.items():
        file.write(f'{key}: {value}\n')
L_dic = segment_probabilities['L']
L_total = sum(L_dic.values())
