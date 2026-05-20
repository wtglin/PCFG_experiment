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

    def __init__(self, grammar):
        self.grammar = grammar
        self.structure_probs = {}
        self.digit_segment_probs = {}
        self.special_segment_probs = {}
        self.letter_segment_probs = {}
        self.calculate_probabilities()

    def calculate_probabilities(self):
        base_structures = self.grammar.get_base_structures()
        total_structures = sum(base_structures.values())

        if total_structures > 0:
            for structure, count in base_structures.items():
                self.structure_probs[structure] = count / total_structures

        digit_segments = self.grammar.get_digit_segments()
        digit_by_length = defaultdict(dict)
        for (length, segment), count in digit_segments.items():
            digit_by_length[length][(length, segment)] = count

        for length, segments in digit_by_length.items():
            total = sum(segments.values())
            if total > 0:
                for key, count in segments.items():
                    self.digit_segment_probs[key] = count / total

        special_segments = self.grammar.get_special_segments()
        special_by_length = defaultdict(dict)
        for (length, segment), count in special_segments.items():
            special_by_length[length][(length, segment)] = count

        for length, segments in special_by_length.items():
            total = sum(segments.values())
            if total > 0:
                for key, count in segments.items():
                    self.special_segment_probs[key] = count / total

        letter_segments = self.grammar.get_letter_segments()
        letter_by_length = defaultdict(dict)
        for (length, segment), count in letter_segments.items():
            letter_by_length[length][(length, segment)] = count

        for length, segments in letter_by_length.items():
            total = sum(segments.values())
            if total > 0:
                for key, count in segments.items():
                    self.letter_segment_probs[key] = count / total

    def get_structure_probability(self, structure):
        return self.structure_probs.get(structure, 0.0)

    def get_digit_segment_probability(self, length, segment):
        return self.digit_segment_probs.get((length, segment), 0.0)

    def get_special_segment_probability(self, length, segment):
        return self.special_segment_probs.get((length, segment), 0.0)

    def get_letter_segment_probability(self, length, segment):
        return self.letter_segment_probs.get((length, segment), 0.0)

    def get_all_structure_probabilities(self):
        return dict(self.structure_probs)

    def get_all_digit_segment_probabilities(self):
        return dict(self.digit_segment_probs)

    def get_all_special_segment_probabilities(self):
        return dict(self.special_segment_probs)

    def get_all_letter_segment_probabilities(self):
        return dict(self.letter_segment_probs)
