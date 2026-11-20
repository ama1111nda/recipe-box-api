import sqlite3

connection = sqlite3.connect("recipes.db")
cursor = connection.cursor()

cursor.execute("ALTER TABLE recipes ADD COLUMN owner_id INTEGER;")
connection.commit()

for row in cursor.execute("PRAGMA table_info(recipes);"):
    print(row)

connection.close()