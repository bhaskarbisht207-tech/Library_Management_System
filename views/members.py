import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from models.member import MemberModel
from utils.validators import required,email_value,phone_value,date_value,positive_int
from utils.ui import Page,PANEL,MUTED,make_table

PAGE=25
class MembersView(Page):
    def __init__(self,master,navigate,logout):
        super().__init__(master,navigate,logout,"Members");self.model=MemberModel(master.db);self.page=0;self.search=ctk.StringVar();self._search_after_id=None;self.build();self.refresh()
    def build(self):
        top=self.header("Members","Manage registered library members")
        self.button(top,"＋ Add Member",self.add,width=140).pack(side="right")
        c=ctk.CTkFrame(self.content,fg_color=PANEL,corner_radius=10);c.pack(fill="x",padx=30,pady=(0,12));
        ctk.CTkLabel(c,text="🔎",font=ctk.CTkFont(size=18)).pack(side="left",padx=(15,4));ctk.CTkLabel(c,text="Search",font=ctk.CTkFont(size=13,weight="bold")).pack(side="left",padx=(0,6));e=ctk.CTkEntry(c,textvariable=self.search,placeholder_text="Search Member ID, name, phone, email or course...",height=40);e.pack(fill="x",expand=True,padx=(0,15),pady=12);e.bind("<KeyRelease>",lambda _:self.schedule_search())
        f,self.tree=make_table(self.content,("ID","Name","Phone","Email","Course / Class","Registration Date"),[80,180,140,230,180,140],height=10);f.pack(fill="x",expand=False,padx=30,pady=5);self.tree.bind("<Double-1>",lambda e:self.edit())
        b=ctk.CTkFrame(self.content,fg_color="transparent");b.pack(fill="x",padx=30,pady=(10,22));self.button(b,"Edit Selected",self.edit).pack(side="left",padx=4);self.button(b,"Delete Selected",self.delete,True).pack(side="left",padx=4);self.info=ctk.CTkLabel(b,text="",text_color=MUTED);self.info.pack(side="right",padx=10);self.button(b,"Previous",lambda:self.change(-1),width=100).pack(side="right",padx=3);self.button(b,"Next",lambda:self.change(1),width=100).pack(side="right",padx=3)
    def schedule_search(self):
        """Wait briefly after typing before running a database search."""
        if self._search_after_id is not None:
            try:self.after_cancel(self._search_after_id)
            except Exception:pass
        self._search_after_id=self.after(180,self._run_scheduled_search)
    def _run_scheduled_search(self):
        self._search_after_id=None
        if self.winfo_exists():self.refresh(True)
    def refresh(self,reset=False):
        if reset:self.page=0
        for i in self.tree.get_children():self.tree.delete(i)
        q=self.search.get().strip();rows=self.model.list(q,PAGE,self.page*PAGE);total=self.model.count(q)
        for r in rows:self.tree.insert("","end",values=list(r))
        start=self.page*PAGE+1 if total else 0;end=min((self.page+1)*PAGE,total);self.info.configure(text=f"Showing {start}–{end} of {total} members")
    def sid(self):
        s=self.tree.selection();return int(self.tree.item(s[0])["values"][0]) if s else None
    def add(self):self.form()
    def edit(self):
        mid=self.sid()
        if not mid:return messagebox.showwarning("Members","Select a member first.")
        self.form(self.model.get(mid))
    def form(self,row=None):
        w=ctk.CTkToplevel(self);w.title("Edit Member" if row else "Add Member");w.geometry("500x620");w.configure(fg_color="#111315");w.grab_set();ctk.CTkLabel(w,text="Edit Member" if row else "Add New Member",font=ctk.CTkFont(size=24,weight="bold")).pack(anchor="w",padx=35,pady=(28,18))
        labels=["Member ID","Name","Phone","Email","Course / Class","Registration Date"];vals=[row[k] for k in ("member_id","name","phone","email","course_class","registration_date")] if row else ["","","","","",date.today().isoformat()];ens=[]
        for lab,val in zip(labels,vals):
            ctk.CTkLabel(w,text=lab).pack(anchor="w",padx=35,pady=(7,2));e=ctk.CTkEntry(w,width=430,height=38);e.pack(padx=35);e.insert(0,str(val or ""));ens.append(e)
            if row and lab=="Member ID":e.configure(state="disabled")
        def save():
            try:
                v=[e.get().strip() for e in ens];required(v[0],labels[0]);required(v[1],labels[1]);v[2]=phone_value(v[2]);v[3]=email_value(v[3]);v[5]=date_value(v[5],"Registration Date")
                if row:self.model.update([v[1],v[2],v[3],v[4],v[5],row["member_id"]])
                else:self.model.add([int(v[0]),v[1],v[2],v[3],v[4],v[5]])
                w.destroy();self.refresh(True);messagebox.showinfo("Members","Member saved successfully.")
            except Exception as ex:messagebox.showerror("Save error",str(ex))
        ctk.CTkButton(w,text="Save Member",height=42,command=save).pack(fill="x",padx=35,pady=25)
    def delete(self):
        mid=self.sid()
        if not mid:return messagebox.showwarning("Members","Select a member first.")
        if messagebox.askyesno("Confirm Delete","Delete selected member? Transaction history prevents deletion if used."):
            try:self.model.delete(mid);self.refresh()
            except Exception:messagebox.showerror("Delete error","This member has transaction history and cannot be deleted.")
    def change(self,d):
        total=self.model.count(self.search.get())
        if d<0 and self.page>0:self.page-=1
        elif d>0 and (self.page+1)*PAGE<total:self.page+=1
        self.refresh()
