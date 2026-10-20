import customtkinter as ctk
from tkinter import messagebox

class LoginView(ctk.CTkFrame):
    def __init__(self,master,on_login):
        super().__init__(master,fg_color="#0F1113"); self.on_login=on_login; self.build()
    def build(self):
        box=ctk.CTkFrame(self,width=470,height=510,corner_radius=18,fg_color="#1B1E21"); box.place(relx=.5,rely=.5,anchor="center"); box.pack_propagate(False)
        ctk.CTkLabel(box,text="▣",font=ctk.CTkFont(size=48,weight="bold"),text_color="#2584D6").pack(pady=(35,5))
        ctk.CTkLabel(box,text="Library Management System",font=ctk.CTkFont(size=25,weight="bold")).pack()
        ctk.CTkLabel(box,text="Administrator Login",text_color="#9CA3AF").pack(pady=(5,28))
        ctk.CTkLabel(box,text="Username",anchor="w").pack(fill="x",padx=55)
        self.user=ctk.CTkEntry(box,height=42,placeholder_text="Enter username");self.user.pack(fill="x",padx=55,pady=(5,16))
        ctk.CTkLabel(box,text="Password",anchor="w").pack(fill="x",padx=55)
        self.password=ctk.CTkEntry(box,height=42,placeholder_text="Enter password",show="•");self.password.pack(fill="x",padx=55,pady=(5,25))
        ctk.CTkButton(box,text="Login",height=44,command=self.login).pack(fill="x",padx=55)
        ctk.CTkLabel(box,text="Default college-demo account: admin / admin123",font=ctk.CTkFont(size=11),text_color="#6B7280").pack(pady=18)
        self.user.bind("<Return>",lambda e:self.password.focus());self.password.bind("<Return>",lambda e:self.login());self.user.focus_set()
    def login(self):
        u,p=self.user.get().strip(),self.password.get()
        if not u or not p:return messagebox.showwarning("Login","Please enter username and password.")
        user=self.master.db.verify_user(u,p)
        if user:self.on_login(user)
        else:messagebox.showerror("Login failed","Invalid username or password.")
