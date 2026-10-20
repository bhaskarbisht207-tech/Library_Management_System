"""Lightweight regression tests for Q02 performance and data integrity."""
import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta

from database.database import Database
from models.book import BookModel
from models.member import MemberModel
from models.transaction import TransactionModel


class PerformanceRegressionTests(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        self.db = Database(self.db_path)
        self.books = BookModel(self.db)
        self.members = MemberModel(self.db)
        self.transactions = TransactionModel(self.db)

    def tearDown(self):
        self.db.close()
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(self.db_path + suffix)
            except FileNotFoundError:
                pass

    def add_book(self, book_id=1, isbn="ISBN-1", quantity=3):
        self.books.add([
            book_id, isbn, f"Python Book {book_id}", "Test Author",
            "Programming", "Test Publisher", 2024, quantity, quantity,
        ])

    def add_member(self, member_id=1):
        self.members.add([
            member_id, "Test Member", "1234567890", "test@example.com",
            "BTech", date.today().isoformat(),
        ])

    def test_search_and_pagination_queries(self):
        for i in range(1, 31):
            self.add_book(i, f"ISBN-{i}", 1)
        self.assertEqual(self.books.count("Python Book"), 30)
        self.assertEqual(len(self.books.list("Python Book", limit=10, offset=10)), 10)
        self.assertEqual(self.books.list("ISBN-12")[0]["book_id"], 12)

    def test_issue_and_return_keep_stock_consistent(self):
        self.add_book()
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        self.transactions.issue(1, 1, due)
        self.assertEqual(self.books.get(1)["available_quantity"], 2)
        self.transactions.return_book(1)
        self.assertEqual(self.books.get(1)["available_quantity"], 3)

    def test_bulk_insert_rolls_back_on_duplicate_isbn(self):
        self.add_book()
        rows = [
            (2, "ISBN-2", "Second", "Author", "Programming", "Press", 2024, 1, 1),
            (3, "ISBN-1", "Duplicate", "Author", "Programming", "Press", 2024, 1, 1),
        ]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.executemany(
                "INSERT INTO books(book_id,isbn,title,author,category,publisher,year,quantity,available_quantity) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                rows,
            )
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS n FROM books")["n"], 1)

    def test_performance_indexes_exist(self):
        names = {
            row["name"]
            for row in self.db.fetchall("SELECT name FROM sqlite_master WHERE type='index'")
        }
        self.assertTrue({
            "idx_transactions_status_due",
            "idx_transactions_book_id",
            "idx_transactions_member_id",
            "idx_members_phone",
        }.issubset(names))



    def test_foreign_keys_are_enabled(self):
        result = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(result[0], 1)

    def test_admin_login_password_verification(self):
        self.assertIsNotNone(self.db.verify_user("admin", "admin123"))
        self.assertIsNone(self.db.verify_user("admin", "wrong-password"))

    def test_database_uses_foreign_key_constraints(self):
        result = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(result[0], 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)

