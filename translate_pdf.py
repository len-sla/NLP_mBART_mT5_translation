import os
import shutil
import fitz
import requests
from PyPDF2 import PdfReader

def extract_text_and_split_sentences(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    sentences = text.replace('\n', ' ').split('. ')
    return sentences

def translate_sentence(sentence, src_lang, tgt_lang, server_url, endpoint):
    url = f"{server_url}/{endpoint}"
    params = {
        "inputs": sentence,
        "src_lang": src_lang,
        "tgt_lang": tgt_lang
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, params=params, headers=headers)
    try:
        translation = response.json()["translation"][0]["translation_text"]
    except KeyError:
        print(f"Error translating sentence: '{sentence}'")
        print(f"Response: {response.json()}")
        raise
    return translation

def main():
    temp_dir = "/tmp/pdf_translator"
    os.makedirs(temp_dir, exist_ok=True)

    # Get the list of PDF files in the mounted directory
    pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]

    if not pdf_files:
        print("No PDF files found in the mounted directory.")
        return

    input_pdf_name = pdf_files[0]
    print(f"Translating PDF file: {input_pdf_name}")

    input_pdf_path = os.path.join(temp_dir, input_pdf_name)

    sentences = extract_text_and_split_sentences(input_pdf_path)

    src_lang = input("Enter the source language code (e.g., en_XX): ")
    tgt_lang = input("Enter the target language code (e.g., de_DE): ")

    server_url = input("Enter the translation server URL (e.g., http://192.168.31.102:7001): ")
    endpoint = input("Enter the translation endpoint (e.g., translate): ")

    translations = []
    with open(os.path.join(temp_dir, f"{os.path.splitext(input_pdf_name)[0]}_{src_lang}_{tgt_lang}.txt"), "w", encoding="utf-8") as source_target_file:
        with open(os.path.join(temp_dir, f"{os.path.splitext(input_pdf_name)[0]}_{tgt_lang}.txt"), "w", encoding="utf-8") as target_file:
            for i, sentence in enumerate(sentences, start=1):
                print(f"Translating sentence: '{sentence}'")
                translation = translate_sentence(sentence, src_lang, tgt_lang, server_url, endpoint)
                translations.append(translation)
                print(translation)  # Print the translation result
                source_target_file.write(f"Source: {sentence}\n")
                source_target_file.write(f"Target: {translation}\n\n")
                target_file.write(f"{translation}\n")
                print(f"Translated {i}/{len(sentences)} sentences.")

if __name__ == "__main__":
    main()
