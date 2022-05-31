import pymysql
import csv
import datetime
import time

create_user_settings_table = """CREATE TABLE users 
    (id int NOT NULL AUTO_INCREMENT,
    name varchar(255) NOT NULL UNIQUE,
    number_of_cards int,
    last_login_time datetime NOT NULL,
    times_logged_in int NOT NULL,
    total_successes int NOT NULL,
    total_failures int NOT NULL,
    PRIMARY KEY (id)
)"""

create_flashcards_table = """CREATE TABLE flashcards
    (id int NOT NULL AUTO_INCREMENT,
    user_id int NOT NULL,
    source varchar(255) NOT NULL UNIQUE,
    translation varchar(255) NOT NULL,
    successes int NOT NULL,
    failures int NOT NULL,
    last_time_seen timestamp NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)"""

## DB FUNCTIONS

def get_connection():
    connection = pymysql.connect(host='35.224.158.93',
        user='root',
        password='7YD{f}dQ)9yyT#3U',
        database='flashcards',
        cursorclass=pymysql.cursors.DictCursor)
    
    return connection

def get_current_timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def drop_table(cursor, table):
    sql = "DROP TABLE IF EXISTS " + table
    cursor.execute(sql)

def reset_db(cursor):
    drop_table("flashcards")
    drop_table("users")
    cursor.execute(create_user_settings_table)
    cursor.execute(create_flashcards_table)    

## GETS

def get_user(cursor, user_id):
    sql = "SELECT * FROM users WHERE id = %s"
    cursor.execute(sql, (user_id))
    user = cursor.fetchone()
    return user

def get_user_by_name(cursor, name):
    sql = "SELECT * FROM users WHERE name = %s"
    cursor.execute(sql, (name))
    user = cursor.fetchone()
    return user

def get_flashcard(cursor, flashcard_id):
    sql = "SELECT * FROM flashcards WHERE id = %s"
    cursor.execute(sql, (flashcard_id))
    flashcard = cursor.fetchone()
    return flashcard

def get_flashcard_by_user_source(cursor, user_id, source):
    sql = "SELECT * FROM flashcards WHERE user_id = %s AND source = %s"
    cursor.execute(sql, (user_id, source))
    flashcard = cursor.fetchone()
    return flashcard

def get_all_flashcards_for_users(cursor, user_id):
    user = get_user(cursor, user_id)
    size = int(user['number_of_cards'])

    sql = "SELECT * FROM flashcards WHERE user_id = %s"
    cursor.execute(sql, (user_id))
    flashcards = cursor.fetchmany(size=size)
    return flashcards

## INSERTS

def insert_csv_into_flashcards(cursor, user_id, file):
     with open(file) as csvfile:
        csvreader = csv.reader(csvfile)

        for row in csvreader:
            source, translation = row[0], row[1]
            insert_card(cursor, user_id, source, translation)

def insert_card(cursor, user_id, source, translation):
    sql = """INSERT INTO `flashcards`
        (`user_id`,
        `source`,
        `translation`,
        `successes`,
        `failures`,
        `last_time_seen`
        )
        VALUES (%s, %s, %s, %s, %s, %s)"""
    
    timestamp = get_current_timestamp()
    cursor.execute(sql, (user_id, source, translation, 0, 0, timestamp))
    print(user_id, source, translation)

def insert_user(cursor, name, number_of_cards):
    sql = """INSERT INTO `users`
        (`name`,
        `number_of_cards`,
        `last_login_time`,
        `times_logged_in`,
        `total_successes`,
        `total_failures`)
        VALUES (%s, %s, %s, %s, %s, %s)"""
    
    timestamp = get_current_timestamp()
    cursor.execute(sql, (name, number_of_cards, timestamp, 0, 0, 0))
    print(name, number_of_cards)

# UPDATES
def increment_card_success(cursor, flashcard_id):
    sql = "UPDATE `flashcards` SET `successes` = `successes` + 1 WHERE id = %s"
    flashcard = cursor.execute(sql, (flashcard_id))
    return flashcard

def increment_card_failure(cursor, flashcard_id):
    sql = "UPDATE `flashcards` SET `failures` = `failures` + 1 WHERE id = %s"
    flashcard = cursor.execute(sql, (flashcard_id))
    return flashcard

def set_user_failures(cursor, user_id, failures):
    sql = "UPDATE `users` SET `total_failures` = %s WHERE id = %s"
    flashcard = cursor.execute(sql, (failures, user_id))
    return flashcard

def set_user_successes(cursor, user_id, successes):
    sql = "UPDATE `users` SET `total_successes` = %s WHERE id = %s"
    flashcard = cursor.execute(sql, (successes, user_id))
    return flashcard

def set_user_card_number(cursor, user_id, card_number):
    sql = "UPDATE `users` SET `number_of_cards` = %s WHERE id = %s"
    flashcard = cursor.execute(sql, (card_number, user_id))
    return flashcard

if __name__ == '__main__':
    name = "Daniel"
    connection = get_connection()

    with connection:
        with connection.cursor() as cursor:

            ## SANITY CHECKS ##

            reset_db(cursor)
            insert_user(cursor, name, 20)
            insert_csv_into_flashcards(cursor, 1, "small_flashcards.csv")

            user = get_user_by_name(cursor, name)
            user_id = user['id']

            print(name + "'s cards:")
            print(user)
            print(get_all_flashcards_for_users(cursor, user_id))
            print("\n\n\n")


            flashcard = get_flashcard_by_user_source(cursor, user_id, 'temperature')
            flashcard_id = flashcard['id']

            print("Before update:")
            print(flashcard)
            
            increment_card_success(cursor, flashcard_id)
            increment_card_failure(cursor, flashcard_id)

            print("After update:")
            print(get_flashcard_by_user_source(cursor, user_id, 'temperature'))
            print("\n\n\n")
            

            print("Before user update:")
            print(get_user(cursor, user_id))
            
            set_user_failures(cursor, user_id, 100)
            set_user_successes(cursor, user_id, 100)

            print("After user update:")
            print(get_user(cursor, user_id))
