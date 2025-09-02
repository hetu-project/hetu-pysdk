#!/usr/bin/env python3
"""
Math Validator Template - A validator that submits weights for math miners.
This template demonstrates how to create a validator service using the protocol layer.
"""

import sys
import os
import logging
import asyncio
import time
import aiohttp
import json
from typing import List, Optional, Dict, Any

# Fix import path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from hetu.phloem import Phloem
from hetu.metagraph import Metagraph
from hetu.utils.wallet import unlock_wallet

# Import from protocol layer
from protocol import MathSumSynapse, MathProductSynapse, get_available_services

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_POLL_INTERVAL_SECONDS = 20
DEFAULT_EPOCH_THRESHOLD_RATIO = 0.9  # Submit within the last 10% of the epoch

# Weight scoring based on validation results
WEIGHT_SCORES = {
    "correct": 100,      # Correct result
    "incorrect": 30,     # Incorrect result  
    "no_response": 0     # No response from miner
}


class MathValidator:
    """A validator that submits weights for math miners each epoch window.
    
    Reference: Hetu Validator Implementation Pattern
    
    This template shows how to create a validator service that:
    1. Uses the protocol layer for service identification
    2. Discovers miners from the metagraph
    3. Submits weights periodically
    4. Handles errors gracefully
    """

    def __init__(self, username: str, netuid: int, network: str = "mainnet", 
                 wallet=None):
        """Initialize the math validator.
        
        Args:
            username (str): Wallet username
            netuid (int): Subnet ID to operate on
            network (str): Network name (mainnet, testnet, etc.)
            wallet: Pre-initialized wallet Account object
        """
        self.username = username
        self.netuid = netuid
        self.network = network

        # Timing configuration
        self.polling_interval = DEFAULT_POLL_INTERVAL_SECONDS
        self.epoch_threshold_ratio = DEFAULT_EPOCH_THRESHOLD_RATIO
        self.is_running = False
        
        # Track last epoch we submitted for (by next_epoch_block)
        self._last_submitted_epoch_end: Optional[int] = None

        # Initialize Phloem/Hetutensor with provided wallet
        if wallet is not None:
            self.phloem = Phloem(
                wallet=wallet,
                netuid=netuid,
                network=network
            )
            logger.info(f"✅ Phloem client created with wallet: {wallet.address}")
        else:
            raise RuntimeError("Wallet object is required")

        # Initialize metagraph with the same Hetutensor
        self.metagraph = Metagraph(
            netuid=netuid,
            network=network,
            hetutensor=self.phloem.hetu
        )
        logger.info("✅ Metagraph initialized")

        # Verify wallet is ready
        if not self.phloem.hetu.has_wallet():
            raise RuntimeError("Wallet not initialized. Please check credentials.")
        logger.info(f"✅ Wallet initialized: {self.phloem.hetu.get_wallet_address()}")
        
        # Log available services from protocol
        available_services = get_available_services()
        logger.info(f"✅ Protocol services: {', '.join(available_services)}")
        
        # Test cases for validation
        self.test_cases = [
            {"x": 5.0, "y": 3.0, "expected_sum": 8.0, "expected_product": 15.0},
            {"x": 10.0, "y": 2.0, "expected_sum": 12.0, "expected_product": 20.0},
            {"x": 0.0, "y": 7.0, "expected_sum": 7.0, "expected_product": 0.0},
            {"x": -5.0, "y": 3.0, "expected_sum": -2.0, "expected_product": -15.0},
        ]

    def get_epoch_info(self) -> Optional[Dict[str, Any]]:
        """Get current epoch information.
        
        Reference: Hetu Epoch Management Protocol
        
        Returns:
            Dictionary with epoch details or None if unavailable
        """
        try:
            self.metagraph.sync(force=True)
            current_block = self.metagraph.block
            tempo = self.metagraph.hyperparameters.get("tempo")
            
            if current_block == 0 or tempo is None:
                logger.warning("⚠️ Cannot get epoch info: block=0 or tempo=None")
                return None

            current_result = (current_block + self.netuid + 1) % (tempo + 1)
            is_epoch_block = current_result == 0

            if is_epoch_block:
                next_epoch_block = current_block + (tempo + 1)
                blocks_until_epoch = 0
            else:
                blocks_until_epoch = (tempo + 1) - current_result
                next_epoch_block = current_block + blocks_until_epoch

            return {
                "current_block": current_block,
                "tempo": tempo,
                "is_epoch_block": is_epoch_block,
                "next_epoch_block": next_epoch_block,
                "blocks_until_epoch": blocks_until_epoch,
                "epoch_length": tempo + 1,
                "threshold_blocks": int((tempo + 1) * self.epoch_threshold_ratio),
            }
        except Exception as e:
            logger.error(f"❌ Error getting epoch info: {e}")
            return None

    def should_submit_weights(self) -> bool:
        """Check if we should submit weights based on epoch timing.
        
        Returns:
            True if we should submit weights, False otherwise
        """
        try:
            epoch = self.get_epoch_info()
            if not epoch:
                return False
            return epoch["blocks_until_epoch"] <= epoch["threshold_blocks"]
        except Exception as e:
            logger.error(f"❌ Error computing submission timing: {e}")
            return False

    def get_miner_addresses(self) -> List[str]:
        """Discover miners from the metagraph.
        
        Returns:
            List of miner hotkey addresses
        """
        try:
            self.metagraph.sync(force=True)
            xylems = self.metagraph.get_xylems(force_sync=True)
            
            if not xylems:
                logger.warning("⚠️ No miners available from metagraph")
                return []
                
            addresses = [a.hotkey for a in xylems if getattr(a, 'hotkey', None)]
            logger.info(f"✅ Discovered {len(addresses)} miners")
            return addresses
            
        except Exception as e:
            logger.error(f"❌ Failed to discover miners: {e}")
            return []

    async def validate_miner(self, miner_address: str, miner_ip: str, miner_port: int) -> Dict[str, Any]:
        """Validate a miner by testing its mathematical services.
        
        Args:
            miner_address: Miner's hotkey address
            miner_ip: Miner's IP address
            miner_port: Miner's port number
            
        Returns:
            Dictionary with validation results and score
        """
        try:
            base_url = f"http://{miner_ip}:{miner_port}"
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                total_score = 0
                total_tests = 0
                test_results = []
                
                # Test addition service
                for test_case in self.test_cases:
                    try:
                        payload = {
                            "x": test_case["x"],
                            "y": test_case["y"]
                        }
                        
                        async with session.post(
                            f"{base_url}/MathSumSynapse",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                if "completion" in data:
                                    # Extract result from completion message
                                    completion = data["completion"]
                                    if "Result:" in completion:
                                        try:
                                            result = float(completion.split("Result:")[1].strip())
                                            expected = test_case["expected_sum"]
                                            
                                            if abs(result - expected) < 0.001:  # Allow small floating point errors
                                                score = WEIGHT_SCORES["correct"]
                                                status = "correct"
                                            else:
                                                score = WEIGHT_SCORES["incorrect"]
                                                status = "incorrect"
                                                
                                            total_score += score
                                            total_tests += 1
                                            
                                            test_results.append({
                                                "service": "addition",
                                                "input": f"{test_case['x']} + {test_case['y']}",
                                                "expected": expected,
                                                "received": result,
                                                "status": status,
                                                "score": score
                                            })
                                            
                                        except (ValueError, IndexError):
                                            score = WEIGHT_SCORES["incorrect"]
                                            status = "incorrect"
                                            total_score += score
                                            total_tests += 1
                                            
                                            test_results.append({
                                                "service": "addition",
                                                "input": f"{test_case['x']} + {test_case['y']}",
                                                "expected": test_case["expected_sum"],
                                                "received": "parse_error",
                                                "status": status,
                                                "score": score
                                            })
                                    else:
                                        score = WEIGHT_SCORES["incorrect"]
                                        status = "incorrect"
                                        total_score += score
                                        total_tests += 1
                                        
                                        test_results.append({
                                            "service": "addition",
                                            "input": f"{test_case['x']} + {test_case['y']}",
                                            "expected": test_case["expected_sum"],
                                            "received": "no_result",
                                            "status": status,
                                            "score": score
                                        })
                                else:
                                    score = WEIGHT_SCORES["incorrect"]
                                    status = "incorrect"
                                    total_score += score
                                    total_tests += 1
                                    
                                    test_results.append({
                                        "service": "addition",
                                        "input": f"{test_case['x']} + {test_case['y']}",
                                        "expected": test_case["expected_sum"],
                                        "received": "no_completion",
                                        "status": status,
                                        "score": score
                                    })
                            else:
                                score = WEIGHT_SCORES["no_response"]
                                status = "no_response"
                                total_score += score
                                total_tests += 1
                                
                                test_results.append({
                                    "service": "addition",
                                    "input": f"{test_case['x']} + {test_case['y']}",
                                    "expected": test_case["expected_sum"],
                                    "received": f"http_{response.status}",
                                    "status": status,
                                    "score": score
                                })
                                
                    except Exception as e:
                        score = WEIGHT_SCORES["no_response"]
                        status = "no_response"
                        total_score += score
                        total_tests += 1
                        
                        test_results.append({
                            "service": "addition",
                            "input": f"{test_case['x']} + {test_case['y']}",
                            "expected": test_case["expected_sum"],
                            "received": f"error: {str(e)}",
                            "status": status,
                            "score": score
                        })
                
                # Test multiplication service
                for test_case in self.test_cases:
                    try:
                        payload = {
                            "x": test_case["x"],
                            "y": test_case["y"]
                        }
                        
                        async with session.post(
                            f"{base_url}/MathProductSynapse",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                if "completion" in data:
                                    completion = data["completion"]
                                    if "Result:" in completion:
                                        try:
                                            result = float(completion.split("Result:")[1].strip())
                                            expected = test_case["expected_product"]
                                            
                                            if abs(result - expected) < 0.001:
                                                score = WEIGHT_SCORES["correct"]
                                                status = "correct"
                                            else:
                                                score = WEIGHT_SCORES["incorrect"]
                                                status = "incorrect"
                                                
                                            total_score += score
                                            total_tests += 1
                                            
                                            test_results.append({
                                                "service": "multiplication",
                                                "input": f"{test_case['x']} × {test_case['y']}",
                                                "expected": expected,
                                                "received": result,
                                                "status": status,
                                                "score": score
                                            })
                                            
                                        except (ValueError, IndexError):
                                            score = WEIGHT_SCORES["incorrect"]
                                            status = "incorrect"
                                            total_score += score
                                            total_tests += 1
                                            
                                            test_results.append({
                                                "service": "multiplication",
                                                "input": f"{test_case['x']} × {test_case['y']}",
                                                "expected": test_case["expected_product"],
                                                "received": "parse_error",
                                                "status": status,
                                                "score": score
                                            })
                                    else:
                                        score = WEIGHT_SCORES["incorrect"]
                                        status = "incorrect"
                                        total_score += score
                                        total_tests += 1
                                        
                                        test_results.append({
                                            "service": "multiplication",
                                            "input": f"{test_case['x']} × {test_case['y']}",
                                            "expected": test_case["expected_product"],
                                            "received": "no_result",
                                            "status": status,
                                            "score": score
                                        })
                                else:
                                    score = WEIGHT_SCORES["incorrect"]
                                    status = "incorrect"
                                    total_score += score
                                    total_tests += 1
                                    
                                    test_results.append({
                                        "service": "multiplication",
                                        "input": f"{test_case['x']} × {test_case['y']}",
                                        "expected": test_case["expected_product"],
                                        "received": "no_completion",
                                        "status": status,
                                        "score": score
                                    })
                            else:
                                score = WEIGHT_SCORES["no_response"]
                                status = "no_response"
                                total_score += score
                                total_tests += 1
                                
                                test_results.append({
                                    "service": "multiplication",
                                    "input": f"{test_case['x']} × {test_case['y']}",
                                    "expected": test_case["expected_product"],
                                    "received": f"http_{response.status}",
                                    "status": status,
                                    "score": score
                                })
                                
                    except Exception as e:
                        score = WEIGHT_SCORES["no_response"]
                        status = "no_response"
                        total_score += score
                        total_tests += 1
                        
                        test_results.append({
                            "service": "multiplication",
                            "input": f"{test_case['x']} × {test_case['y']}",
                            "expected": test_case["expected_product"],
                            "received": f"error: {str(e)}",
                            "status": status,
                            "score": score
                        })
                
                # Calculate average score
                avg_score = total_score / total_tests if total_tests > 0 else 0
                
                logger.info(f"✅ Validated miner {miner_address}: avg_score={avg_score:.1f}")
                
                return {
                    "address": miner_address,
                    "avg_score": avg_score,
                    "total_score": total_score,
                    "total_tests": total_tests,
                    "test_results": test_results,
                    "status": "success"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to validate miner {miner_address}: {e}")
            return {
                "address": miner_address,
                "avg_score": 0,
                "total_score": 0,
                "total_tests": 0,
                "test_results": [],
                "status": "error",
                "error": str(e)
            }

    async def validate_all_miners(self, miner_addresses: List[str]) -> List[Dict[str, Any]]:
        """Validate all discovered miners.
        
        Args:
            miner_addresses: List of miner hotkey addresses
            
        Returns:
            List of validation results for each miner
        """
        validation_results = []
        
        for address in miner_addresses:
            # For now, assume miners are running on localhost:8091
            # In a real implementation, you'd get this from the metagraph
            miner_ip = "127.0.0.1"
            miner_port = 8091
            
            logger.info(f"🔍 Validating miner {address} at {miner_ip}:{miner_port}")
            result = await self.validate_miner(address, miner_ip, miner_port)
            validation_results.append(result)
            
            # Small delay between validations
            await asyncio.sleep(1)
        
        return validation_results

    def build_weights(self, validation_results: List[Dict[str, Any]]) -> List[tuple[str, int]]:
        """Build weight list based on miner validation results.
        
        Args:
            validation_results: List of validation results for each miner
            
        Returns:
            List of (address, weight) tuples
        """
        if not validation_results:
            return []
            
        weights = []
        for result in validation_results:
            if result["status"] == "success":
                # Round the average score to nearest integer
                weight = int(round(result["avg_score"]))
                weights.append((result["address"], weight))
                
                logger.info(f"📊 Miner {result['address']}: score={result['avg_score']:.1f} -> weight={weight}")
            else:
                # If validation failed, assign 0 weight
                weights.append((result["address"], 0))
                logger.warning(f"⚠️ Miner {result['address']}: validation failed -> weight=0")
        
        logger.info(f"✅ Built {len(weights)} weights based on validation results")
        return weights

    async def submit_weights(self, weights: List[tuple[str, int]]) -> bool:
        """Submit weights to the blockchain.
        
        Args:
            weights: List of (address, weight) tuples
            
        Returns:
            True if submission successful, False otherwise
        """
        try:
            if not weights:
                logger.warning("⚠️ No weights to submit")
                return False
                
            logger.info(f"📤 Submitting {len(weights)} weights to blockchain...")
            
            ok = self.phloem.hetu.set_weights(
                netuid=self.netuid,
                weights=weights
            )
            
            if ok:
                logger.info("🎉 Weights submitted successfully!")
                return True
            else:
                logger.error("❌ Weight submission failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Submission error: {e}")
            return False

    async def run_once_if_time(self) -> bool:
        """Check if we should submit weights and do so if appropriate.
        
        Returns:
            True if weights were submitted, False otherwise
        """
        epoch = self.get_epoch_info()
        if not epoch:
            return False
            
        # Avoid duplicate submission within the same epoch
        epoch_end = epoch["next_epoch_block"]
        if self._last_submitted_epoch_end == epoch_end:
            logger.info("🔁 Already submitted for this epoch; skipping")
            return False
            
        if not self.should_submit_weights():
            return False
            
        miners = self.get_miner_addresses()
        
        if miners:
            logger.info(f"🔍 Starting validation of {len(miners)} miners...")
            validation_results = await self.validate_all_miners(miners)
            
            # Log validation summary
            total_score = sum(r["avg_score"] for r in validation_results if r["status"] == "success")
            avg_score = total_score / len(validation_results) if validation_results else 0
            logger.info(f"📊 Validation complete: avg_score={avg_score:.1f}")
            
            weights = self.build_weights(validation_results)
        else:
            logger.warning("⚠️ No miners to validate")
            weights = []
            
        ok = await self.submit_weights(weights)
        
        if ok:
            self._last_submitted_epoch_end = epoch_end
            
        return ok

    async def run_continuous(self):
        """Run the validator in continuous mode."""
        logger.info("🚀 Starting math validator (continuous loop)...")
        logger.info(f"Polling interval: {self.polling_interval}s")
        logger.info(f"Threshold ratio: {self.epoch_threshold_ratio}")
        logger.info(f"Weight scoring: correct={WEIGHT_SCORES['correct']}, incorrect={WEIGHT_SCORES['incorrect']}, no_response={WEIGHT_SCORES['no_response']}")
        logger.info(f"Subnet: {self.netuid}, Network: {self.network}")
        
        self.is_running = True
        
        try:
            while self.is_running:
                logger.info("\n" + "=" * 60)
                logger.info(f"⏰ Tick at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if await self.run_once_if_time():
                    logger.info("✅ Submission completed this tick")
                else:
                    logger.info("⏳ Not in submission window yet")
                    
                await asyncio.sleep(self.polling_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Interrupted, stopping...")
        finally:
            self.is_running = False
            logger.info("✅ Math validator stopped")

    def stop(self):
        """Stop the validator."""
        self.is_running = False
        logger.info("🛑 Math validator stop requested")


async def main():
    """Main function to run the math validator.
    
    This function demonstrates how to use the MathValidator template:
    1. Unlock wallet
    2. Create validator instance
    3. Run continuously
    4. Handle shutdown gracefully
    """
    try:
        # Configuration - change these as needed
        username = "test0"  # Change this to your wallet name
        netuid = 1          # Change this to your subnet ID
        network = "mainnet" # Change this to your network
        
        logger.info("🔧 Using configuration:")
        logger.info(f"   Username: {username}")
        logger.info(f"   Netuid: {netuid}")
        logger.info(f"   Network: {network}")
        logger.info(f"   Weight scoring: correct={WEIGHT_SCORES['correct']}, incorrect={WEIGHT_SCORES['incorrect']}, no_response={WEIGHT_SCORES['no_response']}")

        # Unlock wallet
        logger.info("🔓 Unlocking wallet...")
        wallet = unlock_wallet(username)
        
        if not wallet:
            logger.error("❌ Failed to unlock wallet")
            return False
        
        logger.info(f"✅ Wallet unlocked: {wallet.address}")

        # Create validator
        validator = MathValidator(
            username=username,
            netuid=netuid,
            network=network,
            wallet=wallet
        )

        # Run continuously
        await validator.run_continuous()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to start math validator: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
