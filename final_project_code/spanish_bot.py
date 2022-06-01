import csv
import logging
import random
from datetime import datetime
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session, request

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

    session.attributes['user'] = username

    if username not in USERS:
        template_welcome = 'new_user_welcome'
        session.attributes['flashcards'] = initialize_flashcards(username)
        session.attributes['statistics'] = initialize_statistics(username)
    else:
        template_welcome = 'old_user_welcome'
        session.attributes['flashcards'] = get_flashcards(username)
        session.attributes['statistics'] = get_statistics(username)
        # TODO: give a summary of progress if an old user
    return question(render_template(template_welcome, username=username))


@ask.intent("SetLearningPrefsIntent", convert={"practice_cadence": int})
def set_learning_prefs(practice_cadence):
    session.attributes['practice_cadence'] = practice_cadence
    return question(render_template("user_preference_confirmation", practice_cadence=practice_cadence))


@ask.intent("AddFlashcardIntent", convert={"english_word": str, "spanish_word": str})
def add_flashcard(english_word, spanish_word):
    # TODO: TEST THIS functionality to add a flashcard to deck
    session.attributes['flashcards'][english_word] = [spanish_word]
    return question(render_template('add_flashcard_complete'))


@ask.intent("AskMenuIntent")
def return_menu():
    return question(render_template('return_menu_options'))


@ask.intent("AskEnglishQuestionIntent")
def ask_english_question():
    current_card = get_flashcard()
    session.attributes['current_card'] = current_card
    return question(render_template('test_vocab', spanish_word=current_card[1]))


@ask.intent("AskSpanishQuestionIntent")
def ask_spanish_question():
    current_card = get_flashcard()
    session.attributes['current_card'] = current_card
    return question(render_template('test_spanish_vocab', english_word=current_card[0]))


@ask.intent("AnswerQuestionEnglishIntent", convert={"answer_english": str})
def answer_question_english(answer_english):
    current_card = session.attributes['current_card']

    if current_card[0] == None:
        return question(render_template('no_question'))

    if answer_english != current_card[0]:
        increment_failure(current_card[0])
        return question(render_template('wrong_answer',
                                        spanish_word=current_card[1],
                                        english_word=current_card[0]))
    else:
        increment_success(current_card[0])
        return question(render_template('correct_answer'))


@ask.intent("AnswerQuestionSpanishIntent", convert={"answer_spanish": str})
def answer_question_spanish(answer_spanish):
    current_card = session.attributes['current_card']

    if current_card[0] == None:
        return question(render_template('no_question'))

    if answer_spanish != current_card[1]:
        print("SPANISH ANSWER: ", answer_spanish)
        increment_failure(current_card[0])
        return question(render_template('wrong_answer',
                                        spanish_word=current_card[1],
                                        english_word=current_card[0]))
    else:
        increment_success(current_card[0])
        return question(render_template('correct_answer'))


@ask.intent("AMAZON.FallbackIntent")
def fallback():
    return question(render_template('clarify'))


### Helper functions

def initialize_flashcards(username):
    filename = FLASHCARDS_FILENAME
    flashcards = {}

    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            flashcards[row[0]] = row[1]
    return flashcards


def initialize_statistics(username):
    statistics = {}

    for key in session.attributes['flashcards']:
        statistics[key] = {
            'successes': 0,
            'failures': 0,
            'last_time_seen': str(datetime.max)
        }
    return statistics


# TODO: Get flashcards by username
def get_flashcards(username):
    flashcards = {}
    # TODO: pull data from database system
    return flashcards


# TODO: get statistics by username
def get_statistics(username):
    statistics = {}
    # TODO: pull data from database system
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
