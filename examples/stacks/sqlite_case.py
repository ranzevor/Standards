"""Real in-memory SQLite checks only; no file power-loss or other-engine claims."""
import sqlite3
from contextlib import closing

def check(condition,message):
    if not condition:raise RuntimeError(message)

with closing(sqlite3.connect(':memory:')) as db:
    db.execute('PRAGMA foreign_keys=ON')
    check(db.execute('PRAGMA foreign_keys').fetchone()[0]==1,'actual option')
    db.executescript('CREATE TABLE parent(id INTEGER PRIMARY KEY); CREATE TABLE items(id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id), value TEXT); INSERT INTO parent VALUES(1);')
    db.commit()
    hostile="x' OR 1=1; --"
    db.execute('INSERT INTO items VALUES(?,?,?)',(1,1,hostile))
    db.execute('INSERT INTO items VALUES(?,?,?)',(2,1,None));db.commit()
    check(db.execute('SELECT COUNT(*) FROM items WHERE value=?',(hostile,)).fetchone()[0]==1,'parameter stays data')
    check(db.execute('SELECT COUNT(*) FROM items WHERE value=NULL').fetchone()[0]==0,'NULL equality is not IS NULL')
    check(db.execute('SELECT COUNT(*) FROM items WHERE value IS NULL').fetchone()[0]==1,'legal NULL predicate')
    try:
        with db:
            db.execute('INSERT INTO items VALUES(?,?,?)',(3,1,'valid-first'))
            db.execute('INSERT INTO items VALUES(?,?,?)',(4,99,'invalid-foreign-key'))
    except sqlite3.IntegrityError:pass
    else:raise RuntimeError('foreign key guard absent')
    check(db.execute('SELECT COUNT(*) FROM items').fetchone()[0]==2,'whole transaction rollback')
    db.execute('INSERT INTO items VALUES(?,?,?)',(3,1,''));db.commit()
    check(db.execute('SELECT value FROM items WHERE id=3').fetchone()[0]=='','empty string is a legal distinct value')
print('sqlite-contract-ok version='+sqlite3.sqlite_version)
