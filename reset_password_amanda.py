import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("recipes.db")
cursor = connection.cursor()

username = "amanda"
new_password = "TempPass123!"  # you can change this if you like

password_hash = generate_password_hash(new_password)

cursor.execute(
    "UPDATE users SET password_hash = ? WHERE username = ?",
    (password_hash, username),
)
connection.commit()

print(f"Password reset for {username}. New password is: {new_password}")
connection.close()