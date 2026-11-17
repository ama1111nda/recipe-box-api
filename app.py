"""Recipe Box API — BE104 course skeleton.

A working Flask + SQLite CRUD API for recipes. It stores data perfectly —
and it trusts everyone. There is no authentication and no authorization yet.
That is the point: you will add both, lesson by lesson, in Units 2 and 3.
"""

import sqlite3
import os
import jwt

from datetime import datetime, timedelta
from flask import Flask, g, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "recipes.db"

app = Flask(__name__)
app.config["JWT_SECRET"] = os.environ.get("JWT_SECRET")

from flask import request, jsonify
from werkzeug.security import check_password_hash

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip() or not isinstance(password, str) or not password.strip():
        return jsonify({"error": "username and password are required"}), 400

    db = get_db()
    user = db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()

    def auth_failed():
        return jsonify({"error": "Invalid credentials"}), 401

    if user is None:
        return auth_failed()

    if not check_password_hash(user["password_hash"], password):
        return auth_failed()

    payload = {
        "sub": str(user["id"]),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    token = jwt.encode(
        payload,
        app.config["JWT_SECRET"],
        algorithm="HS256",
    )

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "token": token,
    }), 200

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def recipe_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "ingredients": row["ingredients"],
        "instructions": row["instructions"],
        "is_public": bool(row["is_public"]),
    }


@app.get("/")
def hello():
    return jsonify({"message": "Recipe Box API", "recipes": "/recipes"})


@app.get("/recipes")
def list_recipes():
    rows = get_db().execute("SELECT * FROM recipes ORDER BY id").fetchall()
    return jsonify([recipe_to_dict(r) for r in rows])


@app.get("/recipes/<int:recipe_id>")
def get_recipe(recipe_id):
    row = get_db().execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    if row is None:
        return jsonify({"error": "recipe not found"}), 404
    return jsonify(recipe_to_dict(row))


@app.post("/recipes")
def create_recipe():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return jsonify({"error": "bearer token is empty"}), 401

    try:
        payload = jwt.decode(
            token,
            app.config["JWT_SECRET"],
            algorithms=["HS256"],
        )
    except jwt.PyJWTError:
        return jsonify({"error": "invalid or expired token"}), 401

    user_id = payload.get("sub")
    if not user_id:
        return jsonify({"error": "token missing sub claim"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid JSON body"}), 400

    title = data.get("title")
    ingredients = data.get("ingredients")
    if not isinstance(title, str) or not title.strip() or not ingredients:
        return jsonify({"error": "title and ingredients are required"}), 400

    instructions = data.get("instructions", "")
    if instructions is None:
        instructions = ""

    raw_public = data.get("is_public", True)
    if isinstance(raw_public, bool):
        is_public = 1 if raw_public else 0
    elif isinstance(raw_public, str) and raw_public.lower() in {"true", "1", "false", "0"}:
        is_public = 1 if raw_public.lower() in {"true", "1"} else 0
    else:
        is_public = 1 if bool(raw_public) else 0

    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO recipes (title, ingredients, instructions, is_public)"
            " VALUES (?, ?, ?, ?)",
            (title.strip(), ingredients, instructions, is_public),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        if "UNIQUE" in str(exc).upper():
            return jsonify({"error": "a recipe with that title already exists"}), 409
        return jsonify({"error": "invalid recipe data"}), 400

    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    return jsonify(recipe_to_dict(row)), 201


@app.patch("/recipes/<int:recipe_id>")
def update_recipe(recipe_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return jsonify({"error": "bearer token is empty"}), 401

    try:
        payload = jwt.decode(
            token,
            app.config["JWT_SECRET"],
            algorithms=["HS256"],
        )
    except jwt.PyJWTError:
        return jsonify({"error": "invalid or expired token"}), 401

    user_id = payload.get("sub")
    if not user_id:
        return jsonify({"error": "token missing sub claim"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "a JSON body is required"}), 400
    fields, values = [], []
    for column in ("title", "ingredients", "instructions"):
        if column in data:
            fields.append(f"{column} = ?")
            values.append(data[column])
    if "is_public" in data:
        fields.append("is_public = ?")
        values.append(1 if data["is_public"] else 0)
    if not fields:
        return jsonify({"error": "nothing to update"}), 400
    values.append(recipe_id)
    db = get_db()
    try:
        cur = db.execute(
            f"UPDATE recipes SET {', '.join(fields)} WHERE id = ?", values
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "a recipe with that title already exists"}), 409
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    row = db.execute(
        "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
    ).fetchone()
    return jsonify(recipe_to_dict(row))


@app.delete("/recipes/<int:recipe_id>")
def delete_recipe(recipe_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "missing or invalid Authorization header"}), 401

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return jsonify({"error": "bearer token is empty"}), 401

    try:
        payload = jwt.decode(
            token,
            app.config["JWT_SECRET"],
            algorithms=["HS256"],
        )
    except jwt.PyJWTError:
        return jsonify({"error": "invalid or expired token"}), 401

    user_id = payload.get("sub")
    if not user_id:
        return jsonify({"error": "token missing sub claim"}), 401

    db = get_db()
    cur = db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "recipe not found"}), 404
    return "", 204

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "username is required"}), 400

    if not isinstance(password, str) or not password.strip():
        return jsonify({"error": "password is required"}), 400

    password_hash = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.strip(), password_hash)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "username already exists"}), 409

    return jsonify({"message": "User registered successfully", "username": username.strip()}), 201

def demo_password_hashing():
    password = "example-password"
    wrong = "wrong-password"

    stored_hash = generate_password_hash(password)
    print("Stored hash:", stored_hash)

    print("Correct password matches:", check_password_hash(stored_hash, password))
    print("Wrong password matches:", check_password_hash(stored_hash, wrong))


if __name__ == "__main__":
    app.run(debug=True)

