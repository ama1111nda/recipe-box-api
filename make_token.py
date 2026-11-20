import jwt

JWT_SECRET = "dev-secret-change-me"  # must match app.config["JWT_SECRET"]

def make_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),  # 👈 make sub a string
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

if __name__ == "__main__":
    token = make_token(1)  
    print(token)