import csv
from tkinter import filedialog,messagebox
from pathlib import Path

def ask_csv():
    return filedialog.askopenfilename(title="Select CSV file",filetypes=[("CSV files","*.csv"),("All files","*.*")])

def export_rows(headers,rows,title="Export CSV"):
    path=filedialog.asksaveasfilename(title=title,defaultextension=".csv",filetypes=[("CSV files","*.csv")])
    if not path:return False
    try:
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f);w.writerow(headers);w.writerows(rows)
        messagebox.showinfo("Export complete",f"CSV exported successfully:\n{Path(path).name}");return True
    except Exception as ex:messagebox.showerror("Export error",str(ex));return False
