import customtkinter as ctk
from tkinter import messagebox

from models.book import BookModel
from utils.validators import required, positive_int, year_value
from utils.ui import Page, PANEL, MUTED, make_table


PAGE = 25


class BooksView(Page):

    def __init__(self, master, navigate, logout):
        super().__init__(master, navigate, logout, "Books")

        self.model = BookModel(master.db)
        self.page = 0
        self.search = ctk.StringVar()
        self.category = ctk.StringVar(value="All")

        self.build()
        self.refresh()

    def build(self):

        top = self.header(
            "Books",
            "Fast indexed search, filters and paginated records"
        )

        self.button(
            top,
            "＋ Add Book",
            self.add,
            width=135
        ).pack(side="right", anchor="e")

        # Search / Filter area
        controls = ctk.CTkFrame(
            self.content,
            fg_color=PANEL,
            corner_radius=10
        )
        controls.pack(
            fill="x",
            padx=30,
            pady=(0, 12)
        )

        ctk.CTkLabel(
            controls,
            text="🔎",
            font=ctk.CTkFont(size=18)
        ).pack(
            side="left",
            padx=(15, 4)
        )

        ctk.CTkLabel(
            controls,
            text="Search",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(
            side="left",
            padx=(0, 6)
        )

        e = ctk.CTkEntry(
            controls,
            textvariable=self.search,
            placeholder_text="Search by Book ID, ISBN, title, author or category...",
            height=40
        )

        e.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
            pady=12
        )

        e.bind(
            "<KeyRelease>",
            lambda _: self.refresh(True)
        )

        ctk.CTkLabel(
            controls,
            text="Category",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(
            side="left",
            padx=(8, 4)
        )

        self.cat = ctk.CTkComboBox(
            controls,
            variable=self.category,
            values=["All"] + self.model.categories(),
            width=180,
            height=40,
            command=lambda _: self.refresh(True)
        )

        self.cat.pack(
            side="left",
            padx=5
        )

        ctk.CTkButton(
            controls,
            text="Clear",
            width=80,
            height=40,
            command=self.clear
        ).pack(
            side="left",
            padx=(5, 12)
        )

        # Table
        table, self.tree = make_table(
            self.content,
            (
                "ID",
                "ISBN",
                "Title",
                "Author",
                "Category",
                "Publisher",
                "Year",
                "Qty",
                "Available"
            ),
            [75, 125, 220, 180, 150, 160, 75, 70, 95],
            height=10
        )

        table.pack(
            fill="x",
            expand=False,
            padx=30,
            pady=5
        )

        self.tree.bind(
            "<Double-1>",
            lambda e: self.edit()
        )

        # Bottom buttons
        bottom = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        bottom.pack(
            fill="x",
            padx=30,
            pady=(10, 22)
        )

        self.button(
            bottom,
            "Edit Selected",
            self.edit
        ).pack(
            side="left",
            padx=4
        )

        self.button(
            bottom,
            "Delete Selected",
            self.delete,
            True
        ).pack(
            side="left",
            padx=4
        )

        self.info = ctk.CTkLabel(
            bottom,
            text="",
            text_color=MUTED
        )

        self.info.pack(
            side="right",
            padx=10
        )

        self.button(
            bottom,
            "Previous",
            lambda: self.change(-1),
            width=100
        ).pack(
            side="right",
            padx=3
        )

        self.button(
            bottom,
            "Next",
            lambda: self.change(1),
            width=100
        ).pack(
            side="right",
            padx=3
        )

    def refresh(self, reset=False):

        if reset:
            self.page = 0

        for i in self.tree.get_children():
            self.tree.delete(i)

        rows = self.model.list(
            self.search.get(),
            self.category.get(),
            PAGE,
            self.page * PAGE
        )

        total = self.model.count(
            self.search.get(),
            self.category.get()
        )

        for r in rows:
            self.tree.insert(
                "",
                "end",
                values=[
                    r[k]
                    for k in (
                        "book_id",
                        "isbn",
                        "title",
                        "author",
                        "category",
                        "publisher",
                        "year",
                        "quantity",
                        "available_quantity"
                    )
                ]
            )

        start = self.page * PAGE + 1 if total else 0
        end = min((self.page + 1) * PAGE, total)

        self.info.configure(
            text=f"Showing {start}–{end} of {total} books"
        )

    def clear(self):

        self.search.set("")
        self.category.set("All")
        self.refresh(True)

    def selected_id(self):

        s = self.tree.selection()

        if s:
            return int(
                self.tree.item(s[0])["values"][0]
            )

        return None

    def add(self):
        self.form()

    def edit(self):

        bid = self.selected_id()

        if not bid:
            return messagebox.showwarning(
                "Books",
                "Select a book first."
            )

        self.form(
            self.model.get(bid)
        )

    # =========================================================
    # ADD / EDIT BOOK FORM
    # =========================================================

    def form(self, row=None):

        w = ctk.CTkToplevel(self)

        w.title(
            "Edit Book" if row else "Add Book"
        )

        # FIXED: smaller popup so Save button is visible
        w.geometry("520x650")

        w.minsize(520, 650)
        w.maxsize(520, 650)

        w.configure(
            fg_color="#111315"
        )

        w.grab_set()

        # Center popup on screen
        w.update_idletasks()

        screen_width = w.winfo_screenwidth()
        screen_height = w.winfo_screenheight()

        popup_width = 520
        popup_height = 650

        x = (screen_width - popup_width) // 2
        y = (screen_height - popup_height) // 2

        if y < 20:
            y = 20

        w.geometry(
            f"{popup_width}x{popup_height}+{x}+{y}"
        )

        # Title
        ctk.CTkLabel(
            w,
            text="Edit Book" if row else "Add New Book",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=35,
            pady=(20, 12)
        )

        labels = [
            "Book ID",
            "ISBN",
            "Title",
            "Author",
            "Category",
            "Publisher",
            "Year",
            "Quantity"
        ]

        keys = [
            "book_id",
            "isbn",
            "title",
            "author",
            "category",
            "publisher",
            "year",
            "quantity"
        ]

        ens = []

        for lab, key in zip(labels, keys):

            ctk.CTkLabel(
                w,
                text=lab
            ).pack(
                anchor="w",
                padx=35,
                pady=(3, 1)
            )

            e = ctk.CTkEntry(
                w,
                width=450,
                height=34
            )

            e.pack(
                padx=35,
                pady=(0, 2)
            )

            if row and row[key] is not None:
                e.insert(
                    0,
                    str(row[key])
                )

            if row and key == "book_id":
                e.configure(
                    state="disabled"
                )

            ens.append(e)

        # =====================================================
        # SAVE FUNCTION
        # =====================================================

        def save():

            try:

                vals = [
                    e.get().strip()
                    for e in ens
                ]

                # Required fields
                for i in range(6):
                    required(
                        vals[i],
                        labels[i]
                    )

                year = year_value(
                    vals[6]
                )

                qty = positive_int(
                    vals[7],
                    "Quantity"
                )

                # EDIT BOOK
                if row:

                    issued = (
                        int(row["quantity"])
                        - int(row["available_quantity"])
                    )

                    if qty < issued:
                        raise ValueError(
                            f"Quantity cannot be less than currently "
                            f"issued copies ({issued})."
                        )

                    self.model.update(
                        [
                            vals[1],
                            vals[2],
                            vals[3],
                            vals[4],
                            vals[5],
                            year,
                            qty,
                            qty - issued,
                            row["book_id"]
                        ]
                    )

                # ADD NEW BOOK
                else:

                    self.model.add(
                        [
                            int(vals[0]),
                            vals[1],
                            vals[2],
                            vals[3],
                            vals[4],
                            vals[5],
                            year,
                            qty,
                            qty
                        ]
                    )

                # Close popup
                w.destroy()

                # Refresh category list
                self.cat.configure(
                    values=[
                        "All"
                    ] + self.model.categories()
                )

                # Refresh books table
                self.refresh(True)

                messagebox.showinfo(
                    "Books",
                    "Book saved successfully."
                )

            except Exception as ex:

                messagebox.showerror(
                    "Save error",
                    str(ex)
                )

        # =====================================================
        # SAVE BUTTON
        # =====================================================

        ctk.CTkButton(
            w,
            text="Save Book",
            height=42,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            command=save
        ).pack(
            fill="x",
            padx=35,
            pady=(10, 15)
        )

    # =========================================================
    # DELETE
    # =========================================================

    def delete(self):

        bid = self.selected_id()

        if not bid:
            return messagebox.showwarning(
                "Books",
                "Select a book first."
            )

        if messagebox.askyesno(
            "Confirm Delete",
            "Delete the selected book? This cannot be undone."
        ):

            try:

                self.model.delete(bid)
                self.refresh()

            except Exception:

                messagebox.showerror(
                    "Delete error",
                    "This book has transaction history and cannot be deleted."
                )

    # =========================================================
    # PAGINATION
    # =========================================================

    def change(self, d):

        total = self.model.count(
            self.search.get(),
            self.category.get()
        )

        if d < 0 and self.page > 0:

            self.page -= 1

        elif d > 0 and (self.page + 1) * PAGE < total:

            self.page += 1

        self.refresh()