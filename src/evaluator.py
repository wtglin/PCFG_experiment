from typing import List, Set, Dict
import time


class PasswordEvaluator:
    def __init__(self, generator):
        self.generator = generator

    def evaluate_guessing_success(self, target_passwords, max_guesses=10000000):
        cracked = set()
        guess_count = 0

        for pwd, prob in self.generator.generate_candidates(max_candidates=max_guesses):
            guess_count += 1

            if isinstance(target_passwords, dict):
                if pwd in target_passwords:
                    cracked.add(pwd)
            else:
                if pwd in target_passwords:
                    cracked.add(pwd)

            if guess_count >= max_guesses:
                break

        success_count = len(cracked)
        total_targets = len(target_passwords) if not isinstance(target_passwords, dict) else sum(target_passwords.values())
        success_rate = success_count / total_targets if total_targets > 0 else 0

        return {
            'guess_count': guess_count,
            'success_count': success_count,
            'success_rate': success_rate,
        }

    def print_evaluation_report(self, result):
        print(f"猜测总次数: {result['guess_count']}")
        print(f"成功破解密码数: {result['success_count']}")
        print(f"成功率: {result['success_rate']:.4%}")
