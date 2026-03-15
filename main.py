from paddleocr import PaddleOCR
#import spacy
from spellchecker import SpellChecker
#import pytextrank

ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
#nlp = spacy.load("pt_core_news_sm")
#nlp.add_pipe("textrank")
spell = SpellChecker(language="pt")


def ocr_analyze():
    result = ocr.ocr("assets/fake-news-cartaz.png")
    extracted_text = " ".join([word[1][0] for line in result for word in line]).lower()
    #doc = nlp(extracted_text) #type: ignore

    words = extracted_text.split()
    words_unknow = spell.unknown(words)
    corrected_words = [spell.correction(word) or word if word in words_unknow else word for word in words]
    claim = " ".join(corrected_words)
    


    print(claim)


if __name__ == "__main__":
    ocr_analyze()













"""
ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
nlp = spacy.load("pt_core_news_sm")
nlp.add_pipe("textrank")
spell = SpellChecker(language="pt")


def ocr_analyze():
    result = ocr.ocr("assets/cartaz-dengue.jpeg")
    extracted_text = " ".join([word[1][0] for line in result for word in line]).lower()
    words = extracted_text.split()
    words_unknow = spell.unknown(words)
    corrected_words = [spell.correction(word) or word if word in words_unknow else word for word in words]
    corrected_text = " ".join(corrected_words)
    
    doc = nlp(corrected_text) #type: ignore
    claim = next(doc._.textrank.summary(limit_sentences=1))

    print(extracted_text)
"""