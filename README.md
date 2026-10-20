# Library Management System

A complete B.Tech desktop project built with **Python 3, CustomTkinter and SQLite**. The main quality goal is **Improve Performance**.

## Features
- Secure college-level admin login using PBKDF2-HMAC-SHA256 password hashing.
- Dashboard with total books, available copies, issued books, members and overdue books.
- Book CRUD, category filtering, multi-field search with a short debounce, and pagination.
- Member CRUD, debounced multi-field search and pagination.
- Issue and return workflow with atomic SQLite transactions and automatic quantity updates.
- Overdue detection based on due date.
- Bulk CSV book import with validation, mixed-case/space-tolerant headers, duplicate protection and atomic `executemany()`.
- Optimized reports with search debounce, date filters, sorting, 100-row pagination, and full-result CSV export.
- Dark modern UI with responsive tables and vertical/horizontal scrollbars.
- SQLite indexes (including transaction status/date and foreign-key lookup indexes), foreign keys, UNIQUE constraints, parameterized queries, WAL and minimal result sets.

## Installation
1. Install Python 3.10+.
2. Open a terminal inside this project folder.
3. Run `pip install -r requirements.txt`.
4. Run `python main.py`.

## Default login
- Username: `admin`
- Password: `admin123`

Change the password implementation if this project is ever deployed outside a college/demo environment.

## Database
The database is automatically created at `data/library.db`.

Tables:
- `users`: admin credentials.
- `books`: ISBN, title, author, category, quantity and available quantity.
- `members`: member profile and registration date.
- `transactions`: issue/return history with foreign keys.

## Performance improvements
1. Frequently searched columns have SQLite indexes.
2. Book/member screens use LIMIT/OFFSET pagination rather than loading every row.
3. CSV import uses one atomic bulk `executemany()` call and a single commit; if a database constraint fails, the bulk operation rolls back instead of leaving partial records.
4. Issue/return uses an atomic transaction to keep book quantity and transaction status consistent.
5. Queries select only required columns instead of `SELECT *`.
6. Dashboard uses compact aggregate queries.
7. SQLite WAL mode and `synchronous=NORMAL` improve normal desktop concurrency/performance.
8. Search requests are debounced and list screens fetch only the current page.
9. Reports count matching records in SQLite, render 100 rows at a time, and export the complete filtered result set when requested.
10. Dashboard auto-refresh keeps one scheduled callback instead of accumulating duplicate timers.
11. `PRAGMA optimize` lets SQLite refresh query-planner statistics when useful.

## CSV format
Required headers:
`book_id,isbn,title,author,category,publisher,year,quantity`

See `sample_data/books.csv`.

## Viva points
**Why SQLite?** Lightweight, serverless and ideal for a desktop application.

**Why indexes?** They reduce the work SQLite needs to do for frequently searched/filter columns.

**Why pagination?** Only a small page is rendered, so a large library does not overload the GUI.

**Why `executemany()`?** It performs bulk inserts efficiently instead of opening/committing for every row.

**Why parameterized SQL?** It prevents SQL injection and safely handles user input.

**Why database transactions for issue/return?** Book quantity and transaction history must change together. If one step fails, both changes are rolled back.

## UI notes
- Books and Members tables use a compact fixed row count so action buttons remain visible instead of being pushed below the window.
- Search controls include clear labels and descriptive placeholders.
- Dashboard labels distinguish **Book Titles**, **Available Copies**, and **Issued Copies** to avoid confusing title count with physical copy count.
- Tables use fixed column widths with scrollbars for predictable resizing and readable data.

## Regression tests
Run the built-in database/performance checks from the project folder:

```bash
python -m unittest discover -s tests -v
```

The tests cover paginated search queries, issue/return stock consistency, atomic bulk insert rollback, and the required performance indexes.
