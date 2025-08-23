#!/usr/bin/env python3
"""
Database Management Module

Provides comprehensive database operations including schema management,
migrations, query execution, and data manipulation for the AI Developer Assistant.
"""

import asyncio
import logging
import json
import sqlite3
import asyncpg
import aiomysql
import motor.motor_asyncio
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import uuid

from ..config.settings import get_settings


@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_type: str  # sqlite, postgresql, mysql, mongodb
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    connection_string: str = ""
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class TableSchema:
    """Database table schema"""
    name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class QueryResult:
    """Database query result"""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    affected_rows: int = 0
    execution_time: float = 0.0
    error_message: str = ""


class DatabaseManagement:
    """Database Management for various database operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Database connections
        self.connections: Dict[str, Any] = {}
        self.configs: Dict[str, DatabaseConfig] = {}
        
        # Migration system
        self.migrations: List[Dict[str, Any]] = []
        self.migration_history: List[Dict[str, Any]] = []
        
        # Schema cache
        self.schema_cache: Dict[str, Dict[str, TableSchema]] = {}
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "migrations_run": 0,
            "schemas_created": 0,
            "tables_created": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the database management system"""
        self.logger.info("Initializing Database Management...")
        
        # Create database workspace
        db_workspace = Path(self.settings.workspace_dir) / "database"
        db_workspace.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite for internal operations
        await self._initialize_internal_db()
        
        self.logger.info("Database Management initialized successfully")
    
    async def stop(self) -> None:
        """Stop the database management system"""
        self.logger.info("Stopping Database Management...")
        
        # Close all database connections
        for conn_name, connection in self.connections.items():
            try:
                if conn_name == "sqlite":
                    connection.close()
                elif conn_name in ["postgresql", "mysql"]:
                    await connection.close()
                elif conn_name == "mongodb":
                    connection.client.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection {conn_name}: {e}")
        
        self.connections.clear()
        self.logger.info("Database Management stopped")
    
    async def add_database(self, name: str, config: DatabaseConfig) -> Dict[str, Any]:
        """Add a new database connection"""
        try:
            # Test connection
            if config.db_type == "sqlite":
                connection = sqlite3.connect(config.database or f"{name}.db")
                self.connections[name] = connection
            elif config.db_type == "postgresql":
                if not config.connection_string:
                    config.connection_string = (
                        f"postgresql://{config.username}:{config.password}@"
                        f"{config.host}:{config.port}/{config.database}"
                    )
                connection = await asyncpg.create_pool(
                    config.connection_string,
                    min_size=1,
                    max_size=config.pool_size
                )
                self.connections[name] = connection
            elif config.db_type == "mysql":
                if not config.connection_string:
                    config.connection_string = (
                        f"mysql://{config.username}:{config.password}@"
                        f"{config.host}:{config.port}/{config.database}"
                    )
                connection = await aiomysql.create_pool(
                    host=config.host,
                    port=config.port,
                    user=config.username,
                    password=config.password,
                    db=config.database,
                    minsize=1,
                    maxsize=config.pool_size
                )
                self.connections[name] = connection
            elif config.db_type == "mongodb":
                if not config.connection_string:
                    config.connection_string = (
                        f"mongodb://{config.username}:{config.password}@"
                        f"{config.host}:{config.port}/{config.database}"
                    )
                client = motor.motor_asyncio.AsyncIOMotorClient(config.connection_string)
                connection = client[config.database]
                self.connections[name] = connection
            else:
                return {"error": f"Unsupported database type: {config.db_type}"}
            
            # Store configuration
            self.configs[name] = config
            
            # Cache schema
            await self._cache_schema(name)
            
            return {
                "success": True,
                "database_name": name,
                "db_type": config.db_type,
                "message": f"Database '{name}' connected successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error adding database '{name}': {e}")
            return {"error": str(e)}
    
    async def execute_query(self, database: str, query: str, 
                           params: Optional[List[Any]] = None) -> QueryResult:
        """Execute a database query"""
        start_time = datetime.now()
        self.stats["total_queries"] += 1
        
        try:
            if database not in self.connections:
                return QueryResult(
                    success=False,
                    error_message=f"Database '{database}' not found"
                )
            
            config = self.configs[database]
            connection = self.connections[database]
            
            if config.db_type == "sqlite":
                result = await self._execute_sqlite_query(connection, query, params)
            elif config.db_type == "postgresql":
                result = await self._execute_postgresql_query(connection, query, params)
            elif config.db_type == "mysql":
                result = await self._execute_mysql_query(connection, query, params)
            elif config.db_type == "mongodb":
                result = await self._execute_mongodb_query(connection, query, params)
            else:
                return QueryResult(
                    success=False,
                    error_message=f"Unsupported database type: {config.db_type}"
                )
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            if result.success:
                self.stats["successful_queries"] += 1
            else:
                self.stats["failed_queries"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_queries"] += 1
            return QueryResult(
                success=False,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def create_table(self, database: str, schema: TableSchema) -> Dict[str, Any]:
        """Create a database table"""
        try:
            if database not in self.connections:
                return {"error": f"Database '{database}' not found"}
            
            config = self.configs[database]
            
            if config.db_type == "sqlite":
                create_sql = self._generate_sqlite_create_table(schema)
                result = await self.execute_query(database, create_sql)
            elif config.db_type == "postgresql":
                create_sql = self._generate_postgresql_create_table(schema)
                result = await self.execute_query(database, create_sql)
            elif config.db_type == "mysql":
                create_sql = self._generate_mysql_create_table(schema)
                result = await self.execute_query(database, create_sql)
            elif config.db_type == "mongodb":
                # MongoDB doesn't have explicit table creation
                result = QueryResult(success=True)
            else:
                return {"error": f"Unsupported database type: {config.db_type}"}
            
            if result.success:
                self.stats["tables_created"] += 1
                
                # Update schema cache
                if database not in self.schema_cache:
                    self.schema_cache[database] = {}
                self.schema_cache[database][schema.name] = schema
                
                return {
                    "success": True,
                    "table_name": schema.name,
                    "message": f"Table '{schema.name}' created successfully"
                }
            else:
                return {"error": result.error_message}
                
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            return {"error": str(e)}
    
    async def create_migration(self, name: str, database: str, 
                             up_sql: str, down_sql: str) -> Dict[str, Any]:
        """Create a database migration"""
        try:
            migration_id = str(uuid.uuid4())
            migration = {
                "id": migration_id,
                "name": name,
                "database": database,
                "up_sql": up_sql,
                "down_sql": down_sql,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            self.migrations.append(migration)
            
            # Store migration in internal database
            await self._store_migration(migration)
            
            return {
                "success": True,
                "migration_id": migration_id,
                "name": name,
                "message": f"Migration '{name}' created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating migration: {e}")
            return {"error": str(e)}
    
    async def run_migration(self, migration_id: str) -> Dict[str, Any]:
        """Run a database migration"""
        try:
            migration = None
            for m in self.migrations:
                if m["id"] == migration_id:
                    migration = m
                    break
            
            if not migration:
                return {"error": f"Migration '{migration_id}' not found"}
            
            if migration["status"] == "completed":
                return {"error": f"Migration '{migration_id}' already completed"}
            
            # Execute up migration
            result = await self.execute_query(migration["database"], migration["up_sql"])
            
            if result.success:
                migration["status"] = "completed"
                migration["completed_at"] = datetime.now().isoformat()
                self.stats["migrations_run"] += 1
                
                # Update migration history
                await self._update_migration_history(migration)
                
                return {
                    "success": True,
                    "migration_id": migration_id,
                    "message": f"Migration '{migration['name']}' completed successfully"
                }
            else:
                return {"error": result.error_message}
                
        except Exception as e:
            self.logger.error(f"Error running migration: {e}")
            return {"error": str(e)}
    
    async def rollback_migration(self, migration_id: str) -> Dict[str, Any]:
        """Rollback a database migration"""
        try:
            migration = None
            for m in self.migrations:
                if m["id"] == migration_id:
                    migration = m
                    break
            
            if not migration:
                return {"error": f"Migration '{migration_id}' not found"}
            
            if migration["status"] != "completed":
                return {"error": f"Migration '{migration_id}' is not completed"}
            
            # Execute down migration
            result = await self.execute_query(migration["database"], migration["down_sql"])
            
            if result.success:
                migration["status"] = "rolled_back"
                migration["rolled_back_at"] = datetime.now().isoformat()
                
                # Update migration history
                await self._update_migration_history(migration)
                
                return {
                    "success": True,
                    "migration_id": migration_id,
                    "message": f"Migration '{migration['name']}' rolled back successfully"
                }
            else:
                return {"error": result.error_message}
                
        except Exception as e:
            self.logger.error(f"Error rolling back migration: {e}")
            return {"error": str(e)}
    
    async def get_schema(self, database: str) -> Dict[str, Any]:
        """Get database schema"""
        try:
            if database not in self.schema_cache:
                await self._cache_schema(database)
            
            schema = self.schema_cache.get(database, {})
            
            return {
                "success": True,
                "database": database,
                "schema": {name: self._schema_to_dict(table) for name, table in schema.items()}
            }
            
        except Exception as e:
            self.logger.error(f"Error getting schema: {e}")
            return {"error": str(e)}
    
    async def backup_database(self, database: str, backup_path: str) -> Dict[str, Any]:
        """Backup a database"""
        try:
            if database not in self.connections:
                return {"error": f"Database '{database}' not found"}
            
            config = self.configs[database]
            
            if config.db_type == "sqlite":
                # SQLite backup is just file copy
                import shutil
                shutil.copy2(config.database, backup_path)
            else:
                # For other databases, use dump commands
                if config.db_type == "postgresql":
                    dump_cmd = f"pg_dump {config.database} > {backup_path}"
                elif config.db_type == "mysql":
                    dump_cmd = f"mysqldump {config.database} > {backup_path}"
                else:
                    return {"error": f"Backup not supported for {config.db_type}"}
                
                process = await asyncio.create_subprocess_shell(
                    dump_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            
            return {
                "success": True,
                "database": database,
                "backup_path": backup_path,
                "message": f"Database '{database}' backed up successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error backing up database: {e}")
            return {"error": str(e)}
    
    async def restore_database(self, database: str, backup_path: str) -> Dict[str, Any]:
        """Restore a database from backup"""
        try:
            if database not in self.connections:
                return {"error": f"Database '{database}' not found"}
            
            config = self.configs[database]
            
            if config.db_type == "sqlite":
                # SQLite restore is just file copy
                import shutil
                shutil.copy2(backup_path, config.database)
            else:
                # For other databases, use restore commands
                if config.db_type == "postgresql":
                    restore_cmd = f"psql {config.database} < {backup_path}"
                elif config.db_type == "mysql":
                    restore_cmd = f"mysql {config.database} < {backup_path}"
                else:
                    return {"error": f"Restore not supported for {config.db_type}"}
                
                process = await asyncio.create_subprocess_shell(
                    restore_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            
            return {
                "success": True,
                "database": database,
                "backup_path": backup_path,
                "message": f"Database '{database}' restored successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error restoring database: {e}")
            return {"error": str(e)}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database management statistics"""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "databases": list(self.connections.keys()),
            "migrations": len(self.migrations),
            "migration_history": len(self.migration_history)
        }
    
    async def _initialize_internal_db(self) -> None:
        """Initialize internal SQLite database for management"""
        internal_db_path = Path(self.settings.workspace_dir) / "database" / "internal.db"
        
        connection = sqlite3.connect(str(internal_db_path))
        self.connections["internal"] = connection
        
        # Create management tables
        cursor = connection.cursor()
        
        # Migrations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                database TEXT NOT NULL,
                up_sql TEXT NOT NULL,
                down_sql TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                completed_at TEXT,
                rolled_back_at TEXT
            )
        ''')
        
        # Migration history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (migration_id) REFERENCES migrations (id)
            )
        ''')
        
        connection.commit()
    
    async def _store_migration(self, migration: Dict[str, Any]) -> None:
        """Store migration in internal database"""
        if "internal" not in self.connections:
            return
        
        connection = self.connections["internal"]
        cursor = connection.cursor()
        
        cursor.execute('''
            INSERT INTO migrations (id, name, database, up_sql, down_sql, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            migration["id"], migration["name"], migration["database"],
            migration["up_sql"], migration["down_sql"],
            migration["created_at"], migration["status"]
        ))
        
        connection.commit()
    
    async def _update_migration_history(self, migration: Dict[str, Any]) -> None:
        """Update migration history"""
        if "internal" not in self.connections:
            return
        
        connection = self.connections["internal"]
        cursor = connection.cursor()
        
        action = "completed" if migration["status"] == "completed" else "rolled_back"
        
        cursor.execute('''
            INSERT INTO migration_history (migration_id, action, timestamp)
            VALUES (?, ?, ?)
        ''', (migration["id"], action, datetime.now().isoformat()))
        
        # Update migration status
        cursor.execute('''
            UPDATE migrations 
            SET status = ?, completed_at = ?, rolled_back_at = ?
            WHERE id = ?
        ''', (
            migration["status"],
            migration.get("completed_at"),
            migration.get("rolled_back_at"),
            migration["id"]
        ))
        
        connection.commit()
    
    async def _cache_schema(self, database: str) -> None:
        """Cache database schema"""
        try:
            if database not in self.connections:
                return
            
            config = self.configs[database]
            
            if config.db_type == "sqlite":
                await self._cache_sqlite_schema(database)
            elif config.db_type == "postgresql":
                await self._cache_postgresql_schema(database)
            elif config.db_type == "mysql":
                await self._cache_mysql_schema(database)
            elif config.db_type == "mongodb":
                await self._cache_mongodb_schema(database)
                
        except Exception as e:
            self.logger.warning(f"Could not cache schema for {database}: {e}")
    
    async def _cache_sqlite_schema(self, database: str) -> None:
        """Cache SQLite schema"""
        connection = self.connections[database]
        cursor = connection.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        for (table_name,) in tables:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            table_schema = TableSchema(name=table_name, columns=[])
            
            for col in columns:
                column_info = {
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                }
                table_schema.columns.append(column_info)
                
                if col[5]:  # Primary key
                    table_schema.primary_keys.append(col[1])
            
            schema[table_name] = table_schema
        
        self.schema_cache[database] = schema
    
    async def _cache_postgresql_schema(self, database: str) -> None:
        """Cache PostgreSQL schema"""
        # This would be implemented with PostgreSQL-specific queries
        pass
    
    async def _cache_mysql_schema(self, database: str) -> None:
        """Cache MySQL schema"""
        # This would be implemented with MySQL-specific queries
        pass
    
    async def _cache_mongodb_schema(self, database: str) -> None:
        """Cache MongoDB schema"""
        # This would be implemented with MongoDB-specific queries
        pass
    
    async def _execute_sqlite_query(self, connection: sqlite3.Connection, 
                                  query: str, params: Optional[List[Any]] = None) -> QueryResult:
        """Execute SQLite query"""
        cursor = connection.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return QueryResult(success=True, data=data)
            else:
                affected_rows = cursor.rowcount
                connection.commit()
                return QueryResult(success=True, affected_rows=affected_rows)
                
        except Exception as e:
            connection.rollback()
            return QueryResult(success=False, error_message=str(e))
    
    async def _execute_postgresql_query(self, connection, query: str, 
                                      params: Optional[List[Any]] = None) -> QueryResult:
        """Execute PostgreSQL query"""
        async with connection.acquire() as conn:
            try:
                if query.strip().upper().startswith("SELECT"):
                    if params:
                        rows = await conn.fetch(query, *params)
                    else:
                        rows = await conn.fetch(query)
                    
                    data = [dict(row) for row in rows]
                    return QueryResult(success=True, data=data)
                else:
                    if params:
                        result = await conn.execute(query, *params)
                    else:
                        result = await conn.execute(query)
                    
                    affected_rows = int(result.split()[-1]) if result else 0
                    return QueryResult(success=True, affected_rows=affected_rows)
                    
            except Exception as e:
                return QueryResult(success=False, error_message=str(e))
    
    async def _execute_mysql_query(self, connection, query: str, 
                                 params: Optional[List[Any]] = None) -> QueryResult:
        """Execute MySQL query"""
        async with connection.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    if params:
                        await cursor.execute(query, params)
                    else:
                        await cursor.execute(query)
                    
                    if query.strip().upper().startswith("SELECT"):
                        columns = [description[0] for description in cursor.description]
                        rows = await cursor.fetchall()
                        data = [dict(zip(columns, row)) for row in rows]
                        return QueryResult(success=True, data=data)
                    else:
                        affected_rows = cursor.rowcount
                        await conn.commit()
                        return QueryResult(success=True, affected_rows=affected_rows)
                        
                except Exception as e:
                    await conn.rollback()
                    return QueryResult(success=False, error_message=str(e))
    
    async def _execute_mongodb_query(self, connection, query: str, 
                                   params: Optional[List[Any]] = None) -> QueryResult:
        """Execute MongoDB query"""
        try:
            # Parse MongoDB query (simplified)
            if query.strip().upper().startswith("FIND"):
                collection_name = query.split()[1]
                filter_dict = json.loads(params[0]) if params else {}
                
                collection = connection[collection_name]
                cursor = collection.find(filter_dict)
                data = await cursor.to_list(length=100)
                
                return QueryResult(success=True, data=data)
            elif query.strip().upper().startswith("INSERT"):
                collection_name = query.split()[1]
                document = json.loads(params[0]) if params else {}
                
                collection = connection[collection_name]
                result = await collection.insert_one(document)
                
                return QueryResult(success=True, affected_rows=1)
            else:
                return QueryResult(success=False, error_message="Unsupported MongoDB query")
                
        except Exception as e:
            return QueryResult(success=False, error_message=str(e))
    
    def _generate_sqlite_create_table(self, schema: TableSchema) -> str:
        """Generate SQLite CREATE TABLE statement"""
        columns_sql = []
        
        for column in schema.columns:
            column_def = f"{column['name']} {column['type']}"
            
            if column.get('not_null', False):
                column_def += " NOT NULL"
            
            if column.get('primary_key', False):
                column_def += " PRIMARY KEY"
            
            if 'default_value' in column and column['default_value']:
                column_def += f" DEFAULT {column['default_value']}"
            
            columns_sql.append(column_def)
        
        sql = f"CREATE TABLE {schema.name} (\n    " + ",\n    ".join(columns_sql) + "\n)"
        
        return sql
    
    def _generate_postgresql_create_table(self, schema: TableSchema) -> str:
        """Generate PostgreSQL CREATE TABLE statement"""
        # Similar to SQLite but with PostgreSQL-specific syntax
        return self._generate_sqlite_create_table(schema)
    
    def _generate_mysql_create_table(self, schema: TableSchema) -> str:
        """Generate MySQL CREATE TABLE statement"""
        # Similar to SQLite but with MySQL-specific syntax
        return self._generate_sqlite_create_table(schema)
    
    def _schema_to_dict(self, schema: TableSchema) -> Dict[str, Any]:
        """Convert TableSchema to dictionary"""
        return {
            "name": schema.name,
            "columns": schema.columns,
            "primary_keys": schema.primary_keys,
            "foreign_keys": schema.foreign_keys,
            "indexes": schema.indexes,
            "constraints": schema.constraints
        }