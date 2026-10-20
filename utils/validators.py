from datetime import datetime, date
import re

def required(value,label):
    if not str(value).strip(): raise ValueError(f"{label} is required.")

def positive_int(value,label,allow_zero=False):
    try:
        n=int(str(value).strip())
        if n<0 or (not allow_zero and n==0): raise ValueError
        return n
    except Exception: raise ValueError(f"{label} must be a valid {'non-negative' if allow_zero else 'positive'} integer.")

def year_value(value):
    if not str(value).strip(): return None
    try:
        y=int(value); current=datetime.now().year
        if y<1000 or y>current+1: raise ValueError
        return y
    except Exception: raise ValueError("Year must be between 1000 and next year.")

def email_value(value):
    value=value.strip()
    if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",value): raise ValueError("Enter a valid email address.")
    return value

def date_value(value,label="Date"):
    try:
        return datetime.strptime(value.strip(),"%Y-%m-%d").date().isoformat()
    except Exception: raise ValueError(f"{label} must use YYYY-MM-DD format.")

def phone_value(value):
    value=value.strip()
    if value and not re.fullmatch(r"[0-9+()\- ]{7,20}",value): raise ValueError("Enter a valid phone number.")
    return value
