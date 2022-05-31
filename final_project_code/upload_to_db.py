import csv
import pymysql

connection = pymysql.connect(host='35.224.158.93',
                             user='root',
                             password='7YD{f}dQ)9yyT#3U',
                             database='flashcards',
                             cursorclass=pymysql.cursors.DictCursor)

with connection:
    with connection.cursor() as cursor:
        # Create a new record

        with open('flashcards.csv') as csvfile:
            csvreader = csv.reader(csvfile)

            for row in csvreader:
                source, translation = row[0], row[1]
                sql = "INSERT INTO `spanish_flashcards` (`source`, `translation`) VALUES (%s, %s)"
                cursor.execute(sql, (source, translation))
                print(source, translation)