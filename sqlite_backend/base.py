# Custom SQLite backend that enables foreign keys

from django.db.backends.sqlite3.base import DatabaseWrapper as SQLite3DatabaseWrapper


class DatabaseWrapper(SQLite3DatabaseWrapper):
    """Custom SQLite wrapper that enables FOREIGN_KEYS pragma on every connection"""
    
    def get_new_connection(self, conn_params):
        """Get new connection with foreign keys enabled"""
        conn = super().get_new_connection(conn_params)
        conn.execute('PRAGMA foreign_keys = ON')
        return conn



