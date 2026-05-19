# 主程序入口 - PCFG 密码破解系统
# 基于 Weir 等人论文的 PCFG 生成流程
#
# 流程：
# 1. 读取训练集和测试集
# 2. 读取字典
# 3. 学习 PCFG 文法
# 4. 计算概率
# 5. 生成候选密码
# 6. 评估猜测成功率

import argparse
import sys
from pathlib import Path

# 添加 src 目录到系统路径
sys.path.insert(0, str(Path(__file__).parent))

from grammar import PCFGGrammar
from probability import ProbabilityCalculator
from generator import PasswordGenerator
from evaluator import PasswordEvaluator
from utils import load_password_records,load_dictionary_words


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
    
    # 读取数据
    train_records = load_password_records(str(train_file))
    test_records = load_password_records(str(test_file))

    train_passwords = [pwd for pwd, _ in train_records]
    test_passwords = [pwd for pwd, _ in test_records]

    print("训练集数量:", len(train_passwords))
    print("测试集数量:", len(test_passwords))

    # 读取字典
    dictionary = []
    if dict_file.exists():
        dictionary = load_dictionary_words(str(dict_file), lowercase=True)
        print("字典词数量:", len(dictionary))
    else:
        print("未使用字典文件")

    # 训练 PCFG
    grammar = PCFGGrammar()
    grammar.learn_from_corpus(train_passwords)

    print("基础结构数量:", len(grammar.get_base_structures()))
    print("数字片段数量:", len(grammar.get_digit_segments()))
    print("特殊字符片段数量:", len(grammar.get_special_segments()))
    # 计算概率
    prob_calc = ProbabilityCalculator(grammar)
    # 生成候选密码
    print("\n生成候选密码")
    generator = PasswordGenerator(grammar, prob_calc, dictionary=dictionary)
    candidate_passwords = generator.generate_passwords(
        max_passwords=args.max_guesses
    )

    print("生成候选密码数量:", len(candidate_passwords))
    print(f"\n概率最高的前 {args.top_n} 个密码：")
    for i, (pwd, prob) in enumerate(candidate_passwords[:args.top_n], 1):
        print(f"{i}. {pwd}  {prob:.6e}")

    # 评估猜测成功率
    evaluator = PasswordEvaluator(generator)
    result = evaluator.evaluate_guessing_success(
        target_passwords=set(test_passwords),
        max_guesses=args.max_guesses
    )

    evaluator.print_evaluation_report(result)

    print("\n实验结束")


if __name__ == '__main__':
    main()
