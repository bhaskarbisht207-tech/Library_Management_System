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

    def test_admin_login_password_verification(self):
        self.assertIsNotNone(self.db.verify_user("admin", "admin123"))
        self.assertIsNone(self.db.verify_user("admin", "wrong-password"))

    def test_database_uses_foreign_key_constraints(self):
        result = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(result[0], 1)


    def test_foreign_keys_are_enabled(self):
        result = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(result[0], 1)

    def test_admin_login_password_verification(self):
        self.assertIsNotNone(self.db.verify_user("admin", "admin123"))
        self.assertIsNone(self.db.verify_user("admin", "wrong-password"))

    def test_database_uses_foreign_key_constraints(self):
        result = self.db.fetchone("PRAGMA foreign_keys")
        self.assertEqual(result[0], 1)


    def test_login_rejects_unknown_username(self):
        self.assertIsNone(self.db.verify_user("not-a-user", "admin123"))

    def test_login_trims_username_whitespace(self):
        self.assertIsNotNone(self.db.verify_user(" admin ", "admin123"))

    def test_empty_book_search_count(self):
        self.add_book(1, "ISBN-1", 1)
        self.add_book(2, "ISBN-2", 1)
        self.assertEqual(self.books.count(""), 2)

    def test_book_search_is_case_insensitive(self):
        self.add_book()
        self.assertEqual(self.books.count("python book"), 1)

    def test_book_category_filter_is_case_insensitive(self):
        self.add_book()
        self.assertEqual(self.books.count("", category="programming"), 1)

    def test_book_categories_are_sorted(self):
        self.books.add([1, "ISBN-1", "Z Book", "Author", "Zoology", "Press", 2024, 1, 1])
        self.books.add([2, "ISBN-2", "A Book", "Author", "Biology", "Press", 2024, 1, 1])
        self.assertEqual(self.books.categories(), ["Biology", "Zoology"])

    def test_missing_book_lookup_returns_none(self):
        self.assertIsNone(self.books.get(999))

    def test_book_delete_removes_record(self):
        self.add_book()
        self.books.delete(1)
        self.assertIsNone(self.books.get(1))

    def test_member_add_and_get_round_trip(self):
        self.add_member(7)
        row = self.members.get(7)
        self.assertEqual(row["name"], "Test Member")
        self.assertEqual(row["member_id"], 7)

    def test_member_search_is_case_insensitive(self):
        self.add_member()
        self.assertEqual(len(self.members.list("test member")), 1)

    def test_member_count_matches_search(self):
        self.add_member(1)
        self.members.add([2, "Different Person", "9999999999", "other@example.com", "BTech", date.today().isoformat()])
        self.assertEqual(self.members.count("Test Member"), 1)

    def test_member_pagination_respects_limit(self):
        for i in range(1, 5):
            self.add_member(i)
        self.assertEqual(len(self.members.list(limit=2, offset=1)), 2)

    def test_missing_member_lookup_returns_none(self):
        self.assertIsNone(self.members.get(999))

    def test_issue_missing_book_does_not_create_transaction(self):
        self.add_member()
        with self.assertRaises(ValueError):
            self.transactions.issue(999, 1, (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS n FROM transactions")["n"], 0)

    def test_issue_missing_member_preserves_stock(self):
        self.add_book()
        with self.assertRaises(ValueError):
            self.transactions.issue(1, 999, (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.books.get(1)["available_quantity"], 3)

    def test_issue_rejects_past_due_date(self):
        self.add_book()
        self.add_member()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.transactions.issue(1, 1, yesterday)
        self.assertEqual(self.books.get(1)["available_quantity"], 3)

    def test_issue_rejects_zero_available_stock(self):
        self.add_book(quantity=0)
        self.add_member()
        with self.assertRaises(ValueError):
            self.transactions.issue(1, 1, (date.today() + timedelta(days=7)).isoformat())
        self.assertEqual(self.db.fetchone("SELECT COUNT(*) AS n FROM transactions")["n"], 0)

    def test_second_return_is_rejected(self):
        self.add_book()
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        self.transactions.issue(1, 1, due)
        self.transactions.return_book(1)
        with self.assertRaises(ValueError):
            self.transactions.return_book(1)
        self.assertEqual(self.books.get(1)["available_quantity"], 3)

    def test_issued_list_excludes_returned_transactions(self):
        self.add_book(quantity=3)
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        self.transactions.issue(1, 1, due)
        self.transactions.return_book(1)
        self.transactions.issue(1, 1, due)
        rows = self.transactions.issued()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "Issued")

    def test_recent_transactions_respects_limit(self):
        self.add_book(quantity=3)
        self.add_member()
        due = (date.today() + timedelta(days=7)).isoformat()
        for _ in range(3):
            self.transactions.issue(1, 1, due)
        self.assertEqual(len(self.transactions.recent(limit=2)), 2)

    def test_database_journal_mode_is_wal(self):
        self.assertEqual(str(self.db.fetchone("PRAGMA journal_mode")[0]).lower(), "wal")
if __name__ == "__main__":
    unittest.main(verbosity=2)























