# 概率计算模块
# 从文法学习器的统计结果计算概率
# 核心思想：
# 1. 从文法学习器获取统计数据（频数）
# 2. 将频数转换为概率（频数 / 总数）
# 3. 提供概率查询接口
#
# 概率模型：
# - P(structure) = count(structure) / total_structures
# - P(digit_segment | length) = count(digit_segment) / total_digit_segments_of_length
# - P(special_segment | length) = count(special_segment) / total_special_segments_of_length

from collections import defaultdict


class ProbabilityCalculator:
    # 概率计算器
    # 从文法学习器的统计数据计算概率
    # 提供结构、数字片段、特殊字符片段的概率查询

    def __init__(self, grammar):
        # 初始化概率计算器
        # 参数：grammar: PCFGGrammar 对象，必须已经通过 learn_from_corpus 学习过
        self.grammar = grammar

        # 存储结构的概率分布
        # 例如: {(('L', 8), ('D', 3)): 0.25, (('L', 6), ('D', 2)): 0.15}
        self.structure_probs = {}

        # 存储数字片段的概率分布
        # 例如: {(3, '123'): 0.10, (2, '12'): 0.08}
        self.digit_segment_probs = {}

        # 存储特殊字符片段的概率分布
        # 例如: {(1, '@'): 0.50, (1, '!'): 0.30}
        self.special_segment_probs = {}

        # 计算所有概率
        self.calculate_probabilities()

    def calculate_probabilities(self):
        # 计算所有概率
        # 三个主要任务：
        # 1. 计算结构概率 P(structure) = count(structure) / total_structures
        # 2. 计算数字片段概率 P(digit_segment | length)
        # 3. 计算特殊字符片段概率 P(special_segment | length)

        # ========== 第一部分：计算结构概率 ==========
        base_structures = self.grammar.get_base_structures()
        total_structures = sum(base_structures.values())

        if total_structures > 0:
            # 将每个结构的计数转换为概率
            for structure, count in base_structures.items():
                self.structure_probs[structure] = count / total_structures

        # ========== 第二部分：计算数字片段概率 ==========
        digit_segments = self.grammar.get_digit_segments()

        # 首先按长度分组数字片段
        digit_by_length = defaultdict(dict)
        for (length, segment), count in digit_segments.items():
            digit_by_length[length][(length, segment)] = count

        # 对每个长度分别计算概率
        for length, segments in digit_by_length.items():
            # 计算该长度下所有数字片段的总数
            total = sum(segments.values())
            if total > 0:
                # 计算该长度内每个数字片段的条件概率
                for key, count in segments.items():
                    self.digit_segment_probs[key] = count / total

        # ========== 第三部分：计算特殊字符片段概率 ==========
        special_segments = self.grammar.get_special_segments()

        # 首先按长度分组特殊字符片段
        special_by_length = defaultdict(dict)
        for (length, segment), count in special_segments.items():
            special_by_length[length][(length, segment)] = count

        # 对每个长度分别计算概率
        for length, segments in special_by_length.items():
            # 计算该长度下所有特殊字符片段的总数
            total = sum(segments.values())
            if total > 0:
                # 计算该长度内每个特殊字符片段的条件概率
                for key, count in segments.items():
                    self.special_segment_probs[key] = count / total

    # ========== 概率查询接口 ==========

    def get_structure_probability(self, structure):
        # 获取结构的概率
        # 参数：structure: 结构元组，如 (('L', 8), ('D', 3))
        # 返回：float: 结构的概率，范围 [0, 1]，不存在返回 0.0
        return self.structure_probs.get(structure, 0.0)

    def get_digit_segment_probability(self, length, segment):
        # 获取数字片段的概率
        # 参数：length: 数字片段的长度, segment: 数字片段的内容
        # 返回：float: 数字片段的条件概率 P(segment | length)，不存在返回 0.0
        return self.digit_segment_probs.get((length, segment), 0.0)

    def get_special_segment_probability(self, length, segment):
        # 获取特殊字符片段的概率
        # 参数：length: 特殊字符片段的长度, segment: 特殊字符片段的内容
        # 返回：float: 特殊字符片段的条件概率 P(segment | length)，不存在返回 0.0
        return self.special_segment_probs.get((length, segment), 0.0)

    # ========== 导出全部概率字典的接口 ==========

    def get_all_structure_probabilities(self):
        # 获取所有结构的概率
        # 返回：dict: {结构元组: 概率} 的字典
        return dict(self.structure_probs)

    def get_all_digit_segment_probabilities(self):
        # 获取所有数字片段的概率
        # 返回：dict: {(长度, 数字串): 概率} 的字典
        return dict(self.digit_segment_probs)

    def get_all_special_segment_probabilities(self):
        # 获取所有特殊字符片段的概率
        # 返回：dict: {(长度, 特殊字符串): 概率} 的字典
        return dict(self.special_segment_probs)
