"""
One-off script: creates the django_site table and fakes the sites migrations
so that 'manage.py migrate' can proceed cleanly.
Run with:  .\\env\\Scripts\\python fix_migrations.py
"""
import sqlite3, pathlib, datetime

db_path = pathlib.Path(__file__).parent / 'db.sqlite3'
now = datetime.datetime.now(datetime.UTC).isoformat()

con = sqlite3.connect(str(db_path))
cur = con.cursor()

# 1. Create the django_site table if it doesn't exist yet
cur.execute("""
    CREATE TABLE IF NOT EXISTS django_site (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        domain VARCHAR(100) NOT NULL UNIQUE,
        name VARCHAR(50) NOT NULL
    )
""")
print("Ensured django_site table exists.")

# 2. Insert the default example.com site (id=1 matches SITE_ID=1 in settings)
cur.execute(
    "INSERT OR IGNORE INTO django_site (id, domain, name) VALUES (1, 'example.com', 'example.com')"
)
print("Ensured default site row exists.")

# 3. Fake-mark the sites migrations as applied so Django doesn't try to re-run them
migrations_to_fake = [
    ('sites', '0001_initial'),
    ('sites', '0002_alter_domain_unique'),
]
for app, name in migrations_to_fake:
    cur.execute(
        "INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
        (app, name, now)
    )
    print(f"Faked migration: {app} - {name}")

con.commit()
con.close()
print("\nDone. Run: .\\env\\Scripts\\python manage.py migrate")
