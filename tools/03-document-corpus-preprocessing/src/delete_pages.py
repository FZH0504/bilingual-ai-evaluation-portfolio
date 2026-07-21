import fitz

# 1. 打开你刚刚裁剪好上下边缘的 PDF
input_pdf = "output.pdf"
final_pdf = "final_ready_for_ocr.pdf"

doc = fitz.open(input_pdf)

# ==========================================
# 🛑 核心设置区：你要从哪一页开始保留？
#
# ⚠️ 警报：Python 的页码是从 0 开始数数的！
# 也就是说，PDF 阅读器里显示的第 1 页，在代码里是 0。
# 阅读器里的第 15 页，在代码里是 14。
# ==========================================

# 假设正文是从 PDF 阅读器里显示的第 15 页开始的
# 那么这里就填 14。这代表：删掉 0 到 13 页，从 14 页一直保留到最后。
start_page_index = 14

# 获取这本书的总页数
total_pages = len(doc)

# 2. 核心操作：只“框选”并保留从 start_page_index 到最后一页的内容
doc.select(range(start_page_index, total_pages))

# 3. 另存为最终纯净版
doc.save(final_pdf)
doc.close()

print(f"🎉 搞定！前面的废话已经砍掉了，最终用来做 OCR 的 '{final_pdf}' 已生成！")