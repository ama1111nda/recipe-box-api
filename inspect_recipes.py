import sqlite3

conn = sqlite3.connect("recipes.db")
cur = conn.cursor()
for row in cur.execute("SELECT id, title, owner_id FROM recipes ORDER BY id DESC LIMIT 5;"):
    print(row)
conn.close()