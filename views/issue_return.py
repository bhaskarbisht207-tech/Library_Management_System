import customtkinter as ctk
from tkinter import messagebox
from datetime import date,timedelta,datetime
from models.transaction import TransactionModel
from utils.validators import positive_int,date_value
from utils.ui import Page,PANEL,MUTED,make_table

class IssueReturnView(Page):
    def __init__(self,master,navigate,logout):
        super().__init__(master,navigate,logout,"Issue / Return");self.model=TransactionModel(master.db);self.search=ctk.StringVar();self.build();self.refresh()
    def build(self):
        self.header("Issue / Return","Issue books safely and track active transactions")
        issue=ctk.CTkFrame(self.content,fg_color=PANEL,corner_radius=10);issue.pack(fill="x",padx=30,pady=(0,12))
        ctk.CTkLabel(issue,text="Issue Book",font=ctk.CTkFont(size=20,weight="bold")).grid(row=0,column=0,columnspan=5,sticky="w",padx=18,pady=(15,8))
        self.bid=ctk.CTkEntry(issue,placeholder_text="Book ID",height=40);self.bid.grid(row=1,column=0,padx=10,pady=(0,15),sticky="ew");self.mid=ctk.CTkEntry(issue,placeholder_text="Member ID",height=40);self.mid.grid(row=1,column=1,padx=10,pady=(0,15),sticky="ew")
        self.due=ctk.CTkEntry(issue,height=40);self.due.insert(0,(date.today()+timedelta(days=14)).isoformat());self.due.grid(row=1,column=2,padx=10,pady=(0,15),sticky="ew")
        ctk.CTkButton(issue,text="Issue Book",height=40,command=self.issue).grid(row=1,column=3,padx=10,pady=(0,15));issue.grid_columnconfigure((0,1,2),weight=1)
        ret=ctk.CTkFrame(self.content,fg_color=PANEL,corner_radius=10);ret.pack(fill="x",padx=30,pady=(0,12));ctk.CTkLabel(ret,text="Return Book",font=ctk.CTkFont(size=20,weight="bold")).pack(side="left",padx=18,pady=14);self.tid=ctk.CTkEntry(ret,placeholder_text="Transaction ID",height=40,width=230);self.tid.pack(side="left",padx=8);ctk.CTkButton(ret,text="Return Book",height=40,command=self.return_book).pack(side="left",padx=8)
        search=ctk.CTkFrame(self.content,fg_color="transparent");search.pack(fill="x",padx=30,pady=(2,5));self.search_entry=ctk.CTkEntry(search,textvariable=self.search,placeholder_text="Search active transactions by ID, Book ID, Member ID, title or member...",height=38);self.search_entry.pack(fill="x",expand=True);self.search_entry.bind("<KeyRelease>",lambda _:self.refresh())
        f,self.tree=make_table(self.content,("ID","Book ID","Book","Member ID","Member","Issue","Due","Status"),[65,80,240,90,200,120,120,100],height=9);f.pack(fill="x",expand=False,padx=30,pady=5);self.tree.bind("<Double-1>",lambda e:self.fill_return())
        b=ctk.CTkFrame(self.content,fg_color="transparent");b.pack(fill="x",padx=30,pady=(8,22));self.button(b,"Return Selected",self.return_selected).pack(side="left");self.info=ctk.CTkLabel(b,text="Active issued books",text_color=MUTED);self.info.pack(side="right")
    def issue(self):
        try:
            bid=positive_int(self.bid.get(),"Book ID");mid=positive_int(self.mid.get(),"Member ID");due=date_value(self.due.get(),"Due Date");self.model.issue(bid,mid,due);self.bid.delete(0,"end");self.mid.delete(0,"end");self.refresh();messagebox.showinfo("Issue Book","Book issued successfully.")
        except Exception as ex:messagebox.showerror("Issue error",str(ex))
    def selected_tid(self):
        s=self.tree.selection();return int(self.tree.item(s[0])["values"][0]) if s else None
    def fill_return(self):
        tid=self.selected_tid()
        if tid:self.tid.delete(0,"end");self.tid.insert(0,str(tid))
    def return_selected(self):
        tid=self.selected_tid()
        if not tid:return messagebox.showwarning("Return Book","Select an active transaction first.")
        self.tid.delete(0,"end");self.tid.insert(0,str(tid));self.return_book()
    def return_book(self):
        try:
            tid=positive_int(self.tid.get(),"Transaction ID");overdue=self.model.return_book(tid);self.tid.delete(0,"end");self.refresh();messagebox.showinfo("Return Book","Book returned successfully." + (" It was overdue." if overdue else ""))
        except Exception as ex:messagebox.showerror("Return error",str(ex))
    def refresh(self):
        for i in self.tree.get_children():self.tree.delete(i)
        rows=self.model.issued(self.search.get(),100,0)
        for r in rows:self.tree.insert("","end",values=list(r))
        self.info.configure(text=f"{len(rows)} active issued transaction(s)")
