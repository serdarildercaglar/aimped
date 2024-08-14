# Author AIMPED
# Date 2023-March-14
# Description This file contains the pipeline for relation extraction.

import itertools
import pandas as pd
import numpy as np

def RelationAnnotateSentence(df):
    """It annotates the sentence with [Entity] tags.
    parameters:
    ----------------
    df: pandas dataframe
    return:
    ----------------
    df['new_sentence']: str
    """

    a1_start = min(df['sent_begin1'] - 1, df['sent_begin2'])
    a1_end = min(df['sent_end1'] + 1, df['sent_end2'] + 1)

    a2_start = max(df['sent_begin1'] - 1, df['sent_begin2'])
    a2_end = max(df['sent_end1'] + 1, df['sent_end2'] + 1)

    df['new_sentence'] = " ".join([
        df['sentence'][:a1_start],
        'e1b',
        df['sentence'][a1_start:a1_end],
        'e1e',
        df['sentence'][a1_end:a2_start],
        'e2b',
        df['sentence'][a2_start:a2_end],
        'e2e',
        df['sentence'][a2_end:]
    ])

    return df['new_sentence']


def RelationResults(sentences, ner_chunk_results, relation_classifier,
                    relation_white_label_list, relation_pairs, return_svg):
    """It returns the relation results of a text.
    parameters:
    ----------------
    sentences: list of str
    ner_chunk_results: list of dict
    relation_classifier: str
    ner_white_label_list: list of str
    relation_white_label_list: list of str
    relation_pairs: list of tuple
    return_svg: bool
    return:
    ----------------
    results: list of dict
    """

    end_df = pd.DataFrame()
    if len(ner_chunk_results) == 0:
        return end_df.to_dict(orient='records')
    else:
        df_ner_chunk_results = pd.DataFrame(ner_chunk_results)
        for i in df_ner_chunk_results.sent_idx.unique():
            sentence_bazli_ner_results = df_ner_chunk_results[df_ner_chunk_results.sent_idx == i]
            sentence_bazli_ner_results = sentence_bazli_ner_results.values.tolist()
            if len(sentence_bazli_ner_results) >= 2:
                df = pd.DataFrame(itertools.combinations(sentence_bazli_ner_results, 2))
                df['firstCharEnt1'] = df[0].apply(lambda x: x[2])
                df['lastCharEnt1'] = df[0].apply(lambda x: x[3])
                df['entity1'] = df[0].apply(lambda x: x[0])
                df['chunk1'] = df[0].apply(lambda x: x[1])
                df['sent_begin1'] = df[0].apply(lambda x: x[-2])
                df['sent_end1'] = df[0].apply(lambda x: x[-1])
                df['firstCharEnt2'] = df[1].apply(lambda x: x[2])
                df['lastCharEnt2'] = df[1].apply(lambda x: x[3])
                df['entity2'] = df[1].apply(lambda x: x[0])
                df['chunk2'] = df[1].apply(lambda x: x[1])
                df['sent_begin2'] = df[1].apply(lambda x: x[-2])
                df['sent_end2'] = df[1].apply(lambda x: x[-1])

                df = df[df.apply(lambda row: any((row['entity1'], row['entity2']) == item for item in relation_pairs), axis=1)]


                if len(df) != 0:
                    df['sentID'] = i
                    df['sentence'] = sentences[i]
                    df = df.drop([0, 1], axis=1)
                    df['new_sentence'] = np.nan
                    df['new_sentence'] = df.apply(RelationAnnotateSentence, axis=1)
                    df.reset_index(drop=True, inplace=True)
                    rel_results = relation_classifier(list(df['new_sentence']))
                    df = pd.concat([df, pd.DataFrame(rel_results)], axis=1)
                    df = df[['sentID', 'sentence', 'firstCharEnt1', 'sent_begin1', 'lastCharEnt1', 'sent_end1', 'entity1',
                             'chunk1',
                             'firstCharEnt2', 'sent_begin2', 'lastCharEnt2', 'sent_end2', 'entity2', 'chunk2', 'label',
                             'score'
                             ]]
                    df = df[df['label'].isin(relation_white_label_list)]
                    end_df = pd.concat([end_df, df], ignore_index=True)

        if end_df.empty or return_svg:
            return end_df.to_dict(orient='records')

        else:
            return end_df[['firstCharEnt1', 'lastCharEnt1', 'entity1', 'chunk1',
                           'firstCharEnt2', 'lastCharEnt2', 'entity2', 'chunk2', 'label', 'score']].to_dict(
                orient='records')

########################## neo4j knowledge graph ##########################
import json
from neo4j import GraphDatabase

## Creating a Connection Class
class Neo4j:

    def __init__(self, uri, user, pwd, db=None):

        self.__url = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        self.db = db
        try:
            self.__driver = GraphDatabase.driver(self.__url, auth=(self.__user, self.__pwd))
            print("Connection Successful!")

        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):

        if self.__driver is not None:
            self.__driver.close()
            

    def create_neo4j_query(self, json_output=None, json_file=None):
        
        if json_output:
            data = json_output["output"]["data_json"]["result"]
        elif json_file:
            with open(json_file) as f:
                data = json.load(f)
            data = data["output"]["data_json"]["result"]
            
        queries = []
        for i in data:
            for item in i:
                entity1 = item["entity1"].replace("-","_")
                chunk1 = item["chunk1"].replace("'","")
                entity2 = item["entity2"].replace("-","_")
                chunk2 = item["chunk2"].replace("-","_")
                label = item["label"].replace("-","_")
                
                query = f"""
                MERGE (e1:{entity1} {{name: '{chunk1}'}})
                MERGE (e2:{entity2} {{name: '{chunk2}'}})
                MERGE (e1)-[:{label}]->(e2)
                """
                queries.append(query)
        print("Queries Created!")
        return queries            

    def run_query(self, query, parameters=None, db=None):
        if db is None:
            db = self.db
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None

        try:
            session = self.__driver.session(database=db) if db is not None else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response
    
    def write_data(self, queries=None, db=None):
        if db is None:
            db = self.db
        try:
            assert self.__driver is not None, "Driver not initialized!"
        except AssertionError as e:
            print(e)
        try:
            assert isinstance(queries, list), "Queries should be a list!"
        except AssertionError as e:
            print(e)
        try:
            assert len(queries) > 0, "Queries list is empty!"
        except AssertionError as e:
            print(e)
        try:
            print("Writing data to Neo4j...")
            for query in queries:
                self.run_query(query=query, db=db)  
            print("Data written successfully!")  
        except Exception as e:
            print("Failed to write data:", e)

    
    






    
