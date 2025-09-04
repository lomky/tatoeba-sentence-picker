#!/usr/bin/python3
"""Starts a REPL - give a word, get sentences, pick one, repeat. Final output: get hanzi, zhuyin, pinyin, meaning"""

from pathlib import Path
import click
import requests
from dragonmapper import hanzi
from prompt_toolkit import prompt, choice

from prompt_toolkit.shortcuts import choice
from prompt_toolkit.filters import is_done
from prompt_toolkit.styles import Style

STYLE = Style.from_dict(
    {
        "frame.border": "#884444",
        "selected-option": "bold",
    }
)

class Tatoeba:
    def __init__(self, word):
        self.word = word
        self.has_result = False
        self.index = 0
        self.sentences = []

    def call(self):
        query = f'https://tatoeba.org/en/api_v0/search?from=cmn&has_audio=&list=&native=yes&original=&orphans=no&query={self.word}&sort=relevance&sort_reverse=&tags=&to=eng&trans_filter=limit&trans_has_audio=&trans_link=&trans_orphan=no&trans_to=&trans_unapproved=no&trans_user=&unapproved=no&user=&word_count_max=&word_count_min=6'
        r = requests.get(query)
        response = r.json()
        self.raw_results = response["results"]
        if len(self.raw_results) > 0:
            self.has_result = True

    def populate_sentences(self):
        for result in self.raw_results:
            meaning = self.get_translation(result["translations"])
            sentence = self.get_traditional_sentence(result)
            author = result["user"]["username"]
            cc = result["license"]
            if len(sentence) == 0 or len(meaning) == 0:
                continue
            self.sentences.append(TatoebaSentence(self.word, sentence, meaning, author, cc))

    def get_traditional_sentence(self, result):
        if result["script"] == "Hant":
            return result["text"]
        for transcription in result["transcriptions"]:
            if transcription["script"] == "Hant":
                return transcription["text"]
        return ""

    def get_translation(self, translations):
        meaning = ""
        for translation in translations:
            if len(translation) == 0:
                continue # handle weird empty case
            meaning = translation[0]["text"]
            if len(meaning) > 0:
                break
        return meaning

class TatoebaSentence:
    def __init__(self, word, sentence, meaning, author, cc):
        self.word = word
        self.sentence = sentence
        self.meaning = meaning
        self.author = author
        self.cc = cc
        self.zhuyin = hanzi.to_zhuyin(sentence)
        self.pinyin = hanzi.to_pinyin(sentence)

    def __str__(self):
        return f"{self.word}\t{self.sentence}\t{self.zhuyin}\t{self.pinyin}\t{self.meaning}\t{self.author}\t{self.cc}"

    def option(self):
        return f"{self.sentence} | {self.meaning} | (by {self.author})"

def process_word(text):
    tatoeba = Tatoeba(text)
    tatoeba.call()
    if not tatoeba.has_result:
        print("No sentence results")
        return
    tatoeba.populate_sentences()
    options = []
    index = 0
    for sentence in tatoeba.sentences:
        options.append( (index, sentence.option()) )
        index+=1

    result = choice(
            message="Select sentence",
            options=options,
            default=0,
            style=STYLE,
            show_frame=~is_done,
    )
    picked = tatoeba.sentences[result]
    return picked

def input_loop():
    text = prompt("> ")
    result = []
    while text != "":
        result.append(process_word(text))
        text = prompt("> ")
    for chosen in filter(None, result):
        print(chosen)

def file_loop(input_file):
    result = []
    with open(input_file, encoding='utf-8') as f:
        for word in f:
            result.append(process_word(word.rstrip()))
    for chosen in filter(None, result):
        print(chosen)

# pylint: disable=no-value-for-parameter
@click.command()
@click.option('-i', '--input_file', help='File to read the words from, one word per line.')
@click.option('--repl', is_flag=True, default=True, help='Open a REPL to query one word at a time.')
def run(input_file, repl):
    if input_file:
        file_loop(input_file)
    elif repl:
        input_loop()

if __name__ == '__main__':
    run()
