from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)

result = ocr.ocr("assets/cartaz-dengue.jpeg")
extracted_text = " ".join([word[1][0] for line in result for word in line]).lower()

print(extracted_text)