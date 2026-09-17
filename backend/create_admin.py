"""
BuildTech - Admin Account Creation Script

Creates a single, secure administrator account.
Enforces that only one admin account can exist in the system.
Passwords are typed securely without being displayed or logged.
"""

import argparse
import getpass
import re
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.users.models import User, UserRole

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"


def validate_email(email: str) -> bool:
    return bool(re.match(EMAIL_REGEX, email))


def create_admin():
    parser = argparse.ArgumentParser(
        description="Create the primary BuildTech administrator account."
    )
    parser.add_argument("--email", help="Admin email address", default=None)
    parser.add_argument("--first-name", help="Admin first name", default=None)
    parser.add_argument("--last-name", help="Admin last name", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Check if an admin account already exists (single admin policy)
        existing_admin = (
            db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        )
        if existing_admin:
            print("\n[ERROR] An administrator account already exists:")
            print(f"  ID: {existing_admin.id}")
            print(f"  Email: {existing_admin.email}")
            print(f"  Name: {existing_admin.first_name} {existing_admin.last_name}")
            print("To maintain security, only one admin account is allowed.")
            sys.exit(1)

        print("=" * 55)
        print("BuildTech - Create Administrator Account")
        print("=" * 55)

        # Collect email
        email = args.email
        while not email:
            input_email = input("Admin Email: ").strip()
            if not input_email or not validate_email(input_email):
                print("  [!] Please enter a valid email address.")
                continue
            email = input_email

        email = email.strip().lower()

        # Check if email is already taken by any user
        user_with_email = db.query(User).filter(User.email == email).first()
        if user_with_email:
            print(f"\n[ERROR] A user with email '{email}' already exists.")
            sys.exit(1)

        # Collect first name
        first_name = args.first_name
        while not first_name:
            input_fn = input("First Name: ").strip()
            if not input_fn:
                print("  [!] First name cannot be empty.")
                continue
            first_name = input_fn

        # Collect last name
        last_name = args.last_name
        while not last_name:
            input_ln = input("Last Name: ").strip()
            if not input_ln:
                print("  [!] Last name cannot be empty.")
                continue
            last_name = input_ln

        # Collect password securely
        while True:
            password = getpass.getpass("Password (min 8 chars): ")
            if len(password) < 8:
                print("  [!] Password must be at least 8 characters long.")
                continue

            confirm_password = getpass.getpass("Confirm Password: ")
            if password != confirm_password:
                print("  [!] Passwords do not match. Please try again.")
                continue

            break

        # Create admin user
        admin_user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=UserRole.ADMIN.value,
            is_active=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("\n" + "=" * 55)
        print("[SUCCESS] Admin account created successfully!")
        print(f"  User ID:    {admin_user.id}")
        print(f"  Email:      {admin_user.email}")
        print(f"  Name:       {admin_user.first_name} {admin_user.last_name}")
        print(f"  Role:       {admin_user.role}")
        print(f"  Status:     {'Active' if admin_user.is_active else 'Inactive'}")
        print("=" * 55)

    except Exception as e:
        db.rollback()
        print(f"\n[FATAL] Failed to create admin account: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
