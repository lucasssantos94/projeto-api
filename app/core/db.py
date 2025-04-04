import asyncpg
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    
    await conn.execute("""CREATE EXTENSION IF NOT EXISTS "pgcrypto";""")
    
    # users
    await conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        nickname TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    
    # books
    await conn.execute("""CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY, 
        title TEXT NOT NULL, 
        category TEXT NOT NULL, 
        author TEXT NOT NULL, 
        image_url TEXT NOT NULL,
        user_id UUID REFERENCES users(id),
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)
    
    # password reset tokens
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        token TEXT NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        used BOOLEAN DEFAULT FALSE
    );
    """)
    
    await conn.close()
    print("✅ tabelas criadas com sucesso !")