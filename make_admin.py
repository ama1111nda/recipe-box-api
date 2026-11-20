import sqlite3

connection = sqlite3.connect("recipes.db")
cursor = connection.cursor()

username = "amanda"  # this is the user you’re making admin

cursor.execute(
    "UPDATE users SET role = 'admin' WHERE username = ?",
    (username,),
)
connection.commit()

print(f"Updated role to admin for username={username}")
connection.close()