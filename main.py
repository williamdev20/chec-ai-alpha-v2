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
    
    return paddleOCR_claim


# T2
def tesseract_analyze(img):
    extracted_text = pytesseract.image_to_string(img).lower()
    words = extracted_text.split()
    words_unknow = spell.unknown(words)
    corrected_words = [spell.correction(word) or word if word in words_unknow else word for word in words]
    tesseract_text = " ".join(corrected_words)

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
    is_real = None
    qty_is_fake = 0
    qty_is_real = 0

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
        for claim in data["claims"]:
            reviews = claim["claimReview"]
            if reviews:
                match reviews[0]["textualRating"]:
                    case "Falso":
                        is_real = False
                        qty_is_fake += 1
                    case "Enganoso":
                        is_real = False
                        qty_is_fake += 1
                    case "Verdadeiro":
                        is_real = True
                        qty_is_real += 1
                    # Falta um default aqui pra caso não seja nenhum dos valores listados acima
            else:
                #return "Não foi possível realizar a análise/***DÚVIDA***"
                return None
        
        if qty_is_fake > qty_is_real:
            is_real = False
        else:
            is_real = True
            
        return is_real
    else:
        print("Sem resultados")
        return None




if __name__ == "__main__":
    #print(paddleOCR_analyze(cartaz))
    #print(tesseract_analyze(cartaz))
    #print(getFinalClaim())
    print(google_fact_checking_claim("vacinas da covid realmente funcionam"))
    













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