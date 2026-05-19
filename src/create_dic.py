from pathlib import Path

# English 文件夹路径
folder_path = Path("english")

# 输出文件名
output_file = Path("english.txt")

# 检查文件夹是否存在
if not folder_path.exists() or not folder_path.is_dir():
    print(f"文件夹不存在: {folder_path}")
else:
    # 获取所有文件名（不包含子文件夹）
    words = [file.name for file in folder_path.iterdir() if file.is_file()]

    # 可选：排序
    words.sort()

    # 写入 txt 文件
    with output_file.open("w", encoding="utf-8") as f:
        for word in words:
            f.write(word + "\n")

    print(f"已成功生成文件: {output_file}")
    print(f"共写入 {len(words)} 个单词")