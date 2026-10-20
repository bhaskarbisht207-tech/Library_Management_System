class MemberModel:
    def __init__(self, db): self.db = db

    def list(self, search="", limit=25, offset=0):
        if search:
            q = f"%{search.strip()}%"
            return self.db.fetchall("""SELECT member_id,name,phone,email,course_class,registration_date FROM members
                WHERE CAST(member_id AS TEXT) LIKE ? OR name LIKE ? COLLATE NOCASE OR phone LIKE ? OR email LIKE ? COLLATE NOCASE OR course_class LIKE ? COLLATE NOCASE
                ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?""", (q,q,q,q,q,limit,offset))
        return self.db.fetchall("""SELECT member_id,name,phone,email,course_class,registration_date FROM members
            ORDER BY name COLLATE NOCASE LIMIT ? OFFSET ?""", (limit,offset))

    def count(self, search=""):
        if search:
            q=f"%{search.strip()}%"
            return self.db.fetchone("""SELECT COUNT(*) n FROM members WHERE CAST(member_id AS TEXT) LIKE ? OR name LIKE ? COLLATE NOCASE
                OR phone LIKE ? OR email LIKE ? COLLATE NOCASE OR course_class LIKE ? COLLATE NOCASE""", (q,q,q,q,q))["n"]
        return self.db.fetchone("SELECT COUNT(*) n FROM members")["n"]

    def add(self,data): self.db.execute("INSERT INTO members(member_id,name,phone,email,course_class,registration_date) VALUES(?,?,?,?,?,?)",tuple(data))
    def update(self,data): self.db.execute("UPDATE members SET name=?,phone=?,email=?,course_class=?,registration_date=? WHERE member_id=?",tuple(data))
    def delete(self,member_id): self.db.execute("DELETE FROM members WHERE member_id=?",(member_id,))
    def get(self,member_id): return self.db.fetchone("SELECT member_id,name,phone,email,course_class,registration_date FROM members WHERE member_id=?",(member_id,))
