import re
from nltk.tokenize import sent_tokenize, word_tokenize

def split_text_into_paragraphs(text):
    return text.split('\n')

def split_paragraphs_into_sentences(paragraphs, language):
    paragraphs_sentences = []
    for paragraph in paragraphs:
        sentences = sent_tokenize(paragraph, language=language)
        paragraphs_sentences.append(sentences)
    return paragraphs_sentences

def concat_sentences(sentences, max_words=80):
    concatenated_sentences = []
    current_concat = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(word_tokenize(sentence))
        if current_word_count + sentence_word_count <= max_words:
            current_concat.append(sentence)
            current_word_count += sentence_word_count
        else:
            concatenated_sentences.append(' '.join(current_concat))
            current_concat = [sentence]
            current_word_count = sentence_word_count

    if current_concat:
        concatenated_sentences.append(' '.join(current_concat))
    concatenated_sentences = [sentence for sentence in concatenated_sentences if sentence]
    return concatenated_sentences

def process_text(text, language):
    paragraphs = split_text_into_paragraphs(text)
    paragraphs_sentences = split_paragraphs_into_sentences(paragraphs, language=language)
    all_concatenated_sentences = []

    for sentences in paragraphs_sentences:
        concatenated_sentences = concat_sentences(sentences)
        all_concatenated_sentences.append(concatenated_sentences)

    return all_concatenated_sentences



def text_translate(input_texts, source_lang, pipeline=None):
    """
    Splits the input text into sentences and creates batches of sentences to be fed into the model.

    Args:
        text (str): The input text to be split into sentences.
        source_lang (str): The language of the input text.
        language_codes (dict): A dictionary mapping language names to their corresponding language codes.
        input_length (int): The maximum number of tokens in a batch.

    Returns:
        A list of lists, where each inner list contains a batch of sentences. Each batch is represented as a list of strings.
    """        

    content = []
    content_urls = []
    content_emails = []
    
    language_codes = {
        "en": "english",
        "de": "german",
        "fr": "french",
        "es": "spanish",
        "it": "italian",
        "nl": "dutch",
        "pl": "polish",
        "pt": "portuguese",
        "tr": "turkish",
        "ru": "russian",
        "ar": "arabic",
        "zh": "chinese",
        "ja": "japanese",
        "ko": "korean",
        "vi": "vietnamese",
        "th": "thai",
        "hi": "hindi",
        "bn": "bengali",
        "ro": "english",
                     }
   
    url_pattern = r"\b(?:https?://|ftp://|www\.)\S+(?:/\S+)?\b"
    email_pattern = r"\b[\w.-]+@[\w.-]+\.\w{2,4}\b"
    output_texts = []
    
    for text in input_texts:
        if source_lang == "zh":
            paragraphs = text.split("\n")
            t = [pipeline([i for i in re.split(r'[。！？]', p)]) if p else "\n" for p in paragraphs]
            # print(t)
            translation_result = "\n".join(["" if i == "\n" else " ".join([t['translation_text'] for t in i]) for i in t ])
            # print("source_lang == zh")  
            return translation_result  
        else:
            urls = re.findall(url_pattern, text)
            emails = re.findall(email_pattern, text)
            if urls: text = re.sub(url_pattern, "<URL>", text)
            if emails: text = re.sub(email_pattern, "<EMAIL>", text)
            translation_result = ["\n".join([" ".join([i["translation_text"] for i in pipeline(paragraph)])\
                if paragraph else "\n" for paragraph in process_text(text,language=language_codes[source_lang])])][0]
            
            for url in urls:
                translation_result = translation_result.replace("<URL>", " "+url, 1)
            for email in emails:
                translation_result = translation_result.replace("<EMAIL>", " "+email, 1)
        output_texts.append(translation_result)
    return output_texts