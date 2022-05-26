import csv
import logging
import random
from datetime import datetime
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session, request

app = Flask(__name__)

ask = Ask(app, "/")

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

FLASHCARDS_FILENAME = "flashcards.csv"
#FLASHCARDS_FILENAME = "final_project_code/flashcards.csv"
render_question_template = lambda x, *args: question(render_template(x, *args))
default_rate = '100%'

### Intents

@ask.launch
def new_session():
    session.attributes['current_message'] = 'login' # save the template name to use for repeating the phrase
    return question(render_template('login',rate=default_rate))


@ask.intent("LoginIntent", convert={"username": str})
def login(username):
    session.attributes['flashcards'] = initialize_flashcards(username)
    session.attributes['statistics'] = initialize_statistics(username)
    session.attributes['username'] = username
    session.attributes['current_message'] = 'welcome'
    return question(render_template('welcome',
                                    username=username,
                                    rate=default_rate))

"""
@ask.intent("AddFlashcardIntent", convert={"english_word": str, "spanish_word": str})
def add_flashcard(english_word, spanish_word):
    # TODO: function to add a flashcard to deck
    return question(render_template('add_flashcard_complete'))
"""

@ask.intent("AskVocabQuestionIntent")
def ask_question():
    current_card = get_flashcard()
    session.attributes['current_card'] = current_card
    session.attributes['current_message'] = 'test_vocab'
    return question(render_template('test_vocab',
                                    english_word=current_card[0],
                                    rate=default_rate))


@ask.intent("AnswerVocabQuestionIntent", convert={"vocab_word": str})
def answer_question(vocab_word):
    current_card = session.attributes['current_card']
    if current_card[0] == None:
        session.attributes['current_message'] = 'no_question'
        return question(render_template('no_question',
                                        rate=default_rate))

    if vocab_word != current_card[1]:
        increment_failure(current_card[1])
        session.attributes['current_message'] = 'wrong_answer'
        return question(render_template('wrong_answer',
                                        spanish_word=current_card[1],
                                        english_word=current_card[0],
                                        rate=default_rate))
    else:
        increment_success(current_card[0])
        session.attributes['current_message'] = 'correct_answer'
        return question(render_template('correct_answer',
                                        rate=default_rate))

@ask.intent("InEnglishIntent")
def repeat():
    message = session.attributes['current_message']+'_en'

    # we need to collect the vocab words if we are repeating a vocab question
    if message == 'wrong_answer'+'_en':
        current_card = session.attributes['current_card']
        return question(render_template(message,
                                        spanish_word=current_card[1],
                                        english_word=current_card[0],
                                        rate=default_rate))
    if message == 'test_vocab'+'_en':
        current_card = session.attributes['current_card']
        return question(render_template(message,
                                        english_word=current_card[0],
                                        rate=default_rate))

    # collect the user name if we repeat welcome message
    if message == 'welcome'+'_en':
        username = session.attributes['username']
        return question(render_template(message,
                                        username=username,
                                        rate=default_rate))

    # IF Alexa's response does not need to pass in template information, just pass in the message with _en added
    return question(render_template(message,
                                    rate=default_rate))

@ask.intent("RepeatIntent")
def repeat():
    message = session.attributes['current_message']
    rate = 'slow' # saying things more slowly now
    # we need to collect the vocab words if we are repeating a vocab question
    if message == 'wrong_answer':
        current_card = session.attributes['current_card']
        return question(render_template(message,
                                        spanish_word=current_card[1],
                                        english_word=current_card[0],
                                        rate=rate))
    if message == 'test_vocab':
        current_card = session.attributes['current_card']
        return question(render_template(message,
                                        english_word=current_card[0],
                                        rate=rate))

    # collect the user name if we repeat welcome message
    if message == 'welcome':
        username = session.attributes['username']
        return question(render_template(message,
                                        username=username,
                                        rate=rate))

    # IF Alexa's response does not need to pas in template information, just pass in the message with _en added
    return question(render_template(message,
                                    rate=rate))

@ask.intent("AMAZON.FallbackIntent")
def fallback():
    return question(render_template('clarify'))


### Helper functions

# TODO: Get flashcards by username
def initialize_flashcards(username):
    filename = FLASHCARDS_FILENAME
    flashcards = {}

    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            flashcards[row[0]] = row[1]
    return flashcards


# TODO: get statistics by username
def initialize_statistics(username):
    statistics = {}

    for key in session.attributes['flashcards']:
        statistics[key] = {
            'successes': 0,
            'failures': 0,
            'last_time_seen': str(datetime.max)
        }
    return statistics


# TODO: Weigh cards by success/failure rate
def get_flashcard():
    english_word = random.choice(list(session.attributes['flashcards']))
    spanish_word = session.attributes['flashcards'][english_word]

    return (english_word, spanish_word)


def increment_success(flashcard_q):
    session.attributes['statistics'][flashcard_q]['successes'] += 1
    session.attributes['statistics'][flashcard_q]['last_time_seen'] = str(datetime.now())


def increment_failure(flashcard_q):
    session.attributes['statistics'][flashcard_q]['failures'] += 1
    session.attributes['statistics'][flashcard_q]['last_time_seen'] = str(datetime.now())


if __name__ == "__main__":
    app.run(debug=True)
