"""生成测试用 PDF"""
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Helvetica", size=12)

contents = [
    "Beijing is the capital of China. It has the Forbidden City and the Great Wall.",
    "Shanghai is the economic center of China, with the Bund and Oriental Pearl Tower.",
    "Chengdu is famous for giant pandas and spicy hotpot cuisine.",
    "Shenzhen is the tech hub of China, home to Tencent and Huawei.",
    "Hangzhou is known for the beautiful West Lake and Alibaba Group.",
    "Guangzhou is a major trading port, famous for Cantonese food.",
]

for line in contents:
    pdf.write(12, line + "\n")

pdf.output("test.pdf")
print("Done! test.pdf 已生成")
