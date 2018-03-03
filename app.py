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
import json
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
# coutns occurances
from collections import Counter
# to scrape html and xml
from bs4 import BeautifulSoup
from rq import Queue
from rq.job import Job
from worker import conn

################Configurations##############################

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# sets up a Redis connection and init queue
q = Queue(connection=conn)

#############################################################
from models import Result

def count_and_save_words(url):

    errors = []

    try:
        r = requests.get(url)
    except:
        errors.append(
            "Unable to get URL. Please make sure it's valid and try again."
        )
        return {"error": errors}

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
    # always be careful when querrying with database

    # save the results
    try:
        result = Result(
            url=url,
            result_all=raw_word_count,
            result_no_stop_words=no_stop_words_count
        )
        db.session.add(result)
        db.session.commit()
        return result.id
    except:
        errors.append("Unable to add item to database.")
        return {"error": errors}

@app.route('/', methods=['GET', 'POST'])
def index():
  return render_template('index.html')

@app.route('/start', methods=['POST'])
def get_counts():
  data = json.loads(request.data.decode())
  url = data['url']
  # to send GET requests to grab the content from the URL
  if 'http://' not in url[:7] and 'https://' not in url[:8]:
      url = 'http://' + url
  job = q.enqueue_call(
    func=count_and_save_words, args=(url,), result_ttl=50
    )
  return (job.get_id())
  
@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = Job.fetch(job_key, connection=conn)
    print(job.is_finished)
    if job.is_finished:
        result = Result.query.filter_by(id=job.result).first()
        results = sorted(
            result.result_no_stop_words.items(),
            key=operator.itemgetter(1),
            reverse=True
        )[:10]
        return jsonify(results)
    else:
        return "Nay!", 202

if __name__ == '__main__':
  app.run()