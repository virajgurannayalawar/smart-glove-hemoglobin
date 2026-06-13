"""
Main entry point for Smart Glove Edge Firmware.

Orchestrates the complete firmware startup and operation:
- Configuration validation
- HTTP server startup
- Background worker management
- Graceful shutdown handling
"""

import asyncio
import signal
import logging
import sys
from pathlib import Path

from .config import config
from .server import start_server


# Configure logging
def setup_logging():
    """Configure structured logging for the firmware."""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    if config.LOG_FORMAT == "json":
        # JSON logging for production (can be parsed by log aggregators)
        try:
            import structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
            logging.basicConfig(
                format="%(message)s",
                level=log_level
            )
            return structlog.get_logger()
        except ImportError:
            # Fallback to standard logging if structlog not available
            logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                level=log_level
            )
            return logging.getLogger(__name__)
    else:
        # Text logging for development
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=log_level
        )
        return logging.getLogger(__name__)


logger = setup_logging()


class FirmwareSupervisor:
    """
    Main supervisor for the edge firmware.
    
    Manages the HTTP server and background workers.
    Handles graceful shutdown on SIGTERM/SIGINT.
    """
    
    def __init__(self):
        self.server_task = None
        self.cache_worker_task = None
        self.shutdown_event = asyncio.Event()
    
    def validate_configuration(self) -> bool:
        """
        Validate that required configuration is present and correct.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        logger.info("Validating configuration...")
        
        try:
            config.validate()
            logger.info("Configuration validation passed")
            return True
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        logger.info("Ensuring required directories exist...")
        
        try:
            config.ensure_cache_dir()
            logger.info(f"Cache directory ready: {config.CACHE_DIR}")
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise
    
    async def start_cache_worker(self):
        """
        Start the background cache retry worker.
        
        This worker processes failed uploads from the offline cache.
        """
        try:
            from .cache import CacheWorker
            cache_worker = CacheWorker()
            await cache_worker.run(self.shutdown_event)
        except ImportError:
            logger.warning("Cache module not available, skipping cache worker")
        except Exception as e:
            logger.error(f"Cache worker failed: {e}")
    
    async def run(self):
        """
        Main run loop for the firmware.
        
        Starts the HTTP server and background workers.
        Waits for shutdown signal.
        """
        logger.info("=" * 60)
        logger.info("Smart Glove Edge Firmware Starting")
        logger.info("=" * 60)
        
        # Validate configuration
        self.validate_configuration()
        
        # Ensure directories
        self.ensure_directories()
        
        # Log configuration summary
        logger.info(f"Owner ID: {config.OWNER_ID}")
        logger.info(f"Backend URL: {config.BACKEND_BASE_URL}")
        logger.info(f"Server: {config.SERVER_HOST}:{config.SERVER_PORT}")
        logger.info(f"Camera: {config.CAMERA_RESOLUTION} @ index {config.CAMERA_INDEX}")
        logger.info(f"GPIO Power Control: {config.ENABLE_GPIO_POWER_CONTROL}")
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown())
            )
        
        # Start background tasks
        tasks = []
        
        # Start cache worker
        self.cache_worker_task = asyncio.create_task(self.start_cache_worker())
        tasks.append(self.cache_worker_task)
        
        # Start HTTP server (this blocks)
        logger.info("Starting HTTP server...")
        try:
            # The server runs in the current task
            start_server()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """
        Graceful shutdown procedure.
        
        Cancels background tasks and cleans up resources.
        """
        if self.shutdown_event.is_set():
            return
        
        logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()
        
        # Cancel background tasks
        if self.cache_worker_task and not self.cache_worker_task.done():
            logger.info("Stopping cache worker...")
            self.cache_worker_task.cancel()
            try:
                await self.cache_worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Shutdown complete")


def main():
    """
    Main entry point for the firmware.
    
    Called when running: python -m edge_firmware.main
    """
    try:
        supervisor = FirmwareSupervisor()
        asyncio.run(supervisor.run())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Firmware startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
