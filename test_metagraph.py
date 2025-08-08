from hetu.metagraph import Metagraph
from hetu.hetu import Hetutensor
import logging

logging.basicConfig(level=logging.INFO)

def test_metagraph():
    """Test Metagraph functionality"""
    logging.info("Starting Metagraph test...")
    
    # Initialize Hetu client
    hetu = Hetutensor()
    
    try:
        # Get total subnets
        total_subnets = hetu.get_total_subnets()
        logging.info(f"Total subnets: {total_subnets}")
        
        # Get all subnet IDs
        subnet_ids = hetu.get_subnets()
        logging.info(f"Found subnets: {subnet_ids}")
        
        # Test each subnet
        for netuid in subnet_ids:
            logging.info(f"\n=== Testing Metagraph for subnet {netuid} ===")
            
            try:
                # Create metagraph instance
                metagraph = Metagraph(
                    netuid=netuid,
                    network=hetu.network,
                    hetutensor=hetu,
                    sync=True
                )
                
                # Test string representation
                logging.info(f"Metagraph representation: {metagraph}")
                
                # Test metadata
                metadata = metagraph.metadata()
                logging.info("\nMetagraph metadata:")
                for key, value in metadata.items():
                    logging.info(f"  {key}: {value}")
                
                # Test state
                state = metagraph.state_dict()
                logging.info("\nMetagraph state:")
                
                # Basic info
                logging.info(f"  Network: {state['network']}")
                logging.info(f"  Netuid: {state['netuid']}")
                logging.info(f"  Block: {state['block']}")
                logging.info(f"  Active: {state['is_active']}")
                
                # Hyperparameters
                if state['hyperparameters']:
                    logging.info("\nHyperparameters:")
                    for param, value in state['hyperparameters'].items():
                        logging.info(f"  {param}: {value}")
                else:
                    logging.info("  No hyperparameters found")
                
                # Test sync
                logging.info("\nTesting sync...")
                metagraph.sync()
                logging.info("Sync completed")
                
            except Exception as e:
                logging.error(f"Error processing subnet {netuid}: {e}")
                import traceback
                logging.error(f"Traceback: {traceback.format_exc()}")
                continue
            
            logging.info(f"=== Completed testing for subnet {netuid} ===\n")
            
    except Exception as e:
        logging.error(f"Error during testing: {e}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        hetu.close()

if __name__ == "__main__":
    test_metagraph() 