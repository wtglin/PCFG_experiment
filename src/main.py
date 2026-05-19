import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from grammar import PCFGGrammar
from probability import ProbabilityCalculator
from generator import PasswordGenerator
from utils import load_password_records, load_dictionary_words


def evaluate_from_candidates(candidate_passwords, test_passwords):
    target_set = set(test_passwords)
    total_targets = len(target_set)
    cracked = set()
    milestones = [1000, 10000, 100000, 500000, 1000000, 5000000, 10000000]
    milestone_results = []

    for i, (pwd, _prob) in enumerate(candidate_passwords, 1):
        if pwd in target_set:
            cracked.add(pwd)
        if i in milestones or i == len(candidate_passwords):
            rate = len(cracked) / total_targets if total_targets > 0 else 0
            milestone_results.append((i, len(cracked), rate))

    return cracked, milestone_results


def main():
    parser = argparse.ArgumentParser(description='PCFG密码猜测实验')
    parser.add_argument('--max-guesses', type=int, default=10000000)
    parser.add_argument('--top-n', type=int, default=20)
    args = parser.parse_args()
    project_root = Path(__file__).parent.parent

    train_file = project_root / 'data' / 'training' / 'myspace_train.txt'
    test_file = project_root / 'data' / 'test' / 'myspace_test.txt'
    dict_file = project_root / 'data' / 'raw' / 'dic-0294.txt'

    if not train_file.exists():
        print("训练文件不存在", train_file)
        return

    if not test_file.exists():
        print("测试文件不存在", test_file)
        return

    train_records = load_password_records(str(train_file))
    test_records = load_password_records(str(test_file))

    train_passwords = [pwd for pwd, _ in train_records]
    test_passwords = [pwd for pwd, _ in test_records]

    print(f"训练集数量: {len(train_passwords)}")
    print(f"测试集数量: {len(test_passwords)}")

    dictionary = []
    if dict_file.exists():
        dictionary = load_dictionary_words(str(dict_file), lowercase=True)
        print(f"字典词数量: {len(dictionary)}")
    else:
        print("未使用字典文件")

    grammar = PCFGGrammar()
    grammar.learn_from_corpus(train_passwords)

    print(f"基础结构数量: {len(grammar.get_base_structures())}")
    print(f"数字片段数量: {len(grammar.get_digit_segments())}")
    print(f"特殊字符片段数量: {len(grammar.get_special_segments())}")

    prob_calc = ProbabilityCalculator(grammar)

    print("\n========== 生成候选密码 ==========")
    generator = PasswordGenerator(grammar, prob_calc, dictionary=dictionary)
    candidate_passwords = generator.generate_passwords(
        max_passwords=args.max_guesses
    )

    print(f"\n生成候选密码数量: {len(candidate_passwords):,}")
    print(f"\n概率最高的前 {args.top_n} 个密码：")
    for i, (pwd, prob) in enumerate(candidate_passwords[:args.top_n], 1):
        print(f"  {i:2d}. {pwd:<20s} {prob:.6e}")

    print("\n========== 评估猜测成功率 ==========")
    cracked, milestone_results = evaluate_from_candidates(candidate_passwords, test_passwords)

    print(f"\n{'猜测次数':<12} {'破解数':<10} {'成功率':<10}")
    print("-" * 35)
    for guesses, count, rate in milestone_results:
        print(f"{guesses:<12,} {count:<10} {rate:<10.4%}")

    print(f"\n最终结果: 猜测 {len(candidate_passwords):,} 次, "
          f"破解 {len(cracked)} 个密码, "
          f"成功率 {len(cracked)/len(set(test_passwords)):.4%}")

    print("\n实验结束")


if __name__ == '__main__':
    main()
