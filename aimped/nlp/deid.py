# Author: AIMPED
# Date: 2023-March-12
# Description: This file contains the pipeline for de-identification of clinical notes
import pandas as pd
import random

def maskText(merged, text):
    """
    It masks the actual chunks in the text with their entity labels.
    parameters:
    ----------------
    merged: list of dict
    text: str
    return:
    ----------------
    masked_text: str
    """
    text_mask = text[:]
    for i in range(len(merged) - 1, -1, -1):
        text_mask = text_mask[:merged[i]['begin']] + f"<<{merged[i]['entity']}>>" + text_mask[merged[i]['end']:]
    return text_mask


def fakedChunk(fake_csv_path, merged ):
    """ 
    Randomly select entities from fake.csv file and add them to entities list align with true labels.
    parameters:
    ----------------
    fake_csv_path: str
    merged: list of dict
    return:
    ----------------
    merged: list of dict
    """


    fake_df = pd.read_csv(fake_csv_path, sep=',', encoding='utf8')
    for item in merged:
        item["faked_chunk"] = str(random.choice(fake_df[item['entity']]))
    return merged


def fakedText(merged, text):
    """
    Rewrite the text with faked chunks that comes from fakedChunk function.
    parameters:
    ----------------
    merged: list of dict
    text: str
    return:
    ----------------
    faked_text: str
    """
    
    faked_text = text[:]
    for i in range(len(merged) - 1, -1, -1):
        faked_text = faked_text[:merged[i]['begin']] + f"{merged[i]['faked_chunk']}" + faked_text[merged[i]['end']:]
    return faked_text


def deidentification(faked, masked, merged_results, text, fake_csv_path):
    """
    It masks the actual chunks in the text with their entity labels.
    parameters:
    ----------------
    faked: bool
    masked: bool
    merged_results: list of dict
    text: str
    fake_csv_path: str
    return:
    ----------------
    entities: list of dict
    masked_text: str
    faked_text: str
    """
    if faked and masked:
        text_mask = maskText(merged=merged_results, text=text)
        entities_with_faked_chunks = fakedChunk(fake_csv_path=fake_csv_path, merged=merged_results)
        faked_text = fakedText(merged=entities_with_faked_chunks, text=text)
        return {"entities": entities_with_faked_chunks, "masked_text":text_mask,"faked_text":faked_text}
    elif faked:
        entities_with_faked_chunks = fakedChunk(fake_csv_path=fake_csv_path,merged=merged_results)
        faked_text = fakedText(merged=entities_with_faked_chunks, text=text)
        return {"entities": entities_with_faked_chunks, "faked_text":faked_text}
    elif masked:
        text_mask = maskText(merged=merged_results, text=text)
        return {"entities": merged_results, "masked_text":text_mask}

    else:
        return {"entities": merged_results}
    

# visualizing the de-identified text

import random
import colorsys
from IPython.display import HTML, display

class DeidentificationVisualizer:
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

    def visualize_phi_entities(self, text, entities, is_short=False, show_size=None):
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

    def visualize_anonymized(self, text, entities, is_short=False, show_size=None):
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

    def visualize_pseudonymized(self, text, entities, is_short=False, show_size=None):
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
                    <span class="entity-name">{entity["faked_chunk"]}</span>
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

    def visualize(self, text, entities, mode='phi_entities', is_short=False, show_size=None):
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
        
        if mode == 'phi_entities':
            html = self.visualize_phi_entities(text, entities, is_short, show_size)
        elif mode == 'anonymized':
            html = self.visualize_anonymized(text, entities, is_short, show_size)
        elif mode == 'pseudonymized':
            html = self.visualize_pseudonymized(text, entities, is_short, show_size)
        else:
            raise ValueError("Invalid mode. Choose 'phi_entities', 'anonymized', or 'pseudonymized'.")
        
        return css + html

    def display_visualization(self, text, entities, mode='phi_entities', is_short=False, show_size=None):
        html_output = self.visualize(text, entities, mode, is_short, show_size)
        display(HTML(html_output))

## Example usage
# if __name__ == "__main__":
#     visualizer = DeidentificationVisualizer()
    
#     sample_text = "John Smith was admitted on 2023-05-15 with severe abdominal pain."
#     sample_entities = [
#         {"begin": 0, "end": 10, "chunk": "John Smith", "entity": "PERSON", "faked_chunk": "Alice Johnson"},
#         {"begin": 27, "end": 37, "chunk": "2023-05-15", "entity": "DATE", "faked_chunk": "2023-06-20"}
#     ]
    
#     print("PHI Entities Visualization:")
#     visualizer.display_visualization(sample_text, sample_entities, mode='phi_entities')
    
#     print("\nAnonymized Visualization:")
#     visualizer.display_visualization(sample_text, sample_entities, mode='anonymized')
    
#     print("\nPseudonymized Visualization:")
#     visualizer.display_visualization(sample_text, sample_entities, mode='pseudonymized')