# to get path and set environment variables
import os
# to send GET requests to the desired URL
import requests
#such like  lt, gt, ge operators
import operator
# regular expressions
import re
# natural language
import nltk
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
# coutns occurances
from collections import Counter
# to scrape html and xml
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Result

@app.route('/', methods=['GET', 'POST'])
def index():
  errors = []
  results = {}
  r = None
  if request.method == "POST":
    try:
      # handle GET and POST requests, grab value
      # corresponding to url key
      # use request.form.get('url') is key might not exist
      url = request.form['url']
      # to send GET requests to grab the content from the URL
      r = requests.get(url)
    except:
      errors.append("Not a valid URL request")
    if r:
      raw = BeautifulSoup(r.text, 'html.parser').get_text()
      # set path
      nltk.data.path.append('./nltk_data/')
      # list of strings of tokenized words
      tokens = nltk.word_tokenize(raw)
      stops = nltk.corpus.stopwords.words('english')
      # a wrapper around tokens to Text class
      # use it later for regex search
      text = nltk.Text(tokens)
      # remove puntuations. compiles into regex object
      # faster to compile since this will be cached
      nonPunct = re.compile('[A-Za-z]+')
      punct = re.compile('[\W]+|\d')
      # store all words matched with regex into list
      # only matches the beginnign of string
      raw_words = [w for w in text if nonPunct.match(w) and not punct.search(w)]
      # get raw word counts
      raw_word_count = Counter(raw_words)
      # get rid of all stop words, which are in lower case only
      no_stop_words = [w for w in raw_words if w.lower() not in stops]
      # get new count. 
      no_stop_words_count = Counter(no_stop_words)
      # store into results
      # sorted -> build new sorted list from iterable
      results = sorted(
        # returns a list of tuples
        no_stop_words_count.items(),
        # this will get the second position element from the tuple
        # multiple item extraction
        # love this method
        key=operator.itemgetter(1),
        reverse=True
      )[:10]
      # always be careful when querrying with database
      try:
        result = Result(
            url=url,
            result_all=raw_word_count,
            result_no_stop_words=no_stop_words_count
        )
        db.session.add(result)
        db.session.commit()
      except:
        errors.append("Unable to add item to database.")
  return render_template('index.html', errors=errors, results=results)

@app.route('/<name>')
def hello_name(name):
  return "Hello {}!".format(name)


if __name__ == '__main__':
  app.run()