import customtkinter as ctk
from tkinter import messagebox

from utils.helpers import export_rows
from utils.validators import date_value
from utils.ui import Page, PANEL, MUTED, make_table


PAGE_SIZE = 100


class ReportsView(Page):

    def __init__(self, master, navigate, logout):
        super().__init__(master, navigate, logout, "Reports")

        self.rows = []
        self.headers = []
        self.table_frame = None
        self.tree = None
        self.page = 0
        self.total_rows = 0
        self.export_sql = None
        self.export_params = []
        self._search_after_id = None

        self.build()
        self.load()

    # ---------------------------------------------------------
    # BUILD REPORT PAGE
    # ---------------------------------------------------------

    def build(self):

        top = self.header(
            "Reports",
            "Optimized queries with search, date filters, sorting and CSV export"
        )

        self.button(
            top,
            "Export CSV",
            self.export,
            width=125
        ).pack(side="right")

        # -----------------------------------------------------
        # FILTER PANEL
        # -----------------------------------------------------

        filter_panel = ctk.CTkFrame(
            self.content,
            fg_color=PANEL,
            corner_radius=10
        )

        filter_panel.pack(
            fill="x",
            padx=30,
            pady=(0, 12)
        )

        # Report Type
        self.kind = ctk.CTkComboBox(
            filter_panel,
            values=[
                "All Books",
                "Available Books",
                "Issued Books",
                "Overdue Books",
                "Members",
                "Transactions"
            ],
            width=190,
            height=40,
            command=lambda _: self.load(reset=True)
        )

        self.kind.set("All Books")

        self.kind.pack(
            side="left",
            padx=(12, 5),
            pady=12
        )

        # Search
        self.search = ctk.CTkEntry(
            filter_panel,
            placeholder_text="Search current report...",
            width=250,
            height=40
        )

        self.search.pack(
            side="left",
            padx=5
        )

        self.search.bind(
            "<KeyRelease>",
            lambda _: self.schedule_search()
        )

        # From Date
        self.from_date = ctk.CTkEntry(
            filter_panel,
            placeholder_text="From YYYY-MM-DD",
            width=135,
            height=40
        )

        self.from_date.pack(
            side="left",
            padx=5
        )

        # To Date
        self.to_date = ctk.CTkEntry(
            filter_panel,
            placeholder_text="To YYYY-MM-DD",
            width=135,
            height=40
        )

        self.to_date.pack(
            side="left",
            padx=5
        )

        # Sort
        self.sort = ctk.CTkComboBox(
            filter_panel,
            values=[
                "Default",
                "Date ↑",
                "Date ↓",
                "Title A-Z",
                "Title Z-A"
            ],
            width=130,
            height=40,
            command=lambda _: self.load(reset=True)
        )

        self.sort.set("Default")

        self.sort.pack(
            side="left",
            padx=5
        )

        # Apply date filters explicitly so typing dates does not run a query
        # after every keystroke.
        ctk.CTkButton(
            filter_panel,
            text="Apply",
            width=75,
            height=40,
            command=lambda: self.load(reset=True)
        ).pack(side="left", padx=(6, 4))

        ctk.CTkButton(
            filter_panel,
            text="Clear Filters",
            width=110,
            height=40,
            command=self.clear
        ).pack(side="left", padx=(4, 12))

        # -----------------------------------------------------
        # TABLE HOLDER
        # -----------------------------------------------------

        self.table_holder = ctk.CTkFrame(
            self.content,
            fg_color=PANEL,
            corner_radius=10
        )

        self.table_holder.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 8)
        )

        footer = ctk.CTkFrame(self.content, fg_color="transparent")
        footer.pack(fill="x", padx=30, pady=(0, 18))
        self.page_info = ctk.CTkLabel(footer, text="", text_color=MUTED)
        self.page_info.pack(side="left", padx=8)
        self.button(footer, "Previous", lambda: self.change_page(-1), width=100).pack(side="right", padx=3)
        self.button(footer, "Next", lambda: self.change_page(1), width=100).pack(side="right", padx=3)

    # ---------------------------------------------------------
    # CLEAR FILTERS
    # ---------------------------------------------------------

    def schedule_search(self):
        """Run report search after a short pause instead of on every keystroke."""
        if self._search_after_id is not None:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(220, self._run_scheduled_search)

    def _run_scheduled_search(self):
        self._search_after_id = None
        if self.winfo_exists():
            self.load(reset=True)

    def change_page(self, direction):
        next_page = self.page + direction
        max_page = max(0, (self.total_rows - 1) // PAGE_SIZE)
        if 0 <= next_page <= max_page:
            self.page = next_page
            self.load()

    def clear(self):

        if self._search_after_id is not None:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None

        self.search.delete(0, "end")
        self.from_date.delete(0, "end")
        self.to_date.delete(0, "end")

        self.sort.set("Default")

        self.load(reset=True)

    # ---------------------------------------------------------
    # LOAD REPORT
    # ---------------------------------------------------------

    def load(self, reset=False):

        if reset:
            self.page = 0

        db = self.master.db

        k = self.kind.get()
        q = self.search.get().strip()

        clauses = []
        params = []

        date_col = None

        # -----------------------------------------------------
        # BOOK REPORTS
        # -----------------------------------------------------

        if k in ("All Books", "Available Books"):

            clauses.append("1=1")

            if k == "Available Books":
                clauses.append("b.available_quantity > 0")

            if q:
                clauses.append(
                    """
                    (
                        CAST(b.book_id AS TEXT) LIKE ?
                        OR b.isbn LIKE ?
                        OR b.title LIKE ? COLLATE NOCASE
                        OR b.author LIKE ? COLLATE NOCASE
                        OR b.category LIKE ? COLLATE NOCASE
                    )
                    """
                )

                params += [f"%{q}%"] * 5

            sql = """
                SELECT
                    b.book_id,
                    b.isbn,
                    b.title,
                    b.author,
                    b.category,
                    b.publisher,
                    b.year,
                    b.quantity,
                    b.available_quantity
                FROM books b
            """

        # -----------------------------------------------------
        # MEMBERS
        # -----------------------------------------------------

        elif k == "Members":

            if q:

                clauses.append(
                    """
                    (
                        CAST(m.member_id AS TEXT) LIKE ?
                        OR m.name LIKE ? COLLATE NOCASE
                        OR m.email LIKE ? COLLATE NOCASE
                        OR m.phone LIKE ?
                        OR m.course_class LIKE ? COLLATE NOCASE
                    )
                    """
                )

                params += [f"%{q}%"] * 5

            sql = """
                SELECT
                    m.member_id,
                    m.name,
                    m.phone,
                    m.email,
                    m.course_class,
                    m.registration_date
                FROM members m
            """

            date_col = "m.registration_date"

        # -----------------------------------------------------
        # ISSUED / OVERDUE BOOKS
        # -----------------------------------------------------

        elif k in ("Issued Books", "Overdue Books"):

            clauses.append("t.status = 'Issued'")

            if k == "Overdue Books":
                clauses.append(
                    "t.due_date < date('now')"
                )

            if q:

                clauses.append(
                    """
                    (
                        CAST(t.transaction_id AS TEXT) LIKE ?
                        OR CAST(t.book_id AS TEXT) LIKE ?
                        OR CAST(t.member_id AS TEXT) LIKE ?
                        OR b.title LIKE ? COLLATE NOCASE
                        OR m.name LIKE ? COLLATE NOCASE
                    )
                    """
                )

                params += [f"%{q}%"] * 5

            sql = """
                SELECT
                    t.transaction_id,
                    t.book_id,
                    b.title,
                    t.member_id,
                    m.name,
                    t.issue_date,
                    t.due_date,
                    t.status
                FROM transactions t
                JOIN books b
                    ON b.book_id = t.book_id
                JOIN members m
                    ON m.member_id = t.member_id
            """

            date_col = "t.issue_date"

        # -----------------------------------------------------
        # ALL TRANSACTIONS
        # -----------------------------------------------------

        else:

            if q:

                clauses.append(
                    """
                    (
                        CAST(t.transaction_id AS TEXT) LIKE ?
                        OR CAST(t.book_id AS TEXT) LIKE ?
                        OR CAST(t.member_id AS TEXT) LIKE ?
                        OR b.title LIKE ? COLLATE NOCASE
                        OR m.name LIKE ? COLLATE NOCASE
                        OR t.status LIKE ?
                    )
                    """
                )

                params += [f"%{q}%"] * 6

            sql = """
                SELECT
                    t.transaction_id,
                    t.book_id,
                    b.title,
                    t.member_id,
                    m.name,
                    t.issue_date,
                    t.due_date,
                    t.return_date,
                    t.status
                FROM transactions t
                JOIN books b
                    ON b.book_id = t.book_id
                JOIN members m
                    ON m.member_id = t.member_id
            """

            date_col = "t.issue_date"

        # -----------------------------------------------------
        # DATE FILTER
        # -----------------------------------------------------

        try:

            if date_col:

                from_value = self.from_date.get().strip()
                to_value = self.to_date.get().strip()

                if from_value:

                    clauses.append(
                        f"{date_col} >= ?"
                    )

                    params.append(
                        date_value(
                            from_value,
                            "From date"
                        )
                    )

                if to_value:
                    clauses.append(f"{date_col} <= ?")
                    params.append(date_value(to_value, "To date"))

                if from_value and to_value:
                    if date_value(from_value, "From date") > date_value(to_value, "To date"):
                        raise ValueError("From date cannot be later than To date.")

            # -------------------------------------------------
            # WHERE
            # -------------------------------------------------

            if clauses:
                sql += " WHERE " + " AND ".join(clauses)

            # Count in SQLite, but fetch/render only one page in the GUI.
            count_row = db.fetchone(
                "SELECT COUNT(*) AS n FROM (" + sql + ") AS report_count",
                params,
            )
            self.total_rows = int(count_row["n"])

            # -------------------------------------------------
            # SORTING
            # -------------------------------------------------

            sort_value = self.sort.get()

            if sort_value == "Date ↑" and date_col:

                sql += f" ORDER BY {date_col} ASC"

            elif sort_value == "Date ↓" and date_col:

                sql += f" ORDER BY {date_col} DESC"

            elif sort_value == "Title A-Z" and k != "Members":

                sql += " ORDER BY b.title COLLATE NOCASE ASC"

            elif sort_value == "Title Z-A" and k != "Members":

                sql += " ORDER BY b.title COLLATE NOCASE DESC"

            else:

                sql += " ORDER BY 1"

            # Save the complete filtered/sorted query for full CSV export.
            self.export_sql = sql
            self.export_params = list(params)

            # -------------------------------------------------
            # LIMIT: only one page is rendered in the GUI
            # -------------------------------------------------

            sql += " LIMIT ? OFFSET ?"
            page_params = params + [PAGE_SIZE, self.page * PAGE_SIZE]

            self.rows = db.fetchall(
                sql,
                page_params
            )

            # -------------------------------------------------
            # IMPORTANT FIX
            # Destroy COMPLETE old table frame
            # -------------------------------------------------

            if self.table_frame is not None:

                self.table_frame.destroy()

                self.table_frame = None
                self.tree = None

            # -------------------------------------------------
            # HEADERS
            # -------------------------------------------------

            if self.rows:

                self.headers = list(
                    self.rows[0].keys()
                )

            else:

                self.headers = ["No data"]

            # -------------------------------------------------
            # CREATE ONE TABLE ONLY
            # -------------------------------------------------

            self.table_frame, self.tree = make_table(
                self.table_holder,
                self.headers,
                [140] * len(self.headers),
                height=17
            )

            self.table_frame.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )

            # -------------------------------------------------
            # INSERT DATA
            # -------------------------------------------------

            for r in self.rows:
                self.tree.insert("", "end", values=list(r))

            start = self.page * PAGE_SIZE + 1 if self.total_rows else 0
            end = min((self.page + 1) * PAGE_SIZE, self.total_rows)
            self.page_info.configure(
                text=f"Showing {start}–{end} of {self.total_rows} records"
            )

        except Exception as ex:

            messagebox.showerror(
                "Report filter error",
                str(ex)
            )

    # ---------------------------------------------------------
    # EXPORT CSV
    # ---------------------------------------------------------

    def export(self):

        if self.rows:

            export_rows(
                self.headers,
                [list(r) for r in self.rows],
                "Export Report"
            )

        else:

            messagebox.showinfo(
                "Export",
                "No data to export."
            )