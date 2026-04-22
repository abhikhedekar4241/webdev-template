"""Script to create a superuser."""
import argparse
import asyncio
import sys

sys.path.insert(0, "/app")

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import engine
from app.services.auth import auth_service


async def create_superuser(email, password, full_name):
    async with AsyncSession(engine, expire_on_commit=False) as session:
        user = await auth_service.get_by_email(session, email=email)
        if user:
            print(f"User with email {email} already exists. Promoting to superuser.")
            user.is_superuser = True
            user.is_verified = True
            session.add(user)
            await session.commit()
            print(f"User {email} is now a superuser.")
            return

        user = await auth_service.create_user(
            session,
            email=email,
            password=password,
            full_name=full_name,
            is_verified=True,
        )
        user.is_superuser = True
        session.add(user)
        await session.commit()
        print(f"Superuser created: {email}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a superuser.")
    parser.add_argument("--email", required=True, help="Email of the superuser")
    parser.add_argument("--password", required=True, help="Password of the superuser")
    parser.add_argument("--full_name", required=True, help="Full name of the superuser")

    args = parser.parse_args()
    asyncio.run(create_superuser(args.email, args.password, args.full_name))
