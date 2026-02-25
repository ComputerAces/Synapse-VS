import sqlite3
import os
from synapse.core.super_node import SuperNode
from synapse.core.dependencies import DependencyManager

# Lazy Globals
mysql_connector = None
pyodbc = None

def ensure_mysql():
    global mysql_connector
    if mysql_connector: return True
    if DependencyManager.ensure("mysql-connector-python", "mysql.connector"):
        import mysql.connector as _m; mysql_connector = _m; return True
    return False

def ensure_pyodbc():
    global pyodbc
    if pyodbc: return True
    if DependencyManager.ensure("pyodbc"):
        import pyodbc as _p; pyodbc = _p; return True
    return False

class BaseSQLNode(SuperNode):
    """
    Base class for SQL database operation nodes.
    
    Required Provider:
    - Database: Provides connection configuration.
    """
    version = "2.1.0"
    required_providers = ["DATABASE"]
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self._active_connection = None
        self._active_config_hash = None

    def get_connection(self, config_or_id):
        if not config_or_id:
            # TRY TO FIND PROVIDER AUTOMATICALLY BY TYPE
            # SuperNode context lookups
            provider_id = self.get_provider_id("DATABASE")
            if provider_id:
                config_or_id = provider_id
            
        if not config_or_id:
            raise ValueError("No database connection or provider context found.")
        
        # If it's a string, it's a Node ID
        if isinstance(config_or_id, str):
            config = self.bridge.get(f"{config_or_id}_Connection")
        else:
            config = config_or_id

        if not config:
            raise ValueError("Invalid connection handle.")

        # 1. Check Cache
        try:
            config_hash = hash(frozenset(config.items()))
        except:
            config_hash = str(config)

        if self._active_connection and self._active_config_hash == config_hash:
            return self._active_connection

        # 2. Close old if exists
        if self._active_connection:
            try: self._active_connection.close()
            except: pass

        # 3. Connect
        db_type = config.get("type", "sqlite")
        conn = None
        
        if db_type == "sqlite":
            conn = sqlite3.connect(config.get("path", "data.db"))
            # Enable dictionary access for rows
            conn.row_factory = sqlite3.Row
        elif db_type == "mysql":
            if not ensure_mysql(): raise Exception("mysql-connector-python not installed")
            conn = mysql_connector.connect(
                host=config.get("host"),
                user=config.get("user"),
                password=config.get("password"),
                database=config.get("database"),
                port=config.get("port")
            )
        elif db_type == "odbc":
            if not ensure_pyodbc(): raise Exception("pyodbc not installed")
            conn = pyodbc.connect(config.get("conn_str"))
        elif db_type in ("json", "csv"):
            conn = TextFileDBConnection(config, self.logger)
            conn.load()
        
        if conn:
            self._active_connection = conn
            self._active_config_hash = config_hash
            
        return conn

class TextFileDBConnection:
    """A shim that provides a sqlite3-compatible interface for JSON/CSV files."""
    def __init__(self, config, logger=None):
        self.config = config
        self.type = config.get("type")
        self.path = config.get("path")
        self.logger = logger
        self._memory_conn = sqlite3.connect(":memory:")
        self._memory_conn.row_factory = sqlite3.Row

    def cursor(self):
        return self._memory_conn.cursor()

    def commit(self):
        self.save()

    def close(self):
        self._memory_conn.close()

    def load(self):
        """Loads data from file/folder into in-memory SQLite."""
        if self.type == "json":
            self._load_json()
        elif self.type == "csv":
            self._load_csv()

    def save(self):
        """Saves data from in-memory SQLite back to file/folder."""
        if self.type == "json":
            self._save_json()
        elif self.type == "csv":
            self._save_csv()

    def _load_json(self):
        import json
        if not os.path.exists(self.path): return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tables = data.get("tables", {})
            for table_name, rows in tables.items():
                if not rows: continue
                cols = rows[0].keys()
                col_types = ", ".join([f"[{c}] TEXT" for c in cols])
                self._memory_conn.execute(f"CREATE TABLE [{table_name}] ({col_types})")
                placeholders = ", ".join(["?"] * len(cols))
                insert_sql = f"INSERT INTO [{table_name}] ({', '.join([f'[{c}]' for c in cols])}) VALUES ({placeholders})"
                for row in rows:
                    self._memory_conn.execute(insert_sql, [str(row.get(c, "")) for c in cols])
        except Exception as e:
            if self.logger: self.logger.error(f"[JSON DB] Load Error: {e}")

    def _save_json(self):
        import json
        data = {"tables": {}}
        cursor = self._memory_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"SELECT * FROM [{table}]")
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            data["tables"][table] = rows
        
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _load_csv(self):
        import csv
        if not os.path.exists(self.path) or not os.path.isdir(self.path): return
        for file in os.listdir(self.path):
            if file.endswith(".csv"):
                table_name = os.path.splitext(file)[0]
                full_path = os.path.join(self.path, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if not reader.fieldnames: continue
                        cols = reader.fieldnames
                        col_types = ", ".join([f"[{c}] TEXT" for c in cols])
                        self._memory_conn.execute(f"CREATE TABLE [{table_name}] ({col_types})")
                        placeholders = ", ".join(["?"] * len(cols))
                        insert_sql = f"INSERT INTO [{table_name}] ({', '.join([f'[{c}]' for c in cols])}) VALUES ({placeholders})"
                        for row in rows:
                            self._memory_conn.execute(insert_sql, [str(row.get(c, "")) for c in cols])
                except Exception as e:
                    if self.logger: self.logger.error(f"[CSV DB] Load Error ({file}): {e}")

    def _save_csv(self):
        import csv
        os.makedirs(self.path, exist_ok=True)
        cursor = self._memory_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"SELECT * FROM [{table}]")
            cols = [d[0] for d in cursor.description]
            full_path = os.path.join(self.path, f"{table}.csv")
            with open(full_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                for row in cursor.fetchall():
                    writer.writerow(dict(zip(cols, row)))
