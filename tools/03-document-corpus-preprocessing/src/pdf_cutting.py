import fitz

doc = fitz.open("input.pdf")

for page in doc:
    # 直接获取页面的绝对物理边界 (MediaBox)
    mb = page.mediabox

    # 计算需要裁掉的具体高度 (上下各裁掉 8%)
    top_cut = mb.height * 0.08
    bottom_cut = mb.height * 0.08

    # 构造新的裁剪区域，严格限制在 MediaBox 的范围内
    new_rect = fitz.Rect(
        mb.x0,
        mb.y0 + top_cut,
        mb.x1,
        mb.y1 - bottom_cut
    )

    # 将新计算的安全区域设置为裁剪框
    page.set_cropbox(new_rect)

doc.save("output.pdf")
doc.close()

# 加了一行提示语，跑完就不会“没反应”了！
print("🎉 恭喜！裁剪处理完成，快去左边看看有没有出现 output.pdf ！")