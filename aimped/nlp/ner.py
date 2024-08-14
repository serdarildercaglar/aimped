# Author: AIMPED
# Date: 2023-March-11
# Description: NER model results

import torch
import pandas as pd
import numpy as np
import os
import re
import json
from aimped.nlp.tokenizer import sentence_tokenizer, word_tokenizer

def NerModelResults(sents_tokens_list, sentences, tokenizer, model, text, device,
                    assertion_relation=False):
    """
    It returns the NER model results of a text.
    Parameters
    ----------
    sents_tokens_list : list
    tokenizer : transformers.PreTrainedTokenizer
    model : transformers.PreTrainedModel
    text : str
    device : torch.device
    assertion_relation : bool, optional
        The default is False.
    sentences : list, optional
        The default is []. Only used if assertion_relation is True

    Returns
    -------
    tokens : list
    preds : list
    probs : list
    begins : list
    ends : list
    sent_begins : list
        Only returned if assertion_relation is True
    sent_ends : list
        Only returned if assertion_relation is True
    sent_idxs : list
        Only returned if assertion_relation is True
    """

    start = 0
    tokens, probs, begins, ends, preds, sent_begins, sent_ends, sent_idxs = [], [], [], [], [], [], [], []

    for sentence_idx, sent_token_list in enumerate(sents_tokens_list):
        start_sent = 0
        start = text.find(sentences[sentence_idx], start)
        model_inputs = tokenizer(sent_token_list, is_split_into_words=True, truncation=True,
                                 padding=False, max_length=512, return_tensors="pt").to(device)
        word_ids = model_inputs.word_ids()  # sub tokenlar sent_token_list deki hangi idxteki tokena ait
        # ornek word_ids = [None, 0, 1, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 11, 12, 13, 14, 15, None]
        outputs = model(**model_inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1).tolist()[0]
        predictions = outputs.logits.argmax(dim=-1).tolist()[0]
        idx = 1
        while idx < len(word_ids) - 1:  # sondaki None icin islem yapmamak icin -1 yapildi
            word_id1 = word_ids[idx]
            word_id2 = word_ids[idx + 1]
            label = model.config.id2label[predictions[idx]]
            prob = max(probabilities[idx])
            if word_id1 == word_id2:
                while word_id1 == word_ids[idx]:
                    idx += 1
                idx -= 1

            token = sent_token_list[word_ids[idx]]
            begin = text.find(token, start)
            end = begin + len(token)
            tokens.append(token)
            begins.append(begin)
            ends.append(end)
            preds.append(label)
            probs.append(prob)
            start = end
            if assertion_relation:
                sentence_begin = sentences[sentence_idx].find(token, start_sent)
                sentence_end = sentence_begin + len(token)
                sent_begins.append(sentence_begin)
                sent_ends.append(sentence_end)
                sent_idxs.append(sentence_idx)
                start_sent = sentence_end
            idx += 1
    if not assertion_relation:
        return tokens, preds, probs, begins, ends
    else:
        return tokens, preds, probs, begins, ends, sent_begins, sent_ends, sent_idxs


import random
import colorsys
from IPython.display import HTML, display

class NERVisualizer:
    def __init__(self):
        self.colors = [
            {"dark": "#5C5CE0", "light": "rgba(92, 92, 224, 0.12)"},
            {"dark": "#3DA74E", "light": "rgba(61, 167, 78, 0.12)"},
            {"dark": "#CE2783", "light": "rgba(206, 39, 131, 0.12)"},
            {"dark": "#D2B200", "light": "rgba(210, 178, 0, 0.12)"},
            {"dark": "#B130BD", "light": "rgba(177, 48, 189, 0.12)"},
            {"dark": "#16878C", "light": "rgba(22, 135, 140, 0.02)"},
            {"dark": "#7CC33F", "light": "rgba(124, 195, 63, 0.12)"},
            {"dark": "#864CCC", "light": "rgba(134, 76, 204, 0.12)"},
            {"dark": "#1473E6", "light": "rgba(20, 115, 230, 0.12)"},
            {"dark": "#D7373F", "light": "rgba(215, 55, 63, 0.12)"},
            {"dark": "#DA7B11", "light": "rgba(218, 123, 17, 0.12)"},
            {"dark": "#268E6C", "light": "rgba(38, 142, 108, 0.12)"},
        ]
        self.color_map = {}

    def generate_random_color(self):
        h, s, l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
        r, g, b = [int(256*i) for i in colorsys.hls_to_rgb(h, l, s)]
        dark = f"rgb({r}, {g}, {b})"
        light = f"rgba({r}, {g}, {b}, 0.12)"
        return {"dark": dark, "light": light}

    def get_color(self, entity):
        if entity not in self.color_map:
            if len(self.color_map) < len(self.colors):
                self.color_map[entity] = self.colors[len(self.color_map)]
            else:
                self.color_map[entity] = self.generate_random_color()
        return self.color_map[entity]

    def visualize_entities(self, text, entities, is_short=False, show_size=None):
        html = ['<div style="padding: 14px;"><div dir="auto">']
        
        output = entities
        if is_short and show_size:
            output = [e for e in entities if e["end"] < show_size]
        
        last_index = 0
        for entity in output:
            plain_text = text[last_index:entity["begin"]]
            if plain_text:
                html.append(f'<span class="non-ner">{plain_text}</span>')
            
            color = self.get_color(entity["entity"])
            html.append(f'''
                <span class="entity-wrapper" style="background-color: {color['light']}; border-color: {color['dark']};">
                    <span class="entity-name">{entity["chunk"]}</span>
                    <span class="entity-type" style="background-color: {color['dark']};">{entity["entity"]}</span>
                </span>
            ''')
            last_index = entity["end"]
        
        if last_index < len(text):
            remaining_text = text[last_index:]
            if is_short and show_size and len(text) > show_size:
                remaining_text = remaining_text[:show_size - last_index] + "..."
            html.append(f'<span class="non-ner">{remaining_text}</span>')

        html.append('</div></div>')
        return ''.join(html)





    def visualize(self, text, entities, is_short=False, show_size=None):
        css = '''
        <style>
        .non-ner {
            color: black;
            line-height: 2.2rem;
            font-size: 1rem;
        }
        .entity-wrapper {
            display: inline-flex;
            justify-content: space-between;
            text-align: center;
            border-radius: 5px;
            margin: 3px 2px;
            border: 1px solid;
            overflow: hidden;
            font-size: 1rem;
        }
        .entity-name {
            font-size: 0.9rem;
            line-height: 1.5rem;
            text-align: center;
            font-weight: 400;
            padding: 2px 5px;
            display: inline-block;
        }
        .entity-type {
            font-size: 0.9rem;
            line-height: 1.5rem;
            color: #fff;
            text-transform: uppercase;
            font-weight: 500;
            display: inline-block;
            padding: 2px 5px;
        }
        </style>
        '''
        
        html = self.visualize_entities(text, entities, is_short, show_size)

        return css + html

    def display_visualization(self, text, entities, is_short=False, show_size=None):
        html_output = self.visualize(text, entities, is_short, show_size)
        display(HTML(html_output))

