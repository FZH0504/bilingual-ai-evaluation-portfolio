import tkinter as tk
from tkinter import filedialog, messagebox
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import jieba
import numpy as np
from PIL import Image

def generate_word_cloud(text, font_path=None, mask=None):
    """
    生成词云并返回WordCloud对象
    :param text: 输入的文本内容（字符串）
    :param font_path: 字体路径（对于中文文本，需要指定支持中文的字体路径）
    :param mask: 自定义形状的遮罩
    :return: WordCloud对象
    """
    # 如果是中文文本，进行分词
    if "中文" in text or "汉字" in text:
        text = " ".join(jieba.cut(text))

    # 创建WordCloud对象
    wordcloud = WordCloud(
        font_path=font_path,
        width=800,
        height=600,
        background_color="white",
        max_words=200,
        max_font_size=100,
        min_font_size=10,
        random_state=42,
        mask=mask
    ).generate(text)

    return wordcloud

def display_word_cloud(wordcloud):
    """
    显示词云
    :param wordcloud: WordCloud对象
    """
    plt.figure(figsize=(10, 8))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")  # 关闭坐标轴
    plt.show()

def update_word_cloud():
    text = text_entry.get("1.0", tk.END)
    mask = None
    if mask_path:
        mask = np.array(Image.open(mask_path))
    wordcloud = generate_word_cloud(text, font_path, mask)
    display_word_cloud(wordcloud)

def load_text_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
            text_entry.delete("1.0", tk.END)
            text_entry.insert("1.0", text)
            update_word_cloud()

def load_mask_file():
    global mask_path
    mask_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if mask_path:
        messagebox.showinfo("成功", "形状文件已加载")
        update_word_cloud()

def save_word_cloud():
    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if file_path:
        text = text_entry.get("1.0", tk.END)
        mask = None
        if mask_path:
            mask = np.array(Image.open(mask_path))
        wordcloud = generate_word_cloud(text, font_path, mask)
        wordcloud.to_file(file_path)
        messagebox.showinfo("成功", "词云已保存到文件")

# 创建主窗口
root = tk.Tk()
root.title("动态词云生成器")

# 创建文本输入框
text_entry = tk.Text(root, height=10, width=50)
text_entry.pack()

#按钮
update_button = tk.Button(root, text="生成词云", command=update_word_cloud)
update_button.pack()

load_text_button = tk.Button(root, text="加载文本文件", command=load_text_file)
load_text_button.pack()

load_mask_button = tk.Button(root, text="加载形状文件", command=load_mask_file)
load_mask_button.pack()

save_button = tk.Button(root, text="保存词云", command=save_word_cloud)
save_button.pack()

# 字体路径（对于中文文本，需要指定支持中文的字体路径）
font_path = r"C:\Windows\Fonts\simhei.ttf"  # 示例字体路径，根据实际情况修改
mask_path = None

# 运行主循环
root.mainloop()