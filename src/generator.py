import heapq
from collections import defaultdict


class PreTerminal:
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
    def __init__(self, grammar, prob_calc, dictionary=None, train_passwords=None):
        self.grammar = grammar
        self.prob_calc = prob_calc
        self.dictionary = dictionary or []
        self.train_passwords = train_passwords or []

        self.dict_by_length = defaultdict(list)
        self.word_prob_cache = {}

        self._digit_candidate_cache = {}
        self._special_candidate_cache = {}
        self._letter_candidate_cache = {}
        self._base_structure_cache = None

        self._build_letter_index()

    def _build_letter_index(self):
        from collections import Counter

        train_words_by_length = defaultdict(Counter)
        for pwd in self.train_passwords:
            segments = self.grammar.split_into_segments(pwd)
            for seg_type, seg_content in segments:
                if seg_type == 'L':
                    train_words_by_length[len(seg_content)][seg_content.lower()] += 1

        dict_words_by_length = defaultdict(set)
        for word in self.dictionary:
            w = word.lower()
            dict_words_by_length[len(w)].add(w)

        all_lengths = set(list(train_words_by_length.keys()) + list(dict_words_by_length.keys()))

        for length in all_lengths:
            train_counter = train_words_by_length.get(length, Counter())
            dict_words = dict_words_by_length.get(length, set())

            total_train_count = sum(train_counter.values())

            all_words = []

            if total_train_count > 0:
                alpha = 0.95
                for w, count in train_counter.most_common():
                    prob = alpha * (count / total_train_count)
                    all_words.append((w, prob))

                unseen_dict_words = dict_words - set(train_counter.keys())
                if unseen_dict_words:
                    remaining_prob = (1.0 - alpha)
                    per_word_prob = remaining_prob / len(unseen_dict_words)
                    for w in sorted(unseen_dict_words):
                        all_words.append((w, per_word_prob))
            else:
                if dict_words:
                    prob = 1.0 / len(dict_words)
                    for w in dict_words:
                        all_words.append((w, prob))

            all_words.sort(key=lambda x: x[1], reverse=True)
            self.dict_by_length[length] = all_words

            for w, p in all_words:
                self.word_prob_cache[w] = p

    def get_words_by_length(self, length):
        return self.dict_by_length.get(length, [])

    def get_word_probability(self, word):
        return self.word_prob_cache.get(word, 0)

    def _get_digit_candidates(self, length):
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

    def _create_initial_pre_terminals(self, top_k=50):
        initial_items = []
        base_structures = self.grammar.get_base_structures()

        for structure, count in base_structures.items():
            if count < 2:
                continue
            if len(structure) > 6:
                continue

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
                combined_candidates = new_combined[:5000]

            for idx, cands in special_cands_list:
                new_combined = []
                for digit_parts, special_parts, p in combined_candidates:
                    for seg, seg_p in cands:
                        new_sp = special_parts.copy()
                        new_sp[idx] = seg
                        new_combined.append((digit_parts, new_sp, p * seg_p))
                new_combined.sort(key=lambda x: x[2], reverse=True)
                combined_candidates = new_combined[:5000]

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

    def _create_initial_terminals(self, pre_term, max_terminals=500):
        import itertools
        reprs = pre_term.get_representation()

        letter_slots = []
        for i, (seg_type, seg_val) in enumerate(reprs):
            if seg_type == 'L':
                words = self.get_words_by_length(seg_val)
                if not words:
                    return []
                letter_slots.append((i, words[:max_terminals]))

        if not letter_slots:
            terminal = Terminal(
                pre_term=pre_term,
                letter_parts={},
                probability=pre_term.probability,
                pivot=(0, 0),
            )
            return [terminal]

        if len(letter_slots) == 1:
            i, words = letter_slots[0]
            terminals = []
            for word, word_prob in words:
                letter_parts = {i: word}
                prob = pre_term.probability * word_prob
                t = Terminal(pre_term=pre_term, letter_parts=letter_parts,
                           probability=prob, pivot=(0, 0))
                terminals.append(t)
            return terminals

        slot_indices = [range(min(len(words), max_terminals)) for _, words in letter_slots]
        terminals = []
        for combo in itertools.product(*slot_indices):
            letter_parts = {}
            prob = pre_term.probability
            for slot_idx, word_idx in enumerate(combo):
                i, words = letter_slots[slot_idx]
                word, word_prob = words[word_idx]
                letter_parts[i] = word
                prob *= word_prob
            t = Terminal(pre_term=pre_term, letter_parts=letter_parts,
                        probability=prob, pivot=(0, 0))
            terminals.append(t)
            if len(terminals) >= max_terminals:
                break
        return terminals

    def _next_terminal(self, terminal):
        return []

    def generate_passwords(self, max_passwords=100):
        import time
        pre_term_heap = []
        terminal_heap = []

        print("正在初始化预终结结构...")
        for pt in self._create_initial_pre_terminals(top_k=50):
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
