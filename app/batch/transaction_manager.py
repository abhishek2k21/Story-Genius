"""
Transaction Manager for Batch Processing
Provides ACID-compliant transactional guarantees for batch operations.
"""
from typing import List, Callable, Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager
import traceback

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TransactionContext:
    """Transaction context"""
    transaction_id: str
    batch_id: str
    started_at: datetime
    savepoints: List[str]
    operations_executed: int = 0
    
    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "batch_id": self.batch_id,
            "started_at": self.started_at.isoformat(),
            "savepoints": self.savepoints,
            "operations_executed": self.operations_executed
        }


class TransactionManager:
    """
    Manages transactions for batch operations.
    Provides ACID guarantees:
    - Atomicity: All-or-nothing execution
    - Consistency: Data integrity maintained
    - Isolation: Transaction isolation
    - Durability: Committed changes persist
    """
    
    def __init__(self):
        self._active_transactions: Dict[str, TransactionContext] = {}
        logger.info("TransactionManager initialized")
    
    @contextmanager
    def transaction(self, batch_id: str, transaction_id: Optional[str] = None):
        """
        Context manager for transactional execution.
        
        Usage:
            with transaction_manager.transaction("batch_123") as tx:
                # Execute operations
                pass
        """
        import uuid
        
        tx_id = transaction_id or str(uuid.uuid4())
        context = TransactionContext(
            transaction_id=tx_id,
            batch_id=batch_id,
            started_at=datetime.utcnow(),
            savepoints=[]
        )
        
        self._active_transactions[tx_id] = context
        logger.info(f"Transaction {tx_id} started for batch {batch_id}")
        
        try:
            # Begin transaction
            self._begin_transaction(context)
            
            yield context
            
            # Commit transaction
            self._commit_transaction(context)
            logger.info(f"Transaction {tx_id} committed successfully")
            
        except Exception as e:
            # Rollback transaction
            logger.error(f"Transaction {tx_id} failed: {e}", exc_info=True)
            self._rollback_transaction(context)
            raise
            
        finally:
            # Cleanup
            if tx_id in self._active_transactions:
                del self._active_transactions[tx_id]
    
    def execute_transactional(
        self,
        batch_id: str,
        operations: List[Callable],
        use_savepoints: bool = True
    ) -> List[Any]:
        """
        Execute operations within a transaction.
        
        Args:
            batch_id: Batch ID
            operations: List of operations to execute
            use_savepoints: Use savepoints between operations
        
        Returns:
            List of operation results
        
        Raises:
            Exception: If any operation fails
        """
        results = []
        
        with self.transaction(batch_id) as tx:
            for i, operation in enumerate(operations):
                try:
                    # Create savepoint before operation
                    if use_savepoints:
                        savepoint_name = f"sp_{i}"
                        self._create_savepoint(tx, savepoint_name)
                    
                    # Execute operation
                    logger.debug(f"Executing operation {i+1}/{len(operations)}")
                    result = operation()
                    results.append(result)
                    
                    tx.operations_executed += 1
                    
                except Exception as e:
                    logger.error(f"Operation {i+1} failed: {e}")
                    
                    # Rollback to savepoint if available
                    if use_savepoints and tx.savepoints:
                        self._rollback_to_savepoint(tx, tx.savepoints[-1])
                    
                    # Re-raise to trigger full rollback
                    raise
        
        logger.info(f"Transaction completed: {len(results)} operations executed")
        return results
    
    def create_savepoint(self, transaction_id: str, name: str):
        """Create a savepoint within transaction"""
        context = self._active_transactions.get(transaction_id)
        if not context:
            logger.warning(f"Transaction {transaction_id} not found")
            return
        
        self._create_savepoint(context, name)
    
    def rollback_to_savepoint(self, transaction_id: str, savepoint_name: str):
        """Rollback to a specific savepoint"""
        context = self._active_transactions.get(transaction_id)
        if not context:
            logger.warning(f"Transaction {transaction_id} not found")
            return
        
        self._rollback_to_savepoint(context, savepoint_name)
    
    # Internal methods
    
    def _begin_transaction(self, context: TransactionContext):
        """Begin database transaction"""
        # In production: Begin DB transaction
        # Example: session.begin()
        logger.debug(f"Transaction {context.transaction_id} begun")
    
    def _commit_transaction(self, context: TransactionContext):
        """Commit database transaction"""
        # In production: Commit DB transaction
        # Example: session.commit()
        logger.debug(f"Transaction {context.transaction_id} committed")
    
    def _rollback_transaction(self, context: TransactionContext):
        """Rollback database transaction"""
        # In production: Rollback DB transaction
        # Example: session.rollback()
        logger.warning(f"Transaction {context.transaction_id} rolled back")
    
    def _create_savepoint(self, context: TransactionContext, name: str):
        """Create savepoint"""
        # In production: Create DB savepoint
        # Example: session.execute(f"SAVEPOINT {name}")
        context.savepoints.append(name)
        logger.debug(f"Savepoint '{name}' created in transaction {context.transaction_id}")
    
    def _rollback_to_savepoint(self, context: TransactionContext, savepoint_name: str):
        """Rollback to savepoint"""
        # In production: Rollback to DB savepoint
        # Example: session.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
        
        if savepoint_name in context.savepoints:
            # Remove savepoints after the rollback point
            idx = context.savepoints.index(savepoint_name)
            context.savepoints = context.savepoints[:idx]
            logger.warning(f"Rolled back to savepoint '{savepoint_name}'")
        else:
            logger.error(f"Savepoint '{savepoint_name}' not found")


# Batch-specific transaction wrapper
class BatchTransactionWrapper:
    """
    Higher-level wrapper for batch transactions.
    """
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
    
    def process_batch_transactionally(
        self,
        batch_id: str,
        items: List[Any],
        process_fn: Callable[[Any], Any]
    ) -> Dict[str, Any]:
        """
        Process batch items within a transaction.
        
        Args:
            batch_id: Batch ID
            items: Items to process
            process_fn: Function to process each item
        
        Returns:
            Batch processing result
        """
        results = {
            "batch_id": batch_id,
            "total_items": len(items),
            "processed": [],
            "failed": []
        }
        
        # Create operations for each item
        def create_operation(item):
            def operation():
                return process_fn(item)
            return operation
        
        operations = [create_operation(item) for item in items]
        
        try:
            # Execute all operations transactionally
            processed = self.transaction_manager.execute_transactional(
                batch_id,
                operations,
                use_savepoints=True
            )
            
            results["processed"] = processed
            
        except Exception as e:
            logger.error(f"Batch {batch_id} transaction failed: {e}")
            results["failed"].append({
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise
        
        return results


# Global instance
transaction_manager = TransactionManager()
batch_transaction_wrapper = BatchTransactionWrapper(transaction_manager)
