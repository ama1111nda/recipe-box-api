# Security Audit – Recipe API

## 1. Safe storage (passwords)

- Passwords are stored as **hashed values**, not plaintext.
- Example from `users` table:
  - `scrypt:32768:8:1$...$...`
- **Risk addressed:** If the database is compromised, attackers do not see raw passwords, only scrypt hashes.

---

## 2. Authentication (identity / tokens)

- Protected routes (e.g. `POST /recipes`, `PUT /recipes/:id`, `DELETE /recipes/:id`) **require a valid JWT**.
- Anonymous request (no `Authorization` header) to a protected route returns **`401 Unauthorized`**.
- **Meaning:** The API correctly demands a valid identity before allowing access to protected actions.

---

## 3. Authorization & ownership

- **Owner test:**
  - Logged in as the recipe owner, calling `PUT/DELETE /recipes/:id` returns **`200`** (or `204`), and the action succeeds.
- **Non-owner test:**
  - Logged in as a different valid user on the *same* recipe ID returns **`403 Forbidden`**.
- **Meaning:** Users cannot modify recipes they do not own; cross-user modifications are blocked.

- **Admin routes:**
  - Not implemented in this version of the API, so there is no separate admin-only surface to audit.

---

## 4. Regression tests (old exploits)

- **Previous exploit:** user A could edit user B’s recipe.
  - **Now:** the same action, using user A’s valid JWT on user B’s recipe, returns **`403 Forbidden`**.
  - **Exploit status:** no longer possible due to ownership checks.
- (Other previous bad requests can be added here if needed, with their new status codes.)

---

## 5. Summary

- **Passwords:** safely stored as scrypt hashes, not plaintext.
- **Authentication:** enforced with JWTs; protected routes return **`401`** on missing identity.
- **Access control:** ownership checks enforced; owner succeeds (`200`/`204`), non-owner gets **`403`**.
- **Old cross-user exploit:** user A editing user B’s recipe is now blocked with **`403 Forbidden`**.