def upgrade(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
    conn.commit()
