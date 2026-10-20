import customtkinter as ctk
from datetime import datetime

from views import __name__ as _unused
from utils.ui import Page,BG,PANEL,PANEL2,TEXT,MUTED,BLUE,GREEN,ORANGE,RED,make_table


class DashboardView(Page):
    def __init__(self, master, navigate, logout):
        super().__init__(master, navigate, logout, "Dashboard")

        # Make Dashboard content scrollable
        self.content.destroy()

        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )

        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        self._refresh_after_id = None
        self.build()
        self.refresh()

    # =========================================================
    # BUILD DASHBOARD
    # =========================================================

    def build(self):

        self.header(
            "Dashboard",
            "Library performance overview"
        )

        # -----------------------------------------------------
        # TOP HEADER / REFRESH
        # -----------------------------------------------------

        top_bar = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        top_bar.pack(
            fill="x",
            padx=30,
            pady=(5, 8)
        )

        self.updated_label = ctk.CTkLabel(
            top_bar,
            text="Last updated: --",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        )

        self.updated_label.pack(side="left")

        self.refresh_button = ctk.CTkButton(
            top_bar,
            text="↻  Refresh Dashboard",
            width=160,
            height=34,
            command=self.refresh
        )

        self.refresh_button.pack(side="right")

        # -----------------------------------------------------
        # STATISTICS CARDS
        # -----------------------------------------------------

        cards = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        cards.pack(
            fill="x",
            padx=30,
            pady=(5, 10)
        )

        self.stats = {}

        items = [
            ("Book Titles", "books", BLUE, "Total unique books"),
            ("Available Copies", "available", GREEN, "Ready to issue"),
            ("Issued Copies", "issued", ORANGE, "Currently issued"),
            ("Total Members", "members", BLUE, "Registered members"),
            ("Overdue Books", "overdue", RED, "Past due date"),
        ]

        for title, key, color, subtitle in items:

            card = ctk.CTkFrame(
                cards,
                fg_color=PANEL,
                corner_radius=14
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=5
            )

            # Title
            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(
                    size=15,
                    weight="bold"
                ),
                text_color=TEXT
            ).pack(
                anchor="w",
                padx=20,
                pady=(17, 2)
            )

            # Main number
            value_label = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(
                    size=30,
                    weight="bold"
                ),
                text_color=color
            )

            value_label.pack(
                anchor="w",
                padx=20,
                pady=(0, 2)
            )

            self.stats[key] = value_label

            # Subtitle
            ctk.CTkLabel(
                card,
                text=subtitle,
                font=ctk.CTkFont(size=11),
                text_color=MUTED
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 15)
            )

        # -----------------------------------------------------
        # QUICK ACTIONS
        # -----------------------------------------------------

        quick_panel = ctk.CTkFrame(
            self.content,
            fg_color=PANEL,
            corner_radius=14
        )

        quick_panel.pack(
            fill="x",
            padx=30,
            pady=10
        )

        ctk.CTkLabel(
            quick_panel,
            text="Quick Actions",
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            ),
            text_color=TEXT
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 2)
        )

        ctk.CTkLabel(
            quick_panel,
            text="Frequently used library operations",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 10)
        )

        action_row = ctk.CTkFrame(
            quick_panel,
            fg_color="transparent"
        )

        action_row.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        actions = [
            ("＋  Add Book", "Books"),
            ("♙  Add Member", "Members"),
            ("⇄  Issue / Return", "Issue / Return"),
            ("▥  Reports", "Reports"),
            ("⇩  CSV Import", "CSV Import"),
        ]

        for text, page in actions:

            ctk.CTkButton(
                action_row,
                text=text,
                height=42,
                command=lambda p=page: self.navigate(p)
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=5
            )

        # -----------------------------------------------------
        # RECENT TRANSACTIONS
        # -----------------------------------------------------

        transaction_panel = ctk.CTkFrame(
            self.content,
            fg_color=PANEL,
            corner_radius=14
        )

        transaction_panel.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(10, 25)
        )

        title_row = ctk.CTkFrame(
            transaction_panel,
            fg_color="transparent"
        )

        title_row.pack(
            fill="x",
            padx=20,
            pady=(15, 5)
        )

        ctk.CTkLabel(
            title_row,
            text="Recent Transactions",
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            ),
            text_color=TEXT
        ).pack(side="left")

        self.transaction_count = ctk.CTkLabel(
            title_row,
            text="0 records",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        )

        self.transaction_count.pack(side="right")

        ctk.CTkLabel(
            transaction_panel,
            text="Latest book issue and return activity",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 8)
        )

        table_frame, self.tree = make_table(
        transaction_panel,
        (
        "ID",
        "Book",
        "Member",
        "Issue Date",
        "Due Date",
        "Status"
        ),
        [
        70,
        320,
        220,
        140,
        140,
        120
        ],
        height=12
        )

        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

    # =========================================================
    # REFRESH DATA
    # =========================================================

    def refresh(self):

        # Manual refresh replaces the pending timer instead of creating
        # another timer chain every time the dashboard is refreshed.
        if self._refresh_after_id is not None:
            try:
                self.after_cancel(self._refresh_after_id)
            except Exception:
                pass
            self._refresh_after_id = None

        try:

            db = self.master.db

            # -------------------------------------------------
            # BOOK STATISTICS
            # -------------------------------------------------

            row = db.fetchone(
                """
                SELECT
                    COUNT(*) AS total_books,
                    COALESCE(SUM(quantity), 0) AS total_copies,
                    COALESCE(SUM(available_quantity), 0)
                    AS available_copies
                FROM books
                """
            )

            # -------------------------------------------------
            # MEMBER COUNT
            # -------------------------------------------------

            members = db.fetchone(
                """
                SELECT COUNT(*) AS n
                FROM members
                """
            )["n"]

            # -------------------------------------------------
            # ISSUED COUNT
            # -------------------------------------------------

            issued = db.fetchone(
                """
                SELECT COUNT(*) AS n
                FROM transactions
                WHERE status = 'Issued'
                """
            )["n"]

            # -------------------------------------------------
            # OVERDUE COUNT
            # -------------------------------------------------

            overdue = db.fetchone(
                """
                SELECT COUNT(*) AS n
                FROM transactions
                WHERE status = 'Issued'
                AND due_date < date('now')
                """
            )["n"]

            # -------------------------------------------------
            # UPDATE STAT CARDS
            # -------------------------------------------------

            values = {
                "books": row["total_books"],
                "available": row["available_copies"],
                "issued": issued,
                "members": members,
                "overdue": overdue
            }

            for key, value in values.items():

                self.stats[key].configure(
                    text=str(value)
                )

            # -------------------------------------------------
            # CLEAR OLD TRANSACTIONS
            # -------------------------------------------------

            for item in self.tree.get_children():
                self.tree.delete(item)

            # -------------------------------------------------
            # GET RECENT TRANSACTIONS
            # -------------------------------------------------

            rows = db.fetchall(
                """
                SELECT
                    t.transaction_id,
                    b.title,
                    m.name,
                    t.issue_date,
                    t.due_date,
                    t.status
                FROM transactions t

                JOIN books b
                    ON b.book_id = t.book_id

                JOIN members m
                    ON m.member_id = t.member_id

                ORDER BY
                    t.transaction_id DESC

                LIMIT 20
                """
            )

            # -------------------------------------------------
            # INSERT TRANSACTIONS
            # -------------------------------------------------

            for r in rows:
                self.tree.insert(
                    "",
                    "end",
                    values=list(r)
                )

            # -------------------------------------------------
            # TRANSACTION COUNT
            # -------------------------------------------------

            self.transaction_count.configure(
                text=f"{len(rows)} recent record(s)"
            )

            # -------------------------------------------------
            # LAST UPDATED
            # -------------------------------------------------

            current_time = datetime.now().strftime(
                "%d-%m-%Y  %I:%M:%S %p"
            )

            self.updated_label.configure(
                text=f"Last updated: {current_time}"
            )

            # -------------------------------------------------
            # AUTO REFRESH
            # -------------------------------------------------

            self._refresh_after_id = self.after(
                30000,
                self._auto_refresh
            )

        except Exception as e:

            print(
                "Dashboard refresh error:",
                e
            )

    # =========================================================
    # AUTO REFRESH
    # =========================================================

    def _auto_refresh(self):

        self._refresh_after_id = None
        try:
            if self.winfo_exists():
                self.refresh()

        except Exception:
            pass