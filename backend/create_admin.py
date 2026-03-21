import sys
import os
sys.path.append('/app')

from database import SessionLocal, init_db
from models import User, RoleEnum
from auth import hash_password

def create_admin():
    init_db()
    db = SessionLocal()

    print("=== Admin-Benutzer anlegen ===")
    username = input("Benutzername: ").strip()
    email = input("E-Mail: ").strip()
    password = input("Passwort: ").strip()

    if not username or not email or not password:
        print("Fehler: Alle Felder müssen ausgefüllt werden.")
        db.close()
        return

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"Fehler: Benutzername '{username}' ist bereits vergeben.")
        db.close()
        return

    admin = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=RoleEnum.admin
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"\nAdmin '{username}' erfolgreich angelegt.")
    print(f"ID: {admin.id}")
    print(f"Rolle: {admin.role}")
    db.close()

if __name__ == "__main__":
    create_admin()