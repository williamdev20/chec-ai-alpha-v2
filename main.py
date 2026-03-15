from paddleocr import PaddleOCR
from spellchecker import SpellChecker
import pytesseract
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
spell = SpellChecker(language="pt")

cartaz = "assets/fake-news-cartaz.png"

# T1
def paddleOCR_analyze(img):
    result = ocr.ocr(img)
    extracted_text = " ".join([word[1][0] for line in result for word in line]).lower()

    words = extracted_text.split()
    words_unknow = spell.unknown(words)
    corrected_words = [spell.correction(word) or word if word in words_unknow else word for word in words]
    paddleOCR_claim = " ".join(corrected_words)
    
    #print("PaddleOCR Result:", paddleOCR_claim)
    return paddleOCR_claim


# T2
def tesseract_analyze(img):
    extracted_text = pytesseract.image_to_string(img).lower()
    words = extracted_text.split()
    words_unknow = spell.unknown(words)
    corrected_words = [spell.correction(word) or word if word in words_unknow else word for word in words]
    tesseract_text = " ".join(corrected_words)

    #print("Tesseract OCR Result:", tesseract_text)
    return tesseract_text
    




def check_claim_with_more_correct_words(text):
    words = text.split()
    unknow_word = spell.unknown(words)

    return len(unknow_word)


def getFinalClaim():
    paddle_claim = paddleOCR_analyze(cartaz)
    tesseract_claim = tesseract_analyze(cartaz)
    final_claim = ""

    if check_claim_with_more_correct_words(paddle_claim) < check_claim_with_more_correct_words(tesseract_claim):
        final_claim = paddle_claim
    else:
        final_claim = tesseract_claim

    return final_claim




def google_fact_checking_claim(query):
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    params = {
        "query": query,
        "languageCode": "pt",
        "key": os.getenv("API_KEY")
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("[ERROR]: Houve um erro na requisição: ", response.status_code)
        return
    
    data = response.json()

    if "claims" in data and data["claims"]:
        """
        for claim in data["claims"]:
            reviews = claim["claimReview"]
            if reviews:
                print(reviews[0]["textualRating"])

                # Bota um switch case aqui pra ver se é 'Enganoso', 'Verdadeiro', 'Falso', etc
            else:
                return False
                """
        print(data)
    else:
        print("Sem resultados!")


if __name__ == "__main__":
    #print(paddleOCR_analyze(cartaz))
    #print(tesseract_analyze(cartaz))
    print(getFinalClaim())
    google_fact_checking_claim(getFinalClaim())
    













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