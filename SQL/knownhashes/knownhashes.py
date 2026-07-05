from _hashlib import HASH
from hashlib import md5
from pathlib import Path
from sqlite3 import connect

db_dir = Path("databases")
if not db_dir.exists():
    db_dir.mkdir()

conn = connect(db_dir / "known_hashes.db")
known_images_dir = Path(__file__).parent / "knownImages"


def init_db():
    conn.execute(
        """CREATE TABLE IF NOT EXISTS badHashes
        (
            id INTEGER PRIMARY KEY,
            hash TEXT UNIQUE
        )
        """
    )

    conn.commit()


init_db()


def add_hash(hash: HASH):
    conn.execute("INSERT OR IGNORE INTO badHashes (hash) VALUES (?)", (hash.hexdigest(),))
    conn.commit()


def get_hashes() -> list[str]:
    cur = conn.execute("SELECT hash FROM badHashed")
    results = cur.fetchall()
    return results


with open(r"SQL\knownhashes\knownImages\1522358530747924735_image.jpg", "rb") as f:
    add_hash(md5(f.read()))

with open(r"SQL\knownhashes\knownImages\1522358560930140353_image.jpg", "rb") as f:
    add_hash(md5(f.read()))
