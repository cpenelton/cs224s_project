import csv
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

FLASHCARDS_FILENAME = "final_project_code/flashcards.csv"
USERS = set()
render_question_template = lambda x, *args: question(render_template(x, *args))


### Intents

@ask.launch
def new_session():
    return render_question_template('login')


@ask.intent("LoginIntent", convert={"username": str})
def login(username):

    session.attributes['username']= username
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            user_in_db = database_access.get_user_by_name(cursor, username)

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
    english_word = session.attributes['english_word']
    spanish_word = session.attributes['spanish_word']

    if english_word == None:
        return question(render_template('no_question'))

    if answer_english != english_word:
        increment_failure(english_word)
        return question(render_template('wrong_answer',
                                        spanish_word=spanish_word,
                                        english_word=english_word))
    else:
        increment_success(english_word)
        return question(render_template('correct_answer'))


@ask.intent("AnswerQuestionSpanishIntent", convert={"answer_spanish": str})
def answer_question_spanish(answer_spanish):
    english_word = session.attributes['english_word']
    spanish_word = session.attributes['spanish_word']

    if english_word == None:
        return question(render_template('no_question'))

    if answer_spanish != spanish_word:
        print("SPANISH ANSWER: ", answer_spanish)
        increment_failure(english_word)
        return question(render_template('wrong_answer',
                                        spanish_word=spanish_word,
                                        english_word=english_word))
    else:
        increment_success(english_word)
        return question(render_template('correct_answer'))


@ask.intent("AMAZON.FallbackIntent")
def fallback():
    return question(render_template('clarify'))


### Helper functions

def get_user_id(username):
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            user_id = database_access.get_user_by_name(cursor, username)['id']
    return user_id


def initialize_flashcards(username, practice_cadence):
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            database_access.insert_user(cursor, username, practice_cadence)
            user_id = database_access.get_user_by_name(cursor, username)['id']
            database_access.insert_csv_into_flashcards(cursor, user_id, FLASHCARDS_FILENAME)
    return


def add_flashcard_to_deck(english_word, spanish_word):
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            database_access.insert_card(cursor, session.attributes['user_id'],
                                        english_word, spanish_word)
    return


def get_flashcards(username):
    flashcards = {}
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            user_id = database_access.get_user_by_name(cursor, username)['user_id']
            flashcards = database_access.get_all_flashcards_for_users(cursor, user_id=user_id)
    return flashcards


# TODO: get statistics by username
def get_summary_statistics(username):
    statistics = {}
    statistics = database_access.get_user_by_name(username)
    return statistics


# TODO: Weigh cards by success/failure rate
def get_flashcard():
    flashcards = get_flashcards(session.attributes['username'])
    flashcard = random.choice(flashcards)
    session.attributes['flashcard_id'] = flashcard['id']
    session.attributes['english_word'] = flashcard['source']
    session.attributes['spanish_word'] = flashcard['translation']
    return (session.attributes['english_word'], session.attributes['spanish_word'])


def increment_success(flashcard_id):
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            database_access.increment_card_success(cursor, flashcard_id)



def increment_failure(flashcard_id):
    connection = database_access.get_connection()
    with connection:
        with connection.cursor() as cursor:
            database_access.increment_card_failure(cursor, flashcard_id)


if __name__ == "__main__":
    app.run(debug=True)
