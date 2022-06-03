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
    source varchar(255) NOT NULL,
    translation varchar(255) NOT NULL,
    n int NOT NULL,
    ef float NOT NULL,
    i int NOT NULL,
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

def drop_table(table):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "DROP TABLE IF EXISTS " + table
            cursor.execute(sql)

def reset_db():
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            drop_table("flashcards")
            drop_table("users")
            cursor.execute(create_user_settings_table)
            cursor.execute(create_flashcards_table)
    

## GETS

def get_user(user_id):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id = %s"
            cursor.execute(sql, (user_id))
            user = cursor.fetchone()
            return user

def get_user_by_name(name):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE name = %s"
            cursor.execute(sql, (name))
            user = cursor.fetchone()
            print("THE USER HERE IS", user)
            return user

def get_flashcard(flashcard_id):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM flashcards WHERE id = %s"
            cursor.execute(sql, (flashcard_id))
            flashcard = cursor.fetchone()
            return flashcard

def get_flashcard_by_user_source(user_id, source):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM flashcards WHERE user_id = %s AND source = %s"
            cursor.execute(sql, (user_id, source))
            flashcard = cursor.fetchone()
            return flashcard

def get_all_flashcards_for_users(user_id):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            user = get_user(user_id)
            size = int(user['number_of_cards'])

            sql = "SELECT * FROM flashcards WHERE user_id = %s"
            cursor.execute(sql, (user_id))
            flashcards = cursor.fetchall()
            return flashcards

## INSERTS

def insert_csv_into_flashcards(user_id, file):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            with open(file) as csvfile:
                csvreader = csv.reader(csvfile)

                for row in csvreader:
                    source, translation = row[0], row[1]
                    insert_card(user_id, source, translation)

def insert_card(user_id, source, translation):
    sql = """INSERT INTO `flashcards`
        (`user_id`,
        `source`,
        `translation`,
        `n`,
        `ef`,
        `i`
        )
        VALUES (%s, %s, %s, %s, %s, %s)"""
    
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (user_id, source, translation, 0, 2.5, 0))
            print(user_id, source, translation)
            connection.commit()
    

def insert_user(name, number_of_cards):
    sql = """INSERT INTO `users`
        (`name`,
        `number_of_cards`,
        `last_login_time`,
        `times_logged_in`,
        `total_successes`,
        `total_failures`)
        VALUES (%s, %s, %s, %s, %s, %s)"""
    
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            timestamp = get_current_timestamp()
            cursor.execute(sql, (name, number_of_cards, timestamp, 0, 0, 0))
            print(name, number_of_cards)
            connection.commit()

# UPDATES
def set_sm_2_vals(flashcard_id, n, ef, i):
    sql = """UPDATE `flashcards`
            SET n=%s, ef=%s, i=%s
            WHERE id = %s"""

    print(n, ef, i, flashcard_id)

    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            flashcard = cursor.execute(sql, (n, ef, i, flashcard_id))
            connection.commit()
            
            return flashcard

def set_user_failures(user_id, failures):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "UPDATE `users` SET total_failures= %s WHERE id = %s"
            flashcard = cursor.execute(sql, (failures, user_id))
            connection.commit()

            return flashcard

def set_user_successes(user_id, successes):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "UPDATE `users` SET total_successes= %s WHERE id = %s"
            flashcard = cursor.execute(sql, (successes, user_id))
            connection.commit()

            return flashcard

def set_user_card_number(user_id, card_number):
    connection = get_connection()
    with connection:
        with connection.cursor() as cursor:
            sql = "UPDATE `users` SET number_of_cards= %s WHERE id = %s"
            flashcard = cursor.execute(sql, (card_number, user_id))
            connection.commit()

            return flashcard

if __name__ == '__main__':

    set_sm_2_vals(1, 2, 3, 8)
    # reset_db()
    # name = "Missingno"
    # insert_user(name, 20)

    # user = get_user_by_name(name)
    # user_id = user['id']
    # print(user['id'])

    # insert_csv_into_flashcards(user_id, "small_flashcards.csv")

    # print(name + "'s cards:")
    # print(user)
    # print(get_all_flashcards_for_users(user_id))
    # print("\n\n\n")

    # connection = get_connection()
    # with connection:
    #     with connection.cursor() as cursor:
    #         sql = "SELECT * FROM users"
    #         cursor.execute(sql)
    #         print(cursor.fetchall())