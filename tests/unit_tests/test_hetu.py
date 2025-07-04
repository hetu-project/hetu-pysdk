"""
test_hetu.py, `poetry run pytest -s tests/`

Basic tests for Hetutensor (EVM/ETH integration).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import hetu as ht
from hetu.hetu import Hetutensor
from hetu.metagraph import Metagraph
from hetu.config import Config
from eth_account import Account
import asyncio
from hetu.dendrite import Dendrite
from hetu.synapse import Synapse

def test_hetutensor_version():
    print("Testing Hetutensor version retrieval...")
    print(ht.__version__)


def test_hetutensor_init():
    client = Hetutensor(network="local", log_verbose=True)
    assert client.web3 is not None
    assert hasattr(client, "get_current_block")


def test_hetutensor_block():
    client = Hetutensor(network="local")
    block = client.get_current_block()
    print(f"Current block: {block}")
    assert isinstance(block, int)


def test_hetutensor_balance():
    client = Hetutensor(network="local")
    # Test with the 0x0 address and return 0
    balance = client.get_balance("0x739976a2BABE66F86d6a0f6AB96E498ee2F55dA6")
    print(f"Balance for 0x7399...: {balance}")
    assert isinstance(
        balance, type(client.get_balance("0x739976a2BABE66F86d6a0f6AB96E498ee2F55dA6"))
    )


def test_list_all_axon():
    metagraph = Metagraph(1, "local")
    print(metagraph.axons[:10])


def test_setup_axon():
    """Test Axon setup and basic serve/start lifecycle."""
    config = Config()
    wallet = Account.create()
    # Explicitly pass all Axon-related parameters
    axon = ht.Axon(
        account=wallet,
        config=config,
        port=8091,
        ip="127.0.0.1",
        external_ip="127.0.0.1",
        external_port=8091,
        max_workers=2,
    )
    assert axon is not None
    axon.serve(netuid=1, hetutensor=None)
    axon.start()
    assert axon.started
    axon.stop()

# Test Dendrite client calls Axon server with a simple EchoSynapse.
class EchoSynapse(Synapse):
    input: str = ""
    output: str = ""

def test_dendrite_call_axon():
    """Test Dendrite client calls Axon server with a simple EchoSynapse."""
    config = Config()
    wallet = Account.create()
    axon = ht.Axon(
        account=wallet,
        config=config,
        port=8092,
        ip="127.0.0.1",
        external_ip="127.0.0.1",
        external_port=8092,
        max_workers=2,
    )

    # regist echo forward
    def echo_forward(s: EchoSynapse) -> EchoSynapse:
        s.output = s.input
        return s

    axon.attach(forward_fn=echo_forward)
    axon.serve(netuid=1, hetutensor=None)
    axon.start()

    wallet2 = Account.create()
    async def _run():
        dendrite = Dendrite(account=wallet2)
        syn = EchoSynapse(input="hello")
        # Send the request directly using call
        resp = await dendrite.call(axon.info(), synapse=syn, timeout=3)
        print(f"Echo response: {resp.output}")
        assert resp.output == "hello"
        await dendrite.aclose_session()

    try:
        asyncio.run(_run())
    finally:
        axon.stop()