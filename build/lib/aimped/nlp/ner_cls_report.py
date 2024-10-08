# -*- coding: utf-8 -*-
"""ner_cls_report

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LJIu53E46CcoGLqcAhgav970B6X-coYm
"""

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

try:        
    from seqeval.metrics import classification_report
except:
    print('seqeval is not installed. Please install it with pip install seqeval')

from sklearn.metrics import classification_report
    
def ReadConll(filename):
    df = pd.read_csv(filename,
                    sep = ' ', header = None, keep_default_na = False,
                    names = ['words', 'pos', 'chunk', 'labels'],
                    quoting = 3, 
                     skip_blank_lines = False, 
                     encoding="utf8")
    df = df[~df['words'].astype(str).str.startswith('-DOCSTART-')] # Remove the -DOCSTART- header
    df['sentence_id'] = (df.words == '').cumsum()
    return df[df.words != '']

def ClsReportNerModel(test_conll_path, tokenizer, model, device):


    test = ReadConll(test_conll_path)
    sents_tokens_list, truth_list = [],[]
    model = model.to(device)
    for i in test.sentence_id.unique():
        sents_tokens_list.append(list(test[test.sentence_id == i].words))
        truth_list.append(list(test[test.sentence_id == i].labels))
    tokens,preds,truths= [],[],[]
    for sentence_idx, sent_token_list in enumerate(sents_tokens_list):
        model_inputs = tokenizer(sent_token_list, is_split_into_words = True, truncation=True,
                                        padding=False, max_length=512, return_tensors="pt").to(device)
        word_ids = model_inputs.word_ids() # sub tokenlar sent_token_list deki hangi idxteki tokena ait
        # ornek word_ids = [None, 0, 1, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 11, 12, 13, 14, 15, None]
        outputs = model(**model_inputs)
        predictions = outputs.logits.argmax(dim=-1).tolist()[0]
        idx = 1
        while idx < len(word_ids)-1: # sondaki None icin islem yapmamak icin -1 yapildi
            word_id1 = word_ids[idx]
            word_id2 = word_ids[idx + 1]
            label = model.config.id2label[predictions[idx]]
            if word_id1 == word_id2:
                while word_id1 == word_ids[idx]:                
                    idx +=1
                idx -=1

            token = sent_token_list[word_ids[idx]]
            truth = truth_list[sentence_idx][word_ids[idx]]
            tokens.append(token)        
            preds.append(label)
            truths.append(truth)
            idx +=1

    print(classification_report([truths], [preds], digits = 4, mode = 'strict'))
    print(classification_report(truths, preds, digits = 4))
