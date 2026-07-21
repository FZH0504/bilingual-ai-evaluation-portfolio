import re

input_txt = "飘_终极语料库.txt"
output_txt = "飘_纯净版_分词预备.txt"

with open(input_txt, "r", encoding="utf-8") as f:
    lines = f.readlines()

clean_lines = []
for line in lines:
    text = line.strip()

    if not text:
        continue

    # ==========================================
    # 🛑 章节粉碎机（根据你的需求决定是否保留这行代码）
    # 这个正则会精准识别“第一章”、“第12章”、“第一部”等格式
    # ==========================================
    if re.match(r'^第\s*[一二三四五六七八九十百零0-9]+\s*[章节部]', text):
        continue  # 如果不需要章节号，就直接跳过（扔掉）这一行

    clean_lines.append(text)

# 把所有留下来的干净行拼成一个超级长文本，准备深度清洗
full_text = "\n".join(clean_lines)

print("正在执行深度正则清洗魔法...")

# 滤芯 1：消灭乱码符号 (黑方块、多余下划线等)
full_text = re.sub(r'[■\*◆●_]+', '', full_text)

# 滤芯 2：拯救中英文标点大混战
full_text = re.sub(r'\.{3,}', '……', full_text)
punctuation_map = {',': '，', '.': '。', '?': '？', '!': '！', ':': '：', ';': '；', '(': '（', ')': '）'}
for eng_punc, chn_punc in punctuation_map.items():
    full_text = full_text.replace(eng_punc, chn_punc)

# 滤芯 3：消灭中文之间的“迷之空格”
full_text = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', full_text)

# 滤芯 4：缝合“碎尸万段”的断行
# 把 OCR 错误的回车换行重新拼回完整的长句子
full_text = re.sub(r'([^。！？…”’）\]])\n', r'\1', full_text)

# 滤芯 5：清理多余的连环空行
full_text = re.sub(r'\n{2,}', '\n', full_text)

# 写入最终的 txt 文件
with open(output_txt, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"🎉 史诗级清洗完成！干干净净的《{output_txt}》已经诞生！")