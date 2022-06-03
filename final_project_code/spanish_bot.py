import csv
import heapq
import pymysql
import logging
import random
from datetime import datetime
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session, request
#from database_access import *
import database_access
app = Flask(__name__)

ask = Ask(app, "/")

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

FLASHCARDS_FILENAME = "small_flashcards.csv"
USERS = set()
render_question_template = lambda x, *args: question(render_template(x, *args))

### Intents

@ask.launch
def new_session():
    return render_question_template('login')


@ask.intent("LoginIntent", convert={"username": str})
def login(username):

    session.attributes['username'] = username

    user_in_db = database_access.get_user_by_name(username)
    print("Returned user: ", user_in_db)

    if not user_in_db:
        template_welcome = 'new_user_welcome'
        return_statement = render_template(template_welcome, username=username)
    else:
        template_welcome = 'old_user_welcome'
        num_cards = user_in_db['number_of_cards']
        num_fails = user_in_db['total_failures']
        num_successes = user_in_db['total_successes']
        return_statement = render_template(template_welcome, username=username,
                                           num_cards=num_cards, num_fails=num_fails,
                                           num_successes=num_successes)
    return question(return_statement)


@ask.intent("SetLearningPrefsIntent", convert={"practice_cadence": int})
def setup_new_user(practice_cadence):
    initialize_flashcards(session.attributes['username'], practice_cadence)
    return question(render_template("user_preference_confirmation", practice_cadence=practice_cadence))


@ask.intent("AddFlashcardIntent", convert={"english_word": str, "spanish_word": str})
def add_flashcard(english_word, spanish_word):
    add_flashcard_to_deck(english_word, spanish_word)
    return question(render_template('add_flashcard_complete'))


@ask.intent("AskMenuIntent")
def return_menu():
    return question(render_template('return_menu_options'))


@ask.intent("AskEnglishQuestionIntent")
def ask_english_question():
    current_card = get_flashcard()
    return question(render_template('test_vocab', spanish_word=current_card[1]))


@ask.intent("AskSpanishQuestionIntent")
def ask_spanish_question():
    current_card = get_flashcard()
    return question(render_template('test_spanish_vocab', english_word=current_card[0]))


@ask.intent("AnswerQuestionEnglishIntent", convert={"answer_english": str})
def answer_question_english(answer_english):
    flashcard = session.attributes['flashcard']
    flashcard_id = flashcard['id']
    english_word = flashcard['source']
    spanish_word = flashcard['translation']

    if english_word == None:
        return question(render_template('no_question'))

    if answer_english != english_word:
        increment_SM2_vals(flashcard_id, False)
        return question(render_template('wrong_answer',
                                        spanish_word=spanish_word,
                                        english_word=english_word))
    else:
        increment_SM2_vals(flashcard_id, True)
        return question(render_template('correct_answer'))


@ask.intent("AnswerQuestionSpanishIntent", convert={"answer_spanish": str})
def answer_question_spanish(answer_spanish):
    flashcard = session.attributes['flashcard']
    english_word = flashcard['source']
    spanish_word = flashcard['translation']

    if english_word == None:
        return question(render_template('no_question'))

    if answer_spanish != spanish_word:
        print("SPANISH ANSWER: ", answer_spanish)
        increment_SM2_vals(flashcard_id, False)
        return question(render_template('wrong_answer',
                                        spanish_word=spanish_word,
                                        english_word=english_word))
    else:
        increment_SM2_vals(flashcard_id, True)
        return question(render_template('correct_answer'))


@ask.intent("AMAZON.FallbackIntent")
def fallback():
    return question(render_template('clarify'))


### Helper functions

def get_user_id(username):
    user_id = database_access.get_user_by_name(username)['id']
    return user_id


def initialize_flashcards(username, practice_cadence):
    database_access.insert_user(username, practice_cadence)
    user_id = database_access.get_user_by_name(username)['id']
    database_access.insert_csv_into_flashcards(user_id, FLASHCARDS_FILENAME)
    return


def add_flashcard_to_deck(english_word, spanish_word):
    database_access.insert_card(session.attributes['user_id'], english_word, spanish_word)
    return

def set_flashcards(username):
    user_id = database_access.get_user_by_name(username)['id']
    
    flashcards = []

    flashcards_data = database_access.get_all_flashcards_for_users(user_id=user_id)
    for flashcard in flashcards_data:
        print(flashcard['i'], flashcard)
        heapq.heappush(flashcards, (int(flashcard['i']), flashcard['id']))
    session.attributes['flashcards'] = flashcards

# TODO: get statistics by username
def get_summary_statistics(username):
    statistics = database_access.get_user_by_name(username)
    return statistics

# TODO: Weigh cards by success/failure rate
def get_flashcard():
    if 'flashcards' not in session.attributes:
        set_flashcards(session.attributes['username'])

    flashcards = session.attributes['flashcards']
    flashcard_id = heapq.heappop(flashcards)[1]
    print("Flashcard id is ", flashcard_id)

    session.attributes['flashcard'] = database_access.get_flashcard(flashcard_id)
    flashcard = session.attributes['flashcard']

    return (flashcard['source'], flashcard['translation'])

def increment_SM2_vals(flashcard_id, q):
    flashcard = session.attributes['flashcard']

    n = flashcard['n']
    ef = flashcard['ef']
    i = flashcard['i']

    n, ef, i = SM2(q, n, ef, i)
    database_access.set_sm_2_vals(flashcard_id, n, ef, i)

    flashcard['n'] = n
    flashcard['ef'] = ef
    flashcard['i'] = i

    flashcards = []
    flashcards_old = list(session.attributes['flashcards'])
    for x in flashcards_old:
        heapq.heappush(flashcards, (x[0], x[1]))
    heapq.heappush(flashcards, (i, flashcard['id']))
    session.attributes['flashcards'] = flashcards

def SM2(q: bool, n: int, ef: float, i: int):
    if q:
        if n == 0:
            i = 1
        elif n == 1:
            i = 6
        else:
            i = int(i * ef)
        n += 1
        ef += 0.1
    else:
        n, i = 0,1
        ef -= 0.8

    return n, ef, i

if __name__ == "__main__":
    app.run(debug=True)
