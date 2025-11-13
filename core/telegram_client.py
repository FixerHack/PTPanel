import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class TelegramClientManager:
    """Manager for Telegram client operations"""
    
    def __init__(self):
        self.clients = {}
        logger.info("TelegramClientManager initialized")
    
    async def create_client(self, session_name: str, api_id: int, api_hash: str, 
                          phone: Optional[str] = None, proxy: Optional[Dict] = None):
        """Create a new Telegram client"""
        try:
            from telethon import TelegramClient
            
            client = TelegramClient(
                session=f"sessions/{session_name}",
                api_id=api_id,
                api_hash=api_hash
            )
            
            await client.start(phone=phone)
            self.clients[session_name] = client
            logger.info(f"Telegram client created for session: {session_name}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create Telegram client: {e}")
            raise
    
    async def disconnect_client(self, session_name: str):
        """Disconnect Telegram client"""
        try:
            if session_name in self.clients:
                await self.clients[session_name].disconnect()
                del self.clients[session_name]
                logger.info(f"Telegram client disconnected: {session_name}")
        except Exception as e:
            logger.error(f"Failed to disconnect Telegram client: {e}")
    
    def get_client(self, session_name: str):
        """Get Telegram client by session name"""
        return self.clients.get(session_name)

# Global instance
telegram_client_manager = TelegramClientManager()