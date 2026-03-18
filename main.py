from paddleocr import PaddleOCR
from spellchecker import SpellChecker
import pytesseract
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from groq import Groq

load_dotenv()

ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)
spell = SpellChecker(language="pt")
model = SentenceTransformer("all-MiniLM-L6-v2")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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




def get_final_claim_embedding(text):
    sentence = text
    embedding = model.encode(sentence)

    return embedding




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
                        #is_real = False
                        qty_is_fake += 1
                    case "Enganoso":
                        #is_real = False
                        qty_is_fake += 1
                    case "Verdadeiro":
                        #is_real = True
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
        print("PASSOU PELO GOOGLE FACT CHECK")
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
        #print("================================= URL =================================")
        try:
            html = requests.get(url, headers=headers_scrapping, timeout=10, verify=False)
            soup = BeautifulSoup(html.text, "html.parser")

            if html.status_code != 200:
                #print(f"[ERROR] Houve um erro ao acessar o site de scrapping: {html.status_code}\n URL negada: {url}")
                continue

            paragraphs = soup.find_all("p")
            
            for paragraph in paragraphs:
                #print(paragraph.get_text(strip=True))
                scrapping_paragraphs.append(paragraph.get_text(strip=True))

        except Exception as e:
            print(f"[ERROR]: Houve um erro no scrapping: {e}")

    print("PASSOU PELO SCRAPPING")
    return scrapping_paragraphs

    
def get_scrapping_paragraphs_embedding(paragraphs: list[str]):
    sentences = []
    for paragraph in paragraphs:
        sentences.append(paragraph)

    paragraphs_embedding = model.encode(sentences)

    return paragraphs_embedding


def check_poster_with_cosine_similarity(query_embedding, paragraphs_embedding, paragraphs: list[str]):
    similarities = model.similarity(query_embedding, paragraphs_embedding)
    # Botar um metodo max aqui pra pegar o valor mais alto dessa lista acima. Daí eu faço um if pra ver se o resultado é confiavel, falso ou se precisa mandar pra IA com base no score do resultado do 'max' no vetor da similaridade de cosseno
    score = similarities.max().item()
    top_paragraph_index = int(similarities.argmax().item())
    top_paragraph = paragraphs[top_paragraph_index]

    if score >= 0.85:
        return True
    elif score >= 0.30:
        return False
    else:
        return {"paragraph": top_paragraph}



def check_with_agent(query, top_paragraph):
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "Você é um agente de IA responsável por checar a veracidade de uma informação retirada de um cartaz para saber se ela se trata de uma fake news ou não. Você receberá uma query (texto/pergunta) e um parágrafo com instrução. Você deve analisar essa query e o parágrafo que foi fornecido e verificar se é uma fake news ou não. Para a confirmação das informações fornecidas, você não deve verificar apenas se o parágrafo concorda com a query, mas sim verificar se a informação do parágrafo é um fato real baseado em conhecimento científico. Se o parágrafo contiver informação falsa, pseudociência ou desinformação, retorne 'FALSE'. Mesmo que o parágrafo concorde com a query, se ambos estiverem errados, retorne 'FALSE'. Só retorne 'TRUE' se a informação for comprovadamente verdadeira. Você dever retornar apenas, e somente apenas, 'TRUE' ou 'FALSE'"
            },
            {
                "role": "user",
                "content":
                f"""
                    Query: {query}. Parágrafo: {top_paragraph}

                    Pergunta:
                    O parágrafo responde corretamente a query com base no mundo real e em conhecimento científico e conhecimento confiável? É preciso que a informação seja cientificamente correta, e não verificar apenas a semelhança semântica da query e o parágrafo.

                """
            }
        ],
        temperature=0,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None
    )

    print("PASSOU PELO AGENTE")
    return completion.choices[0].message.content


def check_poster():
    claim = getFinalClaim()

    google_check_result = google_fact_checking_claim(claim)

    if google_check_result is None:
        claim_embedding = get_final_claim_embedding(claim)
        paragraphs = search_on_web(claim)
        paragraph_embedding = get_scrapping_paragraphs_embedding(paragraphs)

        cosine_similarity_result = check_poster_with_cosine_similarity(claim_embedding, paragraph_embedding, paragraphs)

        if isinstance(cosine_similarity_result, dict):
            agent_result = check_with_agent(claim, cosine_similarity_result["paragraph"])

            return agent_result
        else:
            return cosine_similarity_result
    else:
        return google_check_result



if __name__ == "__main__":
    #print(paddleOCR_analyze(cartaz))
    #print(tesseract_analyze(cartaz))
    #print(getFinalClaim())

    #print(google_fact_checking_claim(getFinalClaim()))
    #search_on_web(getFinalClaim())
    #print(get_final_claim_embedding(getFinalClaim()))


    #print(check_poster_with_cosine_similarity(get_final_claim_embedding(getFinalClaim()), get_scrapping_paragraphs_embedding(search_on_web(getFinalClaim()))))
    #check_with_agent(getFinalClaim(), top_paragraph="Chá de erva doce, na verdade, não cura o vírus da dengue")

    print(check_poster())














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