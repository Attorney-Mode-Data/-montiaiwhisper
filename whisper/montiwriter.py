# Add to utils.py (or a separate monti_writer.py)
import sqlite3

class WriteSQLite(ResultWriter):
    extension: str = "sqlite"

    def write_result(self, result: dict, file=None, options=None, **kwargs):
        db_path = os.path.join(self.output_dir, "montidroid.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_path TEXT,
                start REAL,
                end REAL,
                text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for segment in result["segments"]:
            cur.execute(
                "INSERT INTO transcripts (audio_path, start, end, text) VALUES (?, ?, ?, ?)",
                (kwargs.get("audio_path"), segment["start"], segment["end"], segment["text"])
            )
        conn.commit()
        conn.close()
