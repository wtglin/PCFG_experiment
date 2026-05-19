import heapq
from collections import defaultdict


class PreTerminal:
    #用基础结构 + 数字，特殊字符片段填充
    #字母槽位保留为长度标识，不填充具体词汇

    def __init__(self, base_structure, digit_parts, special_parts, probability, pivot):
        self.base_structure = base_structure
        self.digit_parts = digit_parts
        self.special_parts = special_parts
        self.probability = probability
        self.pivot = pivot

    def __lt__(self, other):
        return self.probability > other.probability

    def is_complete(self):
        for i, (seg_type, _) in enumerate(self.base_structure):
            if seg_type == 'D' and i not in self.digit_parts:
                return False
            if seg_type == 'S' and i not in self.special_parts:
                return False
        return True

    def get_representation(self):
        result = []
        for i, (seg_type, seg_len) in enumerate(self.base_structure):
            if seg_type == 'L':
                result.append(('L', seg_len))
            elif seg_type == 'D':
                result.append(('D', self.digit_parts.get(i, seg_len)))
            elif seg_type == 'S':
                result.append(('S', self.special_parts.get(i, seg_len)))
        return result


class Terminal:
    #终端结构：预终结结构 + 字母槽位填充的字典词

    def __init__(self, pre_term, letter_parts, probability, pivot):
        self.pre_term = pre_term
        self.letter_parts = letter_parts
        self.probability = probability
        self.pivot = pivot

    def __lt__(self, other):
        return self.probability > other.probability

    def is_complete(self):
        for i, (seg_type, _) in enumerate(self.pre_term.base_structure):
            if seg_type == 'L' and i not in self.letter_parts:
                return False
        return True

    def get_password(self):
        parts = []
        reprs = self.pre_term.get_representation()
        for i, (seg_type, seg_val) in enumerate(reprs):
            if seg_type == 'L':
                parts.append(self.letter_parts[i])
            else:
                parts.append(seg_val)
        return ''.join(parts)


class PasswordGenerator:
    #保持原有算法结构：优先队列 + pivot + 双阶段生成

    def __init__(self, grammar, prob_calc, dictionary=None):
        self.grammar = grammar
        self.prob_calc = prob_calc
        self.dictionary = dictionary or []

        self.dict_by_length = defaultdict(list)
        self.word_prob_cache = {}

        self._digit_candidate_cache = {}
        self._special_candidate_cache = {}
        self._base_structure_cache = None

        self._build_dict_index()

    def _build_dict_index(self):
        #建立字典长度索引和词概率缓存
        for word in self.dictionary:
            self.dict_by_length[len(word)].append(word)

        for length, words in self.dict_by_length.items():
            prob = 1.0 / len(words) if words else 0
            for w in words:
                self.word_prob_cache[w] = prob

    def get_words_by_length(self, length):
        return self.dict_by_length.get(length, [])

    def get_word_probability(self, word):
        return self.word_prob_cache.get(word, 0)

    def _get_digit_candidates(self, length):
        #获取某长度数字片段候选，带缓存
        if length in self._digit_candidate_cache:
            return self._digit_candidate_cache[length]

        digit_segments = self.grammar.get_digit_segments()
        candidates = []
        for (seg_len, seg) in digit_segments.keys():
            if seg_len == length:
                prob = self.prob_calc.get_digit_segment_probability(length, seg)
                candidates.append((seg, prob))

        candidates.sort(key=lambda x: x[1], reverse=True)
        self._digit_candidate_cache[length] = candidates
        return candidates

    def _get_special_candidates(self, length):
        #获取某长度特殊字符片段候选，带缓存
        if length in self._special_candidate_cache:
            return self._special_candidate_cache[length]

        special_segments = self.grammar.get_special_segments()
        candidates = []
        for (seg_len, seg) in special_segments.keys():
            if seg_len == length:
                prob = self.prob_calc.get_special_segment_probability(length, seg)
                candidates.append((seg, prob))

        candidates.sort(key=lambda x: x[1], reverse=True)
        self._special_candidate_cache[length] = candidates
        return candidates

    def _create_initial_pre_terminals(self, top_k=200):
        initial_items = []
        base_structures = self.grammar.get_base_structures()

        for structure in base_structures.keys():
            struct_prob = self.prob_calc.get_structure_probability(structure)
            if struct_prob <= 0:
                continue

            digit_cands_list = []
            special_cands_list = []

            for i, (seg_type, seg_len) in enumerate(structure):
                if seg_type == 'D':
                    cands = self._get_digit_candidates(seg_len)[:top_k]
                    if cands:
                        digit_cands_list.append((i, cands))
                elif seg_type == 'S':
                    cands = self._get_special_candidates(seg_len)[:top_k]
                    if cands:
                        special_cands_list.append((i, cands))

            if not digit_cands_list and not special_cands_list:
                pre_term = PreTerminal(
                    base_structure=structure,
                    digit_parts={},
                    special_parts={},
                    probability=struct_prob,
                    pivot=(0, 0),
                )
                initial_items.append(pre_term)
                continue

            combined_candidates = [(dict(), dict(), struct_prob)]

            for idx, cands in digit_cands_list:
                new_combined = []
                for digit_parts, special_parts, p in combined_candidates:
                    for seg, seg_p in cands:
                        new_dp = digit_parts.copy()
                        new_dp[idx] = seg
                        new_combined.append((new_dp, special_parts, p * seg_p))
                new_combined.sort(key=lambda x: x[2], reverse=True)
                combined_candidates = new_combined[:50000]

            for idx, cands in special_cands_list:
                new_combined = []
                for digit_parts, special_parts, p in combined_candidates:
                    for seg, seg_p in cands:
                        new_sp = special_parts.copy()
                        new_sp[idx] = seg
                        new_combined.append((digit_parts, new_sp, p * seg_p))
                new_combined.sort(key=lambda x: x[2], reverse=True)
                combined_candidates = new_combined[:50000]

            for digit_parts, special_parts, p in combined_candidates:
                pre_term = PreTerminal(
                    base_structure=structure,
                    digit_parts=digit_parts,
                    special_parts=special_parts,
                    probability=p,
                    pivot=(0, 0),
                )
                initial_items.append(pre_term)

        return initial_items

    def _next_function(self, pre_term):
        next_items = []
        pivot_pos, pivot_idx = pre_term.pivot
        structure = pre_term.base_structure

        for i in range(pivot_pos, len(structure)):
            seg_type, seg_len = structure[i]
            if seg_type == 'L':
                continue

            if seg_type == 'D':
                candidates = self._get_digit_candidates(seg_len)
                current_seg = pre_term.digit_parts.get(i, None)
            elif seg_type == 'S':
                candidates = self._get_special_candidates(seg_len)
                current_seg = pre_term.special_parts.get(i, None)
            else:
                continue

            if not candidates:
                continue

            start_idx = pivot_idx if i == pivot_pos else 0

            current_idx = None
            if current_seg is not None:
                for ci, (cs, _) in enumerate(candidates):
                    if cs == current_seg:
                        current_idx = ci
                        break

            next_idx = max(start_idx, (current_idx + 1) if current_idx is not None else start_idx)

            if next_idx < len(candidates):
                seg, seg_prob = candidates[next_idx]

                old_prob = 1.0
                if current_seg is not None:
                    if seg_type == 'D':
                        old_prob = self.prob_calc.get_digit_segment_probability(len(current_seg), current_seg)
                    elif seg_type == 'S':
                        old_prob = self.prob_calc.get_special_segment_probability(len(current_seg), current_seg)

                new_prob = pre_term.probability / old_prob * seg_prob if old_prob > 0 else 0

                new_digit_parts = pre_term.digit_parts.copy()
                new_special_parts = pre_term.special_parts.copy()

                if seg_type == 'D':
                    new_digit_parts[i] = seg
                else:
                    new_special_parts[i] = seg

                new_pre_term = PreTerminal(
                    base_structure=structure,
                    digit_parts=new_digit_parts,
                    special_parts=new_special_parts,
                    probability=new_prob,
                    pivot=(i, next_idx + 1),
                )
                next_items.append(new_pre_term)

        return next_items

    def _create_initial_terminals(self, pre_term):
        reprs = pre_term.get_representation()

        letter_slots = []
        for i, (seg_type, seg_val) in enumerate(reprs):
            if seg_type == 'L':
                words = self.get_words_by_length(seg_val)
                if not words:
                    return []
                letter_slots.append((i, words))

        if not letter_slots:
            terminal = Terminal(
                pre_term=pre_term,
                letter_parts={},
                probability=pre_term.probability,
                pivot=(0, 0),
            )
            return [terminal]

        first_letter_parts = {}
        prob = pre_term.probability
        for i, words in letter_slots:
            first_letter_parts[i] = words[0]
            prob *= self.get_word_probability(words[0])

        terminal = Terminal(
            pre_term=pre_term,
            letter_parts=first_letter_parts,
            probability=prob,
            pivot=(0, 0),
        )
        return [terminal]

    def _next_terminal(self, terminal):
        next_items = []
        pivot_pos, pivot_idx = terminal.pivot
        bs = terminal.pre_term.base_structure

        for i in range(pivot_pos, len(bs)):
            seg_type, seg_len = bs[i]
            if seg_type != 'L':
                continue

            words = self.get_words_by_length(seg_len)
            if not words:
                continue

            start_idx = pivot_idx if i == pivot_pos else 0

            for idx in range(start_idx, len(words)):
                word = words[idx]
                word_prob = self.get_word_probability(word)

                old_word = terminal.letter_parts.get(i, None)
                old_prob = self.get_word_probability(old_word) if old_word is not None else 1.0

                new_prob = terminal.probability / old_prob * word_prob

                new_letter_parts = terminal.letter_parts.copy()
                new_letter_parts[i] = word

                new_terminal = Terminal(
                    pre_term=terminal.pre_term,
                    letter_parts=new_letter_parts,
                    probability=new_prob,
                    pivot=(i, idx + 1),
                )
                next_items.append(new_terminal)

            if next_items:
                break

        return next_items

    def generate_passwords(self, max_passwords=100):
        import time
        pre_term_heap = []
        terminal_heap = []

        print("正在初始化预终结结构...")
        for pt in self._create_initial_pre_terminals(top_k=200):
            heapq.heappush(pre_term_heap, pt)
        print(f"初始预终结结构数量: {len(pre_term_heap)}")

        passwords = []
        seen = set()
        start_time = time.time()
        last_report_time = start_time

        while (pre_term_heap or terminal_heap) and len(passwords) < max_passwords:
            top_term = terminal_heap[0] if terminal_heap else None
            top_pre = pre_term_heap[0] if pre_term_heap else None

            if top_term and (not top_pre or top_term.probability >= top_pre.probability):
                terminal = heapq.heappop(terminal_heap)
                if terminal.is_complete():
                    pwd = terminal.get_password()
                    if pwd not in seen:
                        seen.add(pwd)
                        passwords.append((pwd, terminal.probability))

                        now = time.time()
                        if now - last_report_time >= 2.0:
                            elapsed = now - start_time
                            speed = len(passwords) / elapsed if elapsed > 0 else 0
                            progress = len(passwords) / max_passwords * 100
                            print(f"\r[进度] {progress:.1f}% | 已生成: {len(passwords):,} / {max_passwords:,} | "
                                  f"速度: {speed:.0f} 个/秒 | 队列: {len(pre_term_heap)+len(terminal_heap):,}", end='')
                            last_report_time = now
                else:
                    next_terms = self._next_terminal(terminal)
                    for t in next_terms:
                        heapq.heappush(terminal_heap, t)
            else:
                pre_term = heapq.heappop(pre_term_heap)
                if pre_term.is_complete():
                    terminals = self._create_initial_terminals(pre_term)
                    for t in terminals:
                        heapq.heappush(terminal_heap, t)
                else:
                    next_pre_terms = self._next_function(pre_term)
                    for pt in next_pre_terms:
                        heapq.heappush(pre_term_heap, pt)

        elapsed = time.time() - start_time
        print(f"\n生成完成: 共 {len(passwords):,} 个密码, 耗时 {elapsed:.1f} 秒")
        return passwords[:max_passwords]

    def generate_candidates(self, max_candidates=100000):
        return self.generate_passwords(max_passwords=max_candidates)
