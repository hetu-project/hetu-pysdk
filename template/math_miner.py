#!/usr/bin/env python3
"""
Math Miner Template - A Xylem server providing mathematical services.
This template demonstrates how to create a miner service using the protocol layer.
"""

import asyncio
import logging
from hetu.xylem import Xylem
from hetu.utils.wallet import unlock_wallet

# Import from protocol layer
from protocol import MathSumSynapse, MathProductSynapse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MathMiner:
    """Math miner service providing addition and multiplication.
    
    This template shows how to create a miner service that:
    1. Uses the protocol layer for Synapse definitions
    2. Implements service logic as async functions
    3. Attaches services to a Xylem server
    4. Handles errors gracefully
    """
    
    def __init__(self, wallet, netuid: int = 1, network: str = "mainnet", 
                 port: int = 8091, ip: str = "127.0.0.1"):
        """Initialize the math miner service.
        
        Args:
            wallet: Pre-initialized wallet Account object
            netuid (int): Subnet ID to operate on
            network (str): Network name (mainnet, testnet, etc.)
            port (int): Port to run the server on
            ip (str): IP address to bind to
        """
        self.wallet = wallet
        self.netuid = netuid
        self.network = network
        self.port = port
        self.ip = ip
        
        # Create Xylem server
        self.xylem = Xylem(
            wallet=wallet,
            port=port,
            ip=ip,
            external_ip=ip,
            external_port=port,
            netuid=netuid,
            network=network
        )
        
        # Attach services
        self._attach_services()
        
        logger.info(f"✅ Math miner initialized for subnet {netuid}")
        logger.info(f"   Wallet: {wallet.address}")
        logger.info(f"   Services: Addition, Multiplication")
        logger.info(f"   Endpoint: http://{ip}:{port}")
    
    def _attach_services(self):
        """Attach mathematical services to the Xylem server."""
        
        # Addition service
        async def addition_service(synapse: MathSumSynapse) -> MathSumSynapse:
            """Handle addition requests.
            
            Args:
                synapse: MathSumSynapse instance with x, y parameters
                
            Returns:
                MathSumSynapse with computed result and status
            """
            try:
                # Calculate result using the synapse's property
                result = synapse.sum_result
                
                # Set completion message and status
                synapse.completion = f"Result: {result}"
                synapse.status_code = 200
                
                # Log the operation
                logger.info(f"➕ Addition: {synapse.x} + {synapse.y} = {result}")
                
                return synapse
                
            except Exception as e:
                # Handle errors gracefully
                error_msg = f"Addition failed: {str(e)}"
                synapse.error = error_msg
                synapse.status_code = 500
                logger.error(f"❌ Addition error: {error_msg}")
                return synapse
        
        # Multiplication service
        async def multiplication_service(synapse: MathProductSynapse) -> MathProductSynapse:
            """Handle multiplication requests.
            
            Args:
                synapse: MathProductSynapse instance with x, y parameters
                
            Returns:
                MathProductSynapse with computed result and status
            """
            try:
                # Calculate result using the synapse's property
                result = synapse.product_result
                
                # Set completion message and status
                synapse.completion = f"Result: {result}"
                synapse.status_code = 200
                
                # Log the operation
                logger.info(f"✖️ Multiplication: {synapse.x} × {synapse.y} = {result}")
                
                return synapse
                
            except Exception as e:
                # Handle errors gracefully
                error_msg = f"Multiplication failed: {str(e)}"
                synapse.error = error_msg
                synapse.status_code = 500
                logger.error(f"❌ Multiplication error: {error_msg}")
                return synapse
        
        # Attach services to Xylem
        self.xylem.attach(forward_fn=addition_service)
        self.xylem.attach(forward_fn=multiplication_service)
        
        logger.info("✅ Math services attached to Xylem")
    
    async def start(self):
        """Start the math miner service."""
        try:
            logger.info(f"🚀 Starting math miner service on subnet {self.netuid}...")
            
            # Start the Xylem server
            self.xylem.start()
            
            # Wait a bit for server to start
            await asyncio.sleep(3)
            
            logger.info(f"✅ Math miner service started successfully!")
            logger.info(f"   Available services:")
            logger.info(f"     - POST /MathSumSynapse (x, y parameters)")
            logger.info(f"     - POST /MathProductSynapse (x, y parameters)")
            
            # Keep the service running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down math miner service...")
                
        except Exception as e:
            logger.error(f"❌ Failed to start math miner service: {e}")
            raise
    
    def stop(self):
        """Stop the math miner service."""
        try:
            if hasattr(self, 'xylem'):
                self.xylem.stop()
                logger.info("🛑 Math miner service stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping service: {e}")


async def main():
    """Main function to run the math miner service.
    
    This function demonstrates how to use the MathMiner template:
    1. Unlock wallet
    2. Create miner instance
    3. Start the service
    4. Handle shutdown gracefully
    """
    try:
        # Unlock wallet
        logger.info("🔐 Unlocking wallet...")
        wallet_name = "hanbo"  # Change this to your wallet name
        wallet = unlock_wallet(wallet_name)
        
        if not wallet:
            logger.error("❌ Failed to unlock wallet")
            return
        
        logger.info(f"✅ Wallet unlocked: {wallet.address}")
        
        # Create math miner service
        miner = MathMiner(
            wallet=wallet,
            netuid=1,  # Change this to your subnet ID
            network="mainnet",  # Change this to your network
            port=8091,  # Change this to your desired port
            ip="127.0.0.1"  # Change this to your desired IP
        )
        
        # Start the service
        await miner.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
