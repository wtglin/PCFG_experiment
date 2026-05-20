# 文法规则学习模块
# 从密码中提取上下文无关文法规则
# 核心思想：
# 1. 将密码分解为字符类型序列（L/D/S）
# 2. 压缩连续相同类型为规则（如 LLLDD -> (('L', 3), ('D', 2))）
# 3. 统计规则和终端符号的出现频率
# 4. 用于后续的概率计算和密码生成

from collections import defaultdict


class PCFGGrammar:
    # PCFG 文法学习器
    # 从密码语料库中学习文法规则，统计规则和终端符号的频率

    def __init__(self):
        self.base_structures = defaultdict(int)
        self.digit_segments = defaultdict(int)
        self.special_segments = defaultdict(int)
        self.letter_length_dist = defaultdict(int)
        self.letter_segments = defaultdict(int)

    def classify_char(self, char):
        # 将单个字符分类为基本类型
        # L: 字母（Letter），包括大小写 a-z, A-Z
        # D: 数字（Digit），0-9
        # S: 特殊字符（Special），其他所有字符
        if char.isalpha():
            return 'L'
        elif char.isdigit():
            return 'D'
        else:
            return 'S'

    def split_into_segments(self, password):
        # 将密码切分为连续的字符片段
        # 每个片段包含相同类型的连续字符
        # 例子：
        # "password123" -> [('L', 'password'), ('D', '123')]
        # "Test@123" -> [('L', 'Test'), ('S', '@'), ('D', '123')]
        if not password:
            return []

        segments = []
        current_type = self.classify_char(password[0])
        current_content = password[0]

        # 遍历密码中的每个字符（从第二个开始）
        for char in password[1:]:
            char_type = self.classify_char(char)

            if char_type == current_type:
                # 如果类型相同，追加到当前片段
                current_content += char
            else:
                # 如果类型不同，保存当前片段，开始新片段
                segments.append((current_type, current_content))
                current_type = char_type
                current_content = char

        # 保存最后一个片段
        segments.append((current_type, current_content))

        return segments

    def segments_to_structure(self, segments):
        # 将片段列表转换为结构元组
        # 将 (类型, 内容) 的片段列表转换为 (类型, 长度) 的元组
        # 例子：
        # [('L', 'password'), ('D', '123')] -> (('L', 8), ('D', 3))
        structure = []
        for seg_type, seg_content in segments:
            seg_length = len(seg_content)
            structure.append((seg_type, seg_length))

        return tuple(structure)

    def learn_from_password(self, password, count=1):
        if not password:
            return

        segments = self.split_into_segments(password)
        structure = self.segments_to_structure(segments)

        self.base_structures[structure] += count
        for seg_type, seg_content in segments:
            seg_length = len(seg_content)

            if seg_type == 'D':
                self.digit_segments[(seg_length, seg_content)] += count
            elif seg_type == 'S':
                self.special_segments[(seg_length, seg_content)] += count
            elif seg_type == 'L':
                self.letter_length_dist[seg_length] += count
                self.letter_segments[(seg_length, seg_content.lower())] += count

    def learn_from_corpus(self, records):
        # 从密码语料库学习规则
        # 批量处理多个密码，对每个密码调用 learn_from_password
        for item in records:
            if isinstance(item, tuple):
                password, count = item
                self.learn_from_password(password, count)
            else:
                self.learn_from_password(item, 1)

    def extract_structure(self, password):
        # 提取单个密码的结构
        # 返回该密码对应的结构元组
        # 例子：
        # "password123" -> (('L', 8), ('D', 3))
        # "Test@123" -> (('L', 4), ('S', 1), ('D', 3))
        if not password:
            return ()

        segments = self.split_into_segments(password)
        structure = self.segments_to_structure(segments)
        return structure

    # ========== Getter 接口 ==========

    def get_base_structures(self):
        # 获取所有基础结构及其计数
        # 返回：dict: {结构元组: 计数}
        # 例子：
        # {
        #     (('L', 8), ('D', 3)): 5,
        #     (('L', 6), ('D', 2)): 3,
        #     (('L', 4), ('S', 1), ('D', 3)): 2
        # }
        return dict(self.base_structures)

    def get_digit_segments(self):
        # 获取所有数字片段及其计数
        # 返回：dict: {(长度, 数字串): 计数}
        # 例子：
        # {
        #     (3, '123'): 10,
        #     (2, '12'): 8,
        #     (4, '2024'): 5
        # }
        return dict(self.digit_segments)

    def get_special_segments(self):
        # 获取所有特殊字符片段及其计数
        # 返回：dict: {(长度, 特殊字符串): 计数}
        # 例子：
        # {
        #     (1, '@'): 15,
        #     (1, '!'): 10,
        #     (2, '@#'): 3
        # }
        return dict(self.special_segments)

    def get_letter_length_dist(self):
        # 获取字母片段的长度分布
        # 返回：dict: {长度: 计数}
        # 例子：
        # {
        #     8: 100,
        #     6: 50,
        #     10: 30,
        #     4: 20
        # }
        return dict(self.letter_length_dist)

    def get_structure_count(self, structure):
        # 获取特定结构的计数
        # 参数：structure: 结构元组，如 (('L', 8), ('D', 3))
        # 返回：int: 该结构出现的次数，如果不存在返回 0
        return self.base_structures.get(structure, 0)

    def get_digit_segment_count(self, length, content):
        # 获取特定数字片段的计数
        # 参数：length: 数字片段的长度, content: 数字片段的内容
        # 返回：int: 该数字片段出现的次数，如果不存在返回 0
        return self.digit_segments.get((length, content), 0)

    def get_special_segment_count(self, length, content):
        # 获取特定特殊字符片段的计数
        # 参数：length: 特殊字符片段的长度, content: 特殊字符片段的内容
        # 返回：int: 该特殊字符片段出现的次数，如果不存在返回 0
        return self.special_segments.get((length, content), 0)

    def get_letter_length_count(self, length):
        return self.letter_length_dist.get(length, 0)

    def get_letter_segments(self):
        return dict(self.letter_segments)
