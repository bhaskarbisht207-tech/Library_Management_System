import csv,customtkinter as ctk
from tkinter import messagebox
from utils.helpers import ask_csv
from utils.validators import year_value,positive_int,required
from utils.ui import Page,PANEL,MUTED

REQUIRED=["book_id","isbn","title","author","category","publisher","year","quantity"]
class CSVImportView(Page):
    def __init__(self,master,navigate,logout):super().__init__(master,navigate,logout,"CSV Import");self.build()
    def build(self):
        self.header("CSV Import","Bulk import books with validation, duplicate protection and one database transaction")
        box=ctk.CTkFrame(self.content,fg_color=PANEL,corner_radius=12);box.pack(fill="x",padx=30,pady=5)
        ctk.CTkLabel(box,text="Import Books from CSV",font=ctk.CTkFont(size=22,weight="bold")).pack(anchor="w",padx=22,pady=(20,5))
        ctk.CTkLabel(box,text="Required columns: book_id, isbn, title, author, category, publisher, year, quantity",text_color=MUTED).pack(anchor="w",padx=22,pady=(0,18))
        row=ctk.CTkFrame(box,fg_color="transparent");row.pack(fill="x",padx=18,pady=(0,18));self.path=ctk.CTkEntry(row,placeholder_text="Select a .csv file...",height=42);self.path.pack(side="left",fill="x",expand=True,padx=4);ctk.CTkButton(row,text="Browse",height=42,command=self.browse).pack(side="left",padx=4);ctk.CTkButton(row,text="Import CSV",height=42,command=self.import_csv).pack(side="left",padx=4)
        self.result=ctk.CTkTextbox(self.content,height=300);self.result.pack(fill="both",expand=True,padx=30,pady=15);self.result.configure(state="disabled")
        sample=ctk.CTkLabel(self.content,text="Tip: sample_data/books.csv is included with the project.",text_color=MUTED);sample.pack(anchor="w",padx=30,pady=(0,20))
    def browse(self):
        p=ask_csv()
        if p:self.path.delete(0,"end");self.path.insert(0,p)
    def log(self,text):self.result.configure(state="normal");self.result.insert("end",text+"\n");self.result.configure(state="disabled")
    def import_csv(self):
        p=self.path.get().strip()
        if not p:return messagebox.showwarning("CSV Import","Please select a CSV file first.")
        try:
            with open(p,"r",encoding="utf-8-sig",newline="") as f:
                reader=csv.DictReader(f)
                if not reader.fieldnames:raise ValueError("CSV has no header row.")
                original_fields = reader.fieldnames
                fields = [x.strip().lower() for x in original_fields]
                column_map = {normalized: original for normalized, original in zip(fields, original_fields)}
                missing = [x for x in REQUIRED if x not in column_map]
                if missing:
                    raise ValueError("Missing required columns: " + ", ".join(missing))

                existing = self.master.db.fetchall("SELECT book_id, isbn FROM books")
                ids = {int(r["book_id"]) for r in existing}
                isbns = {r["isbn"].strip().lower() for r in existing}
                valid, failed = [], []
                seen_ids, seen_isbns = set(), set()
                for line, row in enumerate(reader, start=2):
                    try:
                        data = {key: (row.get(column_map.get(key, ""), "") or "").strip() for key in fields}
                        for k in REQUIRED[:5]:required(data[k],k.title())
                        bid=positive_int(data["book_id"],"Book ID");qty=positive_int(data["quantity"],"Quantity")
                        isbn=data["isbn"];year=year_value(data["year"])
                        if bid in ids or bid in seen_ids:raise ValueError("Duplicate Book ID")
                        if isbn.lower() in isbns or isbn.lower() in seen_isbns:raise ValueError("Duplicate ISBN")
                        seen_ids.add(bid);seen_isbns.add(isbn.lower());valid.append((bid,isbn,data["title"],data["author"],data["category"],data["publisher"],year,qty,qty))
                    except Exception as ex:failed.append((line,str(ex)))
            if valid:
                self.master.db.executemany(
                    "INSERT INTO books(book_id,isbn,title,author,category,publisher,year,quantity,available_quantity) VALUES(?,?,?,?,?,?,?,?,?)",
                    valid,
                )
            self.result.configure(state="normal");self.result.delete("1.0","end");self.result.configure(state="disabled")
            self.log(f"Import completed. Successful records: {len(valid)}")
            self.log(f"Failed / invalid records: {len(failed)}")
            if failed:
                self.log("\nFailed rows:")
                for line,reason in failed[:100]:self.log(f"  Line {line}: {reason}")
            messagebox.showinfo("CSV Import",f"Imported {len(valid)} book(s).\nFailed: {len(failed)}")
        except UnicodeDecodeError:messagebox.showerror("CSV Import","Could not read this file as UTF-8 CSV.")
        except Exception as ex:messagebox.showerror("CSV Import",str(ex))
