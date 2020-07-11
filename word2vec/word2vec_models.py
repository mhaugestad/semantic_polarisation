#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from nltk.corpus import stopwords
import spacy
import en_core_web_sm
import pandas as pd
from gensim.models import Word2Vec
from gensim.models.phrases import Phrases, Phraser
from tqdm import tqdm
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Call in and clean data
now_articles = pd.read_csv('./now_articles.txt', sep = "\t",
                          names = ['date', 'period', 'outlet', 'outlet_type', 'politics', 'tag', 'text', 'title'],
                          skip_blank_lines = True).dropna()
now_articles['year'] = pd.to_datetime(now_articles.date).apply(lambda x: x.year)
df = now_articles.loc[(now_articles.year.isin([2013, 2014, 2015, 2016, 2017, 2018])) &\
                       (now_articles.outlet.isin(['Daily Mail', 'Guardian']))]
df['mods'] = df.outlet + "_" +  df.year.apply(lambda x: 'Pre' if x < 2016 else 'Post')

# Retokenize entities                       
class EntityRetokenizeComponent:
  def __init__(self, nlp):
    pass
  def __call__(self, doc):
    for entity in doc.ents:
        if entity.label_ in ["PERSON", "ORG", "GPE", "NORP"]:
            with doc.retokenize() as retokenizer:
                retokenizer.merge(entity)
    return doc


nlp = en_core_web_sm.load()
retokenizer = EntityRetokenizeComponent(nlp) 
nlp.add_pipe(retokenizer, name='merge_phrases', last=True)
StopWords = set(stopwords.words('english'))
StopWords.update(['-PRON-'])

for mod in ['Guardian_Pre', 'Guardian_Post', 'Daily Mail_Pre', 'Daily Mail_Post']:    
    raw_data = df.loc[df.mods == mod]

    articles = []
    for art in tqdm(nlp.pipe(raw_data.text, n_process=12, batch_size =500)):
        articles.append([tok.lemma_.lower().strip() for tok in art if len(tok.text.strip()) > 1])

    phrases = Phrases(articles, common_terms = StopWords)
    bigram = Phraser(phrases)
    tphrases = Phrases(bigram[articles], common_terms = StopWords)
    trigram = Phraser(tphrases)

    phrased_articles = [trigram[bigram[art]] for art in articles]
    
    model = Word2Vec(phrased_articles, size=300, window=7, min_count=200, workers=12, sg = 1, iter = 15)
    model.save("./word2vec/{}.model".format(mod))
