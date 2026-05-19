import itertools
from Probabiity_Calculate import *
from Calculate_Dictionary import *
import heapq  # Python的heapq模块实现了优先队列
from line_profiler_pycharm import profile
def calculate_probability_train(password):
    # 计算给定密码概率
    structure, segments = parse_structure(password)
    base_pr = base_structure_probabilities.get(structure, 0)
    for seg in segments:
        seg_pr = seg_pr_train.get(seg, 0)
        base_pr *= seg_pr
    return base_pr


def calculate_probability_dic(password):
    # 计算给定密码概率
    structure, segments = parse_structure(password)
    base_pr = base_structure_probabilities.get(structure, 0)
    for seg in segments:
        if seg.isalpha():
            seg_pr = specific_L_segment_probabilities.get(seg, 0)
        else:
            seg_pr = seg_pr_train.get(seg, 0)
        base_pr *= seg_pr
    return base_pr

@profile
def decrement(structure, i):
    # 生成次优先级结构
    # 定义三种segment类型的正则表达式
    patterns = {
        'digit': r'\d+',  # 匹配一段纯数字
        'special': r'[^a-zA-Z0-9]+',  # 匹配一段特殊符号（非字母、非数字）
        'L_segment': r'L\d'  # 匹配以L开头，后跟一个数字的段
    }

    # 将三个模式组合成一个模式，用于分词
    combined_pattern = re.compile(f"({patterns['digit']}|{patterns['special']}|{patterns['L_segment']})")

    # 使用combined_pattern查找所有匹配的segment
    segments = combined_pattern.findall(structure)

    # 定义匹配以 L 开头后跟一个数字的正则表达式
    pattern = re.compile(r'^L\d$')

    # 使用列表推导式过滤掉所有匹配的项
    filtered_items = [item for item in segments if not pattern.match(item)]

    # 目标段替换
    target_segment = filtered_items[i]
    target_value = seg_pr_train.get(target_segment, 0)

    # 检查是否找到目标段的值
    if target_value is None:
        print(f"Error: '{target_segment}' not found in seg_pr_train.")
    elif target_segment.isdigit():
        # 筛选满足条件的键
        matching_keys = [
            k for k, v in seg_pr_train.items()
            if len(k) == len(target_segment) and k.isdigit() and v <= target_value and k != target_segment
        ]
        probabilities = [
            v for k, v in seg_pr_train.items()
            if len(k) == len(target_segment) and k.isdigit() and v <= target_value and k != target_segment
        ]
        probabilities = [p / target_value for p in probabilities]
        # 生成所有可能的替换结果
        # 确保替换项前面不能是L
        # 使用前向否定查找 (?<!L) 来确保前面不是 'L'
        results = [re.sub(rf'(?<!L){target_segment}', k, structure) for k in matching_keys]
    else:
        # 筛选满足条件的键
        matching_keys = [
            k for k, v in seg_pr_train.items()
            if len(k) == len(target_segment) and not k.isdigit() and not k.isalpha() and v <= target_value and k != target_segment
        ]
        probabilities = [
            v for k, v in seg_pr_train.items()
            if len(k) == len(target_segment) and not k.isdigit() and not k.isalpha() and v <= target_value and k != target_segment
        ]
        probabilities = [p / target_value for p in probabilities]
        # # 生成所有可能的替换结果
        # results = [re.sub(target_segment, k, structure) for k in matching_keys]
        results = []
        for k in matching_keys:
            try:
                # 尝试替换，如果发生错误就跳过
                if k.endswith("\\"):
                    k += "\\"
                sub = re.sub(target_segment, k, structure)
                results.append(sub)
            except re.error:
                print('error')
                continue
    return probabilities, results  # 示例：返回未改变的结构

def split_base_structure(structure):
    # 使用正则表达式匹配 L, D, S 段，每个段是一个字母加一个或多个数字
    segments = re.findall(r'[LDS]\d+', structure)
    return segments

def whether_decrement(structure,i):
    patterns = {
        'digit': r'\d+',  # 匹配一段纯数字
        'special': r'[^a-zA-Z0-9]+',  # 匹配一段特殊符号（非字母、非数字）
        'L_segment': r'L\d'  # 匹配以L开头，后跟一个数字的段
    }

    # 将三个模式组合成一个模式，用于分词
    combined_pattern = re.compile(f"({patterns['digit']}|{patterns['special']}|{patterns['L_segment']})")

    # 使用combined_pattern查找所有匹配的segment
    segments = combined_pattern.findall(structure)

    # 定义匹配以 L 开头后跟一个数字的正则表达式
    pattern = re.compile(r'^L\d$')

    # 使用列表推导式过滤掉所有匹配的项
    filtered_items = [item for item in segments if not pattern.match(item)]

    if i > len(filtered_items) - 1:
        return False
    else:
        return True

def whether_generate_all(working_value):
    pattern = re.compile(r'L(\d)')
    structure = working_value['structure']

    # 查找所有匹配的 L 加数字片段
    matches = list(pattern.finditer(structure))
    if not matches:
        return False
    else:
        return True

@profile
def generate_all_replacements(working_value, segment_probabilities):
    # pre_terminal TO terminal
    # 正则表达式匹配 L 加数字的片段
    pattern = re.compile(r'L(\d)')
    structure = working_value['structure']

    # 查找所有匹配的 L 加数字片段
    matches = list(pattern.finditer(structure))

    # 生成所有可能的替换
    replacements = []
    for match in matches:
        length = int(match.group(1))
        matching_keys = [k for k in segment_probabilities.keys() if len(k) == length]
        replacements.append(matching_keys)

    # 存储列表
    possible_replacements = []

    # 遍历所有组合并替换
    for combination in itertools.product(*replacements):
        temp_structure = structure
        for key in combination:
            temp_structure = re.sub(r'L\d', key, temp_structure, 1)
        possible_replacements.append(temp_structure)

    return possible_replacements

@profile
def generate_password_guesses(base_structures):
    priority_queue = []

    # 初始化优先队列
    for base_structure in base_structures:
        base_pr = base_structure_probabilities[base_structure]
        segments = split_base_structure(base_structure)
        combined_word = ""
        num_l = 0

        for seg in segments:
            if seg[0]== 'D':
                values = {k: v for k, v in seg_pr_train.items() if len(k) == int(seg[1]) and k.isdigit()}
                # 概率从高到低排序
                sorted_values = sorted(values.items(), key=lambda item: item[1], reverse=True)
                # 取出概率最高的
                top_value = sorted_values[0][0]
                base_pr *= seg_pr_train[top_value]

            elif seg[0]== 'L':
                top_value = seg
                num_l += 1
                base_pr *= 1 / L_dic[int(seg[1])]

            else:
                values = {k: v for k, v in seg_pr_train.items() if len(k) == int(seg[1]) and not k.isdigit() and not k.isalpha()}
                # 概率从高到低排序
                sorted_values = sorted(values.items(), key=lambda item: item[1], reverse=True)
                # 取出概率最高的
                top_value = sorted_values[0][0]
                base_pr *= seg_pr_train[top_value]

            combined_word += top_value

        working_value = {
            'structure': combined_word,  # 最可能的pre_terminal
            'pivot_value': 0,
            'num_strings': len(segments)-num_l,  # 假设base_structure长度为字符串数
            'probability': base_pr
        }
        # 将结构插入优先队列（使用负值作为优先级，因为heapq是最小堆）
        heapq.heappush(priority_queue, (-working_value['probability'],id(working_value), working_value))

    with open('array_data.txt', 'w', encoding='utf-8') as file:
        for item in priority_queue:
            file.write(f"{item}\n")

    # 生成密码猜测
    total_num = 0
    password_list = []
    ii = 0

    while priority_queue and total_num < 3e8:
        # 弹出优先级最高的项
        _,_,working_value = heapq.heappop(priority_queue)
        # 执行生成所有可能的替换
        if whether_generate_all(working_value):
            all_working_values = generate_all_replacements(working_value, seg_pr_train_chr)
            total_num += len(all_working_values)
            password_list += all_working_values
            print(total_num)

            if len(password_list) > 1e8:
                ii += 1
                print('正在写入')
                print(ii)
                # 将列表写入到本地文件
                with open(f"passwords_{ii}.txt", 'w', encoding='utf-8') as file:
                    for password in password_list:
                        file.write(password + '\n')
                password_list = []



        # 在每个pivot值上生成新的结构
        for i in range(working_value['pivot_value'], working_value['num_strings']):
            if whether_decrement(working_value['structure'], i):
                probabilities, new_structures = decrement(working_value['structure'], i)
                for probability, new_structure in zip(probabilities, new_structures):
                    new_value = {
                        'structure': new_structure,
                        'pivot_value': i + 1,
                        'num_strings': working_value['num_strings'],
                        'probability': working_value['probability'] * probability
                    }
                    # 插入新的结构到优先队列
                    heapq.heappush(priority_queue, (-new_value['probability'], id(new_value), new_value))

    return password_list

# 调用
base_structures = [key for key in base_structure_probabilities.keys()]

password_list = generate_password_guesses(base_structures)
with open('passwords_last.txt', 'w', encoding='utf-8') as file:
    for password in password_list:
        file.write(password + '\n')
