#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gensim.downloader as api
from gensim.models.word2vec import Word2Vec
import numpy as np
from sklearn.linear_model import LinearRegression
import pickle

w2v = api.load('word2vec-google-news-300')
models = ['Guardian_Pre', 'Guardian_Post', 'Daily Mail_Pre', 'Daily Mail_Post']

for model in models:

    mod = Word2Vec.load("./word2vec/{}.model".format(model))
    
    # Get transformation words
    transformation_words = set.intersection(
        set(mod.wv.index2word),
        set(w2v.wv.index2word)
        )

    # Get training matrices
    X = np.concatenate([np.tile(mod[word], (25,1)) for word in transformation_words])

    ylist = []
    for word in transformation_words:
        nn = [i[0] for i in w2v.similar_by_word(word, 25)]
        ylist.extend(np.array([w2v[n] for n in nn]))
    Y = np.array(ylist)

    lr = LinearRegression(fit_intercept=False)
    lr.fit(X, Y)

    outmat = lr.predict(mod.wv.vectors)
    transmat = lr.coef_
    outlist = [mod.wv.index2word, outmat, transmat]
    

    with open('./alignement/{}.pkl'.format(model), 'wb') as f:
        pickle.dump(outlist, f)

    
