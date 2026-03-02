"""SeekDB Database Client Module"""

from typing import Any, Optional

import pyseekdb as seekdb

from skillpilot.core.config import settings
from skillpilot.core.utils.logger import get_logger

logger = get_logger(__name__)


class SeekDBClient:
    """SeekDB database client with connection pooling and error handling"""

    _instance: Optional["SeekDBClient"] = None
    _client: Any | None = None

    def __new__(cls):
        """Singleton pattern for database client"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Any:
        """Connect to SeekDB"""
        if self._client is None:
            try:
                logger.info("Connecting to SeekDB", url=settings.seekdb_url)
                self._client = seekdb.connect(
                    url=settings.seekdb_url,
                    vector_dimension=settings.seekdb_vector_dimension,
                )
                logger.info("SeekDB connection established")
            except Exception as e:
                logger.error("Failed to connect to SeekDB", error=str(e), url=settings.seekdb_url)
                raise
        return self._client

    def close(self):
        """Close database connection"""
        if self._client:
            try:
                self._client.close()
                logger.info("SeekDB connection closed")
            except Exception as e:
                logger.warning("Error closing SeekDB connection", error=str(e))
            finally:
                self._client = None

    async def create_tables(self):
        """Create database tables if they don't exist"""
        client = self.connect()

        try:
            # Skills table
            await client.create_table(
                "skills",
                {
                    "skill_id": "string",
                    "skill_name": "string",
                    "platform": "string",
                    "developer": "string",
                    "description": "string",
                    "capabilities": "json",
                    "rating": "float",
                    "usage_count": "int",
                    "pricing": "json",
                    "tags": "json",
                    "created_at": "timestamp",
                    "updated_at": "timestamp",
                },
                primary_key="skill_id",
            )

            # Skill vectors table
            await client.create_table(
                "skill_vectors",
                {
                    "skill_id": "string",
                    "skill_vector": "vector",
                    "capability_vectors": "json",
                },
                primary_key="skill_id",
            )

            # Users table
            await client.create_table(
                "users",
                {
                    "user_id": "string",
                    "email": "string",
                    "password_hash": "string",
                    "name": "string",
                    "avatar_url": "string",
                    "role": "string",
                    "created_at": "timestamp",
                },
                primary_key="user_id",
            )

            # Orchestration plans table
            await client.create_table(
                "orchestration_plans",
                {
                    "plan_id": "string",
                    "user_id": "string",
                    "task_description": "string",
                    "skill_chain": "json",
                    "status": "string",
                    "created_at": "timestamp",
                    "executed_at": "timestamp",
                },
                primary_key="plan_id",
            )

            # Task vectors table
            await client.create_table(
                "task_vectors",
                {
                    "task_id": "string",
                    "task_description": "string",
                    "task_vector": "vector",
                    "required_capabilities": "json",
                },
                primary_key="task_id",
            )

            # Create vector indexes
            await client.create_vector_index(
                "skill_vectors",
                "idx_skill_vector",
                index_type=settings.seekdb_index_type,
                m=settings.seekdb_hnsw_m,
                ef_construction=settings.seekdb_hnsw_ef_construction,
            )

            await client.create_vector_index(
                "task_vectors",
                "idx_task_vector",
                index_type=settings.seekdb_index_type,
                m=settings.seekdb_hnsw_m,
                ef_construction=settings.seekdb_hnsw_ef_construction,
            )

            logger.info("Database tables created successfully")

        except Exception as e:
            logger.error("Failed to create tables", error=str(e))
            raise

    async def vector_search(
        self,
        table: str,
        vector_column: str,
        query_vector: list,
        top_k: int = 10,
        filter_conditions: dict | None = None,
    ) -> list:
        """Perform vector similarity search"""
        client = self.connect()
        try:
            return await client.vector_search(
                table=table,
                vector_column=vector_column,
                query_vector=query_vector,
                top_k=top_k,
                filter_conditions=filter_conditions,
            )
        except Exception as e:
            logger.error("Vector search failed", table=table, error=str(e))
            raise

    async def insert(self, table: str, data: dict) -> None:
        """Insert a record into table"""
        client = self.connect()
        try:
            await client.insert(table, data)
            logger.debug("Record inserted", table=table, id=data.get("id", "unknown"))
        except Exception as e:
            logger.error("Insert failed", table=table, error=str(e))
            raise

    async def update(self, table: str, primary_key: str, data: dict) -> None:
        """Update a record in table"""
        client = self.connect()
        try:
            await client.update(table, primary_key, data)
            logger.debug("Record updated", table=table, id=primary_key)
        except Exception as e:
            logger.error("Update failed", table=table, id=primary_key, error=str(e))
            raise

    async def delete(self, table: str, primary_key: str) -> None:
        """Delete a record from table"""
        client = self.connect()
        try:
            await client.delete(table, primary_key)
            logger.debug("Record deleted", table=table, id=primary_key)
        except Exception as e:
            logger.error("Delete failed", table=table, id=primary_key, error=str(e))
            raise

    async def get(self, table: str, primary_key: str) -> dict | None:
        """Get a single record by primary key"""
        client = self.connect()
        try:
            return await client.get(table, primary_key)
        except Exception as e:
            logger.error("Get failed", table=table, id=primary_key, error=str(e))
            raise

    async def query(
        self, table: str, filters: dict | None = None, limit: int = 100, offset: int = 0
    ) -> list:
        """Query records with optional filters"""
        client = self.connect()
        try:
            return await client.query(table, filters=filters, limit=limit, offset=offset)
        except Exception as e:
            logger.error("Query failed", table=table, filters=filters, error=str(e))
            raise


seekdb_client = SeekDBClient()
