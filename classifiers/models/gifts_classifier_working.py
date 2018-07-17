#!/usr/bin/env python
# -*- coding: utf-8 -*-
import django
import os
import pandas as pd
import xgboost
from sklearn import ensemble, metrics, model_selection, preprocessing, linear_model, naive_bayes
from sklearn.externals import joblib
from sklearn.feature_extraction.text import CountVectorizer

os.environ['DJANGO_SETTINGS_MODULE'] = 'arbot.settings'
django.setup()

from amazon.models import Review


if __name__ == '__main__':
    reviews = Review.objects.all()
    train_df = pd.DataFrame()
    labels = []
    texts = []

    # Load the data
    df = pd.read_csv('classifiers/training/gifts.csv', names=['text', 'label'])

    # Split the dataset into training and validation datasets
    train_x, valid_x, train_y, valid_y = model_selection.train_test_split(df['text'], df['label'])

    # Label encode the target variable
    encoder = preprocessing.LabelEncoder()
    train_y = encoder.fit_transform(train_y)
    valid_y = encoder.fit_transform(valid_y)

    # Create a count vectorizer object
    count_vect = CountVectorizer(analyzer='word', token_pattern=r'\w{1,}')
    count_vect.fit(df['text'])

    # Transform the training and validation data using count vectorizer object
    xtrain_count = count_vect.transform(train_x)
    xvalid_count = count_vect.transform(valid_x)

    # Select algorithm
    max_accuracy = 0

    # Mulitnomial naive bayes
    classifier = naive_bayes.MultinomialNB()
    classifier.fit(xtrain_count, train_y)
    predictions = classifier.predict(xvalid_count)
    accuracy = metrics.accuracy_score(predictions, valid_y)
    print('Naive bayes: {0:.2f}%'.format(accuracy))
    max_accuracy = accuracy
    clf = classifier

    # Linear regression
    classifier = linear_model.LogisticRegression()
    classifier.fit(xtrain_count, train_y)
    predictions = classifier.predict(xvalid_count)
    accuracy = metrics.accuracy_score(predictions, valid_y)
    print('Logistic regression: {0:.2f}%'.format(accuracy))
    if accuracy > max_accuracy:
        max_accuracy = accuracy
        clf = classifier

    # Random forrest
    classifier = ensemble.RandomForestClassifier()
    classifier.fit(xtrain_count, train_y)
    predictions = classifier.predict(xvalid_count)
    accuracy = metrics.accuracy_score(predictions, valid_y)
    print('Random forrest: {0:.2f}%'.format(accuracy))
    if accuracy > max_accuracy:
        max_accuracy = accuracy
        clf = classifier

    # Xgboost
    classifier = xgboost.XGBClassifier()
    classifier.fit(xtrain_count.tocsc(), train_y)
    predictions = classifier.predict(xvalid_count)
    accuracy = metrics.accuracy_score(predictions, valid_y)
    print('XGBoost: {0:.2f}%'.format(accuracy))
    if accuracy > max_accuracy:
        max_accuracy = accuracy
        clf = classifier

    joblib.dump(clf, 'classifiers/models/gifts.pkl')
    joblib.dump(count_vect.vocabulary_, 'classifiers/models/gifts_features.pkl')
