from datetime import date

class TransactionModel:
    def __init__(self, db): self.db=db

    def issue(self, book_id, member_id, due_date):
        conn=self.db.conn
        try:
            conn.execute("BEGIN IMMEDIATE")
            book=conn.execute("SELECT available_quantity FROM books WHERE book_id=?",(book_id,)).fetchone()
            member=conn.execute("SELECT member_id FROM members WHERE member_id=?",(member_id,)).fetchone()
            if not book: raise ValueError("Book ID does not exist.")
            if not member: raise ValueError("Member ID does not exist.")
            if book["available_quantity"]<=0: raise ValueError("No available copies of this book.")
            if due_date < date.today().isoformat(): raise ValueError("Due date cannot be before today.")
            conn.execute("INSERT INTO transactions(book_id,member_id,issue_date,due_date,status) VALUES(?,?,?,?, 'Issued')",(book_id,member_id,date.today().isoformat(),due_date))
            conn.execute("UPDATE books SET available_quantity=available_quantity-1 WHERE book_id=? AND available_quantity>0",(book_id,))
            conn.commit()
        except Exception:
            conn.rollback(); raise

    def return_book(self, transaction_id):
        conn=self.db.conn
        try:
            conn.execute("BEGIN IMMEDIATE")
            tx=conn.execute("SELECT book_id,status,due_date FROM transactions WHERE transaction_id=?",(transaction_id,)).fetchone()
            if not tx: raise ValueError("Transaction ID does not exist.")
            if tx["status"]=="Returned": raise ValueError("This transaction has already been returned.")
            conn.execute("UPDATE transactions SET status='Returned',return_date=? WHERE transaction_id=?",(date.today().isoformat(),transaction_id))
            conn.execute("UPDATE books SET available_quantity=MIN(quantity,available_quantity+1) WHERE book_id=?",(tx["book_id"],))
            conn.commit()
            return tx["due_date"] < date.today().isoformat()
        except Exception:
            conn.rollback(); raise

    def issued(self, search="", limit=100, offset=0):
        clauses=["t.status='Issued'"]; params=[]
        if search:
            q=f"%{search.strip()}%"; clauses.append("(CAST(t.transaction_id AS TEXT) LIKE ? OR CAST(t.book_id AS TEXT) LIKE ? OR CAST(t.member_id AS TEXT) LIKE ? OR b.title LIKE ? COLLATE NOCASE OR m.name LIKE ? COLLATE NOCASE)"); params += [q,q,q,q,q]
        where=" AND ".join(clauses)
        return self.db.fetchall(f"""SELECT t.transaction_id,t.book_id,b.title,t.member_id,m.name,t.issue_date,t.due_date,t.status
            FROM transactions t JOIN books b ON b.book_id=t.book_id JOIN members m ON m.member_id=t.member_id
            WHERE {where} ORDER BY t.due_date ASC,t.transaction_id DESC LIMIT ? OFFSET ?""",params+[limit,offset])

    def recent(self,limit=8):
        return self.db.fetchall("""SELECT t.transaction_id,b.title,m.name,t.issue_date,t.due_date,t.status
            FROM transactions t JOIN books b ON b.book_id=t.book_id JOIN members m ON m.member_id=t.member_id
            ORDER BY t.transaction_id DESC LIMIT ?""",(limit,))
