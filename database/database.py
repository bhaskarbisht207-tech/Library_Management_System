import sqlite3, hashlib, secrets
from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent.parent
DATA_DIR=BASE_DIR/"data"
DB_PATH=DATA_DIR/"library.db"

class Database:
    def __init__(self,db_path=DB_PATH):
        DATA_DIR.mkdir(exist_ok=True)
        self.conn=sqlite3.connect(str(db_path),timeout=15)
        self.conn.row_factory=sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.initialize()

    def execute(self,sql,params=()):
        cur=self.conn.execute(sql,params); self.conn.commit(); return cur
    def executemany(self, sql, rows):
        """Run a bulk write atomically: all rows commit, or none do."""
        try:
            with self.conn:
                return self.conn.executemany(sql, rows)
        except Exception:
            # The connection context rolls back automatically; re-raise for the UI.
            raise
    def fetchone(self,sql,params=()): return self.conn.execute(sql,params).fetchone()
    def fetchall(self,sql,params=()): return self.conn.execute(sql,params).fetchall()

    def initialize(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL UNIQUE,password_hash TEXT NOT NULL,salt TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS books(book_id INTEGER PRIMARY KEY,isbn TEXT NOT NULL UNIQUE,title TEXT NOT NULL,author TEXT NOT NULL,category TEXT NOT NULL,publisher TEXT,year INTEGER,quantity INTEGER NOT NULL CHECK(quantity>=0),available_quantity INTEGER NOT NULL CHECK(available_quantity>=0 AND available_quantity<=quantity));
        CREATE TABLE IF NOT EXISTS members(member_id INTEGER PRIMARY KEY,name TEXT NOT NULL,phone TEXT,email TEXT,course_class TEXT,registration_date TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS transactions(transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,book_id INTEGER NOT NULL,member_id INTEGER NOT NULL,issue_date TEXT NOT NULL,due_date TEXT NOT NULL,return_date TEXT,status TEXT NOT NULL CHECK(status IN ('Issued','Returned')),FOREIGN KEY(book_id) REFERENCES books(book_id) ON DELETE RESTRICT,FOREIGN KEY(member_id) REFERENCES members(member_id) ON DELETE RESTRICT);
        DROP INDEX IF EXISTS idx_books_isbn;
        CREATE INDEX IF NOT EXISTS idx_books_title ON books(title COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_books_author ON books(author COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_books_category ON books(category COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_books_available ON books(available_quantity);
        CREATE INDEX IF NOT EXISTS idx_members_name ON members(name COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_members_email ON members(email COLLATE NOCASE);
        CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
        CREATE INDEX IF NOT EXISTS idx_transactions_due_date ON transactions(due_date);
        CREATE INDEX IF NOT EXISTS idx_transactions_issue_date ON transactions(issue_date);
        CREATE INDEX IF NOT EXISTS idx_transactions_status_due ON transactions(status, due_date);
        CREATE INDEX IF NOT EXISTS idx_transactions_book_id ON transactions(book_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_member_id ON transactions(member_id);
        CREATE INDEX IF NOT EXISTS idx_members_phone ON members(phone);
        """)
        self.conn.commit()
        # Let SQLite refresh lightweight planner statistics when useful.
        self.conn.execute("PRAGMA optimize")
        if not self.fetchone("SELECT id FROM users WHERE username=?",("admin",)):
            salt=secrets.token_hex(16); pwd=hashlib.pbkdf2_hmac("sha256",b"admin123",bytes.fromhex(salt),120000).hex()
            self.execute("INSERT INTO users(username,password_hash,salt) VALUES(?,?,?)",("admin",pwd,salt))

    def verify_user(self,username,password):
        row=self.fetchone("SELECT id,username,password_hash,salt FROM users WHERE username=?",(username.strip(),))
        if not row:return None
        candidate=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(row["salt"]),120000).hex()
        return dict(row) if secrets.compare_digest(candidate,row["password_hash"]) else None
    def close(self): self.conn.close()
