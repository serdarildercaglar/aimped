# Author AIMPED
# Date 2023-March-12
# Description This file contains the pipeline for assertion detection of clinical notes

import pandas as pd
import numpy as np

def AssertionAnnotateSentence(df):
    """
    It annotates the sentence with [Entity] tags.   
    parameters:
    ----------------
    df: pandas dataframe
    return:
    ----------------
    df['new_sentence']: str
    """

    df['new_sentence'] = " ".join([
        df['sentence'][:df['sent_begin']],
        ' [Entity] ',
        df['sentence'][df['sent_begin']:df['sent_end']],
        ' [Entity] ',
        df['sentence'][df['sent_end']:]])
    return df['new_sentence']


def AssertionModelResults(ner_results, sentences, classifier, assertion_white_label_list, resolver = False):
    """
    It returns the assertion detection results of a text.
    parameters:
    ----------------
    ner_results: list of dict
    sentences: list of str
    tokenizer: transformers.tokenization_utils_base.PreTrainedTokenizer
    model: transformers.modeling_utils.PreTrainedModel
    classifier: transformers.modeling_utils.PreTrainedModel
    return:
    ----------------
    df.to_dict(orient = 'records'): list of dict
    """

    df = pd.DataFrame()
    if len(ner_results) >= 1:
        ner_results = list(map(lambda x: list(x.values()), ner_results))
        df = pd.DataFrame(ner_results)
        df.columns = ['ner_label', 'chunk', 'begin', 'end', 'sent_idx', 'sent_begin', 'sent_end']
        if len(df) != 0:
            df['sentence'] = np.nan
            for i in df.sent_idx.unique():
                df.loc[df[df.sent_idx == i].index, 'sentence'] = sentences[i]
            df['new_sentence'] = np.nan
            df['new_sentence'] = df.apply(AssertionAnnotateSentence, axis=1)
            df.reset_index(drop=True, inplace=True)
            rel_results = classifier(list(df['new_sentence']))
            df = pd.concat([df, pd.DataFrame(rel_results)], axis=1)
            if not resolver:
                df = df[['begin', 'end', 'ner_label', 'chunk', 'label','score']]
                df.columns = ['begin','end', 'ner_label', 'chunk', 'assertion','score']
            else:
                df = df[['begin', 'end', 'ner_label', 'chunk', 'sent_idx','label']]
                df.columns = ['begin','end', 'entity', 'chunk','sent_idx', 'assertion']
            df =df[df['assertion'].isin(assertion_white_label_list)]
    return df.to_dict(orient='records')


# visualizer

import random
import colorsys
from IPython.display import HTML, display

class AssertionVisualizer:
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
        self.assertion_color_map = {}

    def generate_random_color(self):
        h, s, l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
        r, g, b = [int(256*i) for i in colorsys.hls_to_rgb(h, l, s)]
        dark = f"rgb({r}, {g}, {b})"
        light = f"rgba({r}, {g}, {b}, 0.12)"
        return {"dark": dark, "light": light}

    def get_color(self, label):
        if label not in self.color_map:
            if len(self.color_map) < len(self.colors):
                self.color_map[label] = self.colors[len(self.color_map)]
            else:
                self.color_map[label] = self.generate_random_color()
        return self.color_map[label]

    def get_assertion_color(self, assertion):
        if assertion not in self.assertion_color_map:
            if len(self.assertion_color_map) < len(self.colors):
                self.assertion_color_map[assertion] = self.colors[-(len(self.assertion_color_map) + 1)]["dark"]
            else:
                self.assertion_color_map[assertion] = self.generate_random_color()["dark"]
        return self.assertion_color_map[assertion]

    def visualize(self, text, data, is_short=False, show_size=None):
        output = []
        html = ['<div style="padding: 14px;"><div dir="auto">']
        
        if is_short and show_size:
            for entity in data:
                if entity["end"] < show_size:
                    output.append(entity)
                else:
                    break
        else:
            output = data

        last_index = 0
        for entity in output:
            # Add plain text before the entity
            plain_text = text[last_index:entity["begin"]]
            if plain_text:
                html.append(f'<span class="non-ner">{plain_text}</span>')

            # Add the entity
            color = self.get_color(entity["ner_label"])
            assertion_color = self.get_assertion_color(entity["assertion"])
            
            html.append(f'''
                <span class="entity-wrapper-outer" style="border-color: {color['dark']};">
                    <span class="entity-wrapper" style="background-color: {color['light']};">
                        <span class="entity-name">{entity["chunk"]}</span>
                        <span class="entity-type" style="background-color: {color['dark']};">{entity["ner_label"]}</span>
                    </span>
                    <span class="entity-type-assertion" style="background-color: {assertion_color};">{entity["assertion"]}</span>
                </span>
            ''')

            last_index = entity["end"]

        # Add any remaining text
        if last_index < len(text):
            remaining_text = text[last_index:]
            if is_short and show_size and len(text) > show_size:
                remaining_text = remaining_text[:show_size - last_index] + "..."
            html.append(f'<span class="non-ner">{remaining_text}</span>')

        html.append('</div></div>')

        css = '''
        <style>
        .non-ner {
            color: black;
            line-height: 3.4rem;
            font-size: 1rem;
        }
        .entity-wrapper-outer {
            display: inline-grid;
            text-align: center;
            border-radius: 4px;
            margin: 5px 2px;
            border: 1px solid;
            font-size: 1rem;
        }
        .entity-wrapper {
            display: inline-flex;
            text-align: center;
            justify-content: space-between;
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
        .entity-type, .entity-type-assertion {
            font-size: 0.9rem;
            line-height: 1.5rem;
            color: #fff;
            text-transform: uppercase;
            font-weight: 500;
            display: inline-block;
            padding: 3px 5px;
        }
        </style>
        '''

        return css + ''.join(html)

    def display_visualization(self, text, data, is_short=False, show_size=None):
        html_output = self.visualize(text, data, is_short, show_size)
        display(HTML(html_output))