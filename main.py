import customtkinter as ctk
from database.database import Database
from views.login import LoginView
from views.dashboard import DashboardView
from views.books import BooksView
from views.members import MembersView
from views.issue_return import IssueReturnView
from views.reports import ReportsView
from views.csv_import import CSVImportView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__();self.title("Library Management System");self.geometry("1400x850");self.minsize(1120,700);self.db=Database();self.current_user=None;self.protocol("WM_DELETE_WINDOW",self.on_close);self.show_login()
    def clear(self):
        for w in self.winfo_children():w.destroy()
    def show_login(self):
        self.clear();LoginView(self,self.on_login).pack(fill="both",expand=True)
    def on_login(self,user):self.current_user=user;self.show_dashboard()
    def show_dashboard(self):self.clear();DashboardView(self,self.navigate,self.logout).pack(fill="both",expand=True)
    def navigate(self,page):
        self.clear();views={"Dashboard":DashboardView,"Books":BooksView,"Members":MembersView,"Issue / Return":IssueReturnView,"Reports":ReportsView,"CSV Import":CSVImportView};views[page](self,self.navigate,self.logout).pack(fill="both",expand=True)
    def logout(self):self.current_user=None;self.show_login()
    def on_close(self):self.db.close();self.destroy()

if __name__=="__main__":LibraryApp().mainloop()
