import fitz
import numpy as np
import cv2
from paddleocr import PaddleOCR

# 2.8.1 经典稳定版初始化（重新启用倾斜校正）
ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)

input_pdf = "final_ready_for_ocr.pdf"  # 你的纯净版 PDF 文件名
output_txt = "飘_终极语料库.txt"

doc = fitz.open(input_pdf)

with open(output_txt, "w", encoding="utf-8") as f:
    for page_num, page in enumerate(doc):
        print(f"🚀 正在狂飙识别第 {page_num + 1} 页 / 共 {len(doc)} 页...")

        # 1. 把 PDF 页面高清截图 (放大2倍)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # 2. 图片格式转换
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        elif pix.n == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        # 3. 经典版识别指令（重新启用 cls=True）
        result = ocr.ocr(img, cls=True)

        # 4. 提取文字并进行过滤
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]

                # 脚注过滤器
                if text.startswith(('①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨')) or "译者注" in text:
                    continue

                f.write(text + "\n")

doc.close()
print(f"🎉 史诗级胜利！整本书已被榨干，《{output_txt}》 已在左侧文件夹生成！")