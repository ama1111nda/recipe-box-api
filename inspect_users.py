import sqlite3

connection = sqlite3.connect("recipes.db")
cursor = connection.cursor()

for row in cursor.execute("SELECT id, username FROM users;"):
    print(row)

connection.close()