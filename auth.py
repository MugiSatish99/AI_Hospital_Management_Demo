import sqlite3

# ================= LOGIN (UNCHANGED)
def login_user(username, password):
    conn = sqlite3.connect("hospital.db", timeout=10)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()

    conn.close()
    return user


# ================= ADD USER (FIX ADDED)
def add_user(username, password, role="patient"):
    try:
        conn = sqlite3.connect("hospital.db", timeout=10)
        c = conn.cursor()

        c.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, (username, password, role))

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        print("Add User Error:", e)
        return False