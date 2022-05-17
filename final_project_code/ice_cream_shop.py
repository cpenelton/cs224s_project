import csv
import logging
import random
from datetime import datetime
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session, request

FLASHCARDS_FILENAME = "flashcards.csv"
render_question_template = lambda x, *args: question(render_template(x, *args))


### Intents

@ask.launch
def new_session():
    return render_question_template('login')


@ask.intent("LoginIntent", convert={"username": str})
def login(username):
    session.attributes['flashcards'] = get_flashcards(username)
    session.attribute['successes'] = get_statistics(username)

    return render_question_template('welcome')


@ask.intent("AddFlashcardIntent", convert={"english_word": str, "spanish_word": str})
def add_flashcard(english_word, spanish_word):
    return render_question_template('add_flashcard')


@ask.intent("AskQuestionIntent")
def ask_question():
    current_card = get_flashcard()
    session.attribute['current_card'] = current_card

    return render_question_template('test_vocab', spanish_word=current_card[1])


@ask.intent("AnswerQuestionIntent", convert={"answer": str})
def answer_question(answer):
    current_card = session.attribute['current_card']

    if current_card == None:
        return render_question_template('no_question')

    if answer != current_card:
        increment_failure(current_card)
        return render_question_template('wrong_answer',
                                        spanish_word=current_card[1],
                                        english_word=current_card[0])
    else:
        increment_success(current_card)
        return render_question_template('correct_answer')


@ask.intent("AMAZON.FallbackIntent")
def fallback():
    return render_question_template('clarify')


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

    for key in session.attributes['flashcards'].keys:
        statistics[key] = {
            'successes': 0,
            'failures': 0,
            'last_time_seen' = datetime.max()
        }

        return statistics

    # TODO: Weigh cards by success/failure rate
    def get_flashcard():
        english_word = random.choice(list(session.attributes['flashcards']))
        spanish_word = session.attributes['flashcards'][english_word]

        return (english_word, spanish_word)

    def increment_success(flashcard):
        session.attributes['statistics'][flashcard]['success'] += 1
        session.attributes['statistics'][flashcard]['last_time_seen'] = datetime.now()

    def increment_failure(flashcard):
        session.attributes['statistics'][flashcard]['failure'] += 1
        session.attributes['statistics'][flashcard]['last_time_seen'] = datetime.now()

    if __name__ == "__main__":
        app = Flask(__name__)
        ask = Ask(app, "/")

        logging.getLogger("flask_ask").setLevel(logging.DEBUG)