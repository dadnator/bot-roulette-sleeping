import sqlite3
import os

print("📂 Fichier SQLite inspecté :", os.path.abspath("roulette_stats.db"))

conn = sqlite3.connect("roulette_stats.db")
c = conn.cursor()

# Liste toutes les tables existantes
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()

if not tables:
    print("📭 Aucune table trouvée dans la base.")
else:
    print("📋 Tables trouvées :", [t[0] for t in tables])
