from paddleocr import PaddleOCR
from spellchecker import SpellChecker
import pytesseract
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
#from sentence_transformers import SentenceTransformer # Ta dando erro no import pq precisa do Pytorch em uma versão e eu to em uma desatualizada

load_dotenv()

ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
spell = SpellChecker(language="pt")
#model = SentenceTransformer("all-MiniLM-L6-v2")

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



"""
def get_paddleOCR_embedding(text):
    sentence = text
    embedding = model.encode(sentence)

    return embedding.shape
""" 



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



def search_on_web(query):
    url = "https://google.serper.dev/search"

    payload = {
        "q": query,
        "hl": "pt",
        "num": 10
    }

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }

    headers_scrapping = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    response = requests.request("POST", url, headers=headers, json=payload) # Quando chegar em casa tirar esse 'verify' pra ver se funciona no Linux
    
    if response.status_code != 200:
        print("[ERROR]: Houve erro na requisição da API: ", response.status_code)


    data = response.json()

    # Pegar os links #
    source_links = []
    scrapping_paragraphs = []

    if data["organic"]:
        for result in data["organic"]:
            #print(result["link"])
            source_links.append(result["link"])


    #print(source_links)
    #print(json.dumps(data, indent=2, ensure_ascii=False))


    # Scrapping #
    for url in source_links:
        print("================================= URL =================================")
        try:
            html = requests.get(url, headers=headers_scrapping, timeout=10, verify=False)
            soup = BeautifulSoup(html.text, "html.parser")

            if html.status_code != 200:
                #print(f"[ERROR] Houve um erro ao acessar o site de scrapping: {html.status_code}\n URL negada: {url}")
                continue

            paragraphs = soup.find_all("p")
            
            for paragraph in paragraphs:
                print(paragraph.get_text(strip=True))
                scrapping_paragraphs.append(paragraph.get_text(strip=True))

        except Exception as e:
            print(f"[ERROR]: Houve um erro no scrapping: {e}")


    


if __name__ == "__main__":
    #print(paddleOCR_analyze(cartaz))
    #print(tesseract_analyze(cartaz))
    #print(getFinalClaim())

    #print(google_fact_checking_claim(getFinalClaim()))
    search_on_web(getFinalClaim())
    #print(get_paddleOCR_embedding(paddleOCR_analyze(cartaz)))














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