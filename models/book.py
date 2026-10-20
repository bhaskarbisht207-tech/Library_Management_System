class BookModel:
    def __init__(self, db):
        self.db = db

    def list(self, search="", category="All", limit=25, offset=0):
        clauses, params = [], []
        search = search.strip()
        if search:
            # Prefix matches on ID/ISBN and substring matches on human-readable fields.
            clauses.append("(CAST(book_id AS TEXT) LIKE ? OR isbn LIKE ? OR title LIKE ? COLLATE NOCASE OR author LIKE ? COLLATE NOCASE OR category LIKE ? COLLATE NOCASE)")
            params.extend([f"{search}%", f"{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        if category and category != "All":
            clauses.append("category = ? COLLATE NOCASE")
            params.append(category)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        return self.db.fetchall(f"""SELECT book_id,isbn,title,author,category,publisher,year,quantity,available_quantity
            FROM books{where} ORDER BY title COLLATE NOCASE, book_id LIMIT ? OFFSET ?""", params + [limit, offset])

    def count(self, search="", category="All"):
        clauses, params = [], []
        search = search.strip()
        if search:
            clauses.append("(CAST(book_id AS TEXT) LIKE ? OR isbn LIKE ? OR title LIKE ? COLLATE NOCASE OR author LIKE ? COLLATE NOCASE OR category LIKE ? COLLATE NOCASE)")
            params.extend([f"{search}%", f"{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        if category and category != "All":
            clauses.append("category = ? COLLATE NOCASE")
            params.append(category)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        return self.db.fetchone(f"SELECT COUNT(*) AS n FROM books{where}", params)["n"]

    def categories(self):
        return [r["category"] for r in self.db.fetchall("SELECT DISTINCT category FROM books WHERE category<>'' ORDER BY category COLLATE NOCASE")]

    def add(self, data):
        self.db.execute("""INSERT INTO books(book_id,isbn,title,author,category,publisher,year,quantity,available_quantity)
            VALUES(?,?,?,?,?,?,?,?,?)""", tuple(data))

    def update(self, data):
        self.db.execute("""UPDATE books SET isbn=?,title=?,author=?,category=?,publisher=?,year=?,quantity=?,available_quantity=? WHERE book_id=?""", tuple(data))

    def delete(self, book_id):
        self.db.execute("DELETE FROM books WHERE book_id=?", (book_id,))

    def get(self, book_id):
        return self.db.fetchone("SELECT book_id,isbn,title,author,category,publisher,year,quantity,available_quantity FROM books WHERE book_id=?", (book_id,))
