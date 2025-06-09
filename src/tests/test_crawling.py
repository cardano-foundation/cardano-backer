import pytest
from unittest.mock import MagicMock

import backer.crawling as crawling
import ogmios
from backer.cardaning import CardanoType

class MockPoint:
    def __init__(self, *args, **kwargs):
        pass

class MockBlock:
    def __init__(self, *args, **kwargs):
        self.id = kwargs.get("id", "mock_block_id")
        self.slot = kwargs.get("slot", 0)
        self.blocktype = kwargs.get("blocktype", None)
        self.height = kwargs.get("height", None)
        self.transactions = kwargs.get("transactions", [])

@pytest.fixture
def mock_ledger():
    ledger = MagicMock()
    ledger.states.get.return_value = None
    ledger.onTip = False
    ledger.tipHeight = 100
    ledger.states.pin = MagicMock()
    ledger.getConfirmingTrans = MagicMock(return_value=None)
    ledger.updateTrans = MagicMock()
    ledger.updateTip = MagicMock()
    ledger.rollbackBlock = MagicMock()
    ledger.confirmTrans = MagicMock()
    return ledger

@pytest.fixture(autouse=True)
def patch_ogmios_and_helpers(monkeypatch):
    monkeypatch.setattr("ogmios.Client", MagicMock())
    monkeypatch.setattr("ogmios.Point", MockPoint)
    crawling.ogmios = ogmios
    monkeypatch.setattr("backer.crawling.ogmios.Point", MockPoint)

    if hasattr(crawling, "Point"):
        monkeypatch.setattr("backer.crawling.Point", MockPoint)
        
    monkeypatch.setattr("ogmios.Block", MockBlock)
    monkeypatch.setattr("ogmios.Origin", MagicMock(return_value="mock_origin"))
    monkeypatch.setattr("ogmios.Direction", type("Direction", (), {"forward": "forward"}))
    monkeypatch.setattr("ogmios.model.model_map.Types", MagicMock())
    monkeypatch.setattr("backer.cardaning.PointRecord", lambda id, slot: (id, slot))
    monkeypatch.setattr("keri.help.ogler.getLogger", lambda: MagicMock())

def test_crawler_init(mock_ledger):
    crawler = crawling.Crawler(mock_ledger)
    assert isinstance(crawler, crawling.Crawler)
    assert crawler.ledger == mock_ledger

def test_crawlBlockDo_yields_and_handles_tip(mock_ledger):
    crawler = crawling.Crawler(mock_ledger)
    crawler.ledger.client.find_intersection.execute.side_effect = lambda *a, **kw: (None, None, None)
    crawler.ledger.client.query_block_height.execute.side_effect = lambda *a, **kw: (None, None)

    # Create a block that passes isinstance(block, ogmios.Block)
    block = crawling.ogmios.Block()
    block.blocktype = None
    block.height = 100
    block.slot = 42
    block.id = "mock_block_id"
    block.transactions = [{'id': 'tx1'}]

    crawler.ledger.client.next_block.execute.return_value = (
        'forward',
        MagicMock(height=100),
        block,
        None
    )
    mock_ledger.getConfirmingTrans.return_value = '{"type": "CARDANO_KEL"}'

    gen = crawler.crawlBlockDo()
    next(gen)  # prime generator
    for _ in range(3):
        next(gen)  # run a few cycles

    assert mock_ledger.updateTrans.called
    mock_ledger.updateTip.assert_called_with(100)
    assert mock_ledger.states.pin.called

def test_confirmTrans_calls_ledger_methods(mock_ledger):
    crawler = crawling.Crawler(mock_ledger)
    gen = crawler.confirmTrans()
    next(gen)  # prime generator
    next(gen)
    mock_ledger.confirmTrans.assert_any_call(CardanoType.KEL)
    mock_ledger.confirmTrans.assert_any_call(CardanoType.SCHEMA)

def test_crawlBlockDo_skips_on_point_block(mock_ledger):
    crawler = crawling.Crawler(mock_ledger)
    crawler.ledger.client.find_intersection.execute.side_effect = lambda *a, **kw: (None, None, None)
    crawler.ledger.client.query_block_height.execute.side_effect = lambda *a, **kw: (100, None)
    # Block is a Point
    block = crawling.ogmios.Point()
    crawler.ledger.client.next_block.execute.return_value = (
        'forward',
        MagicMock(height=100),
        block,
        None
    )
    gen = crawler.crawlBlockDo()
    next(gen)
    next(gen)  # Should yield without calling updateTrans
    assert not mock_ledger.updateTrans.called

def test_crawlBlockDo_skips_on_origin_block(mock_ledger):
    crawler = crawling.Crawler(mock_ledger)
    crawler.ledger.client.find_intersection.execute.side_effect = lambda *a, **kw: (None, None, None)
    crawler.ledger.client.query_block_height.execute.side_effect = lambda *a, **kw: (100, None)
    # Block is Origin
    block = crawling.ogmios.Origin()
    crawler.ledger.client.next_block.execute.return_value = (
        'forward',
        MagicMock(height=100),
        block,
        None
    )
    gen = crawler.crawlBlockDo()
    next(gen)
    next(gen)
    assert not mock_ledger.updateTrans.called

def test_crawlBlockDo_skips_on_ebb_blocktype(mock_ledger, monkeypatch):
    crawler = crawling.Crawler(mock_ledger)
    crawler.ledger.client.find_intersection.execute.side_effect = lambda *a, **kw: (None, None, None)
    crawler.ledger.client.query_block_height.execute.side_effect = lambda *a, **kw: (100, None)
    # Patch ogmm.Types.ebb.value
    class FakeTypes:
        class ebb:
            value = "EBB"
    monkeypatch.setattr("ogmios.model.model_map.Types", FakeTypes)
    block = crawling.ogmios.Block()
    block.blocktype = "EBB"
    block.height = 100
    block.slot = 42
    block.transactions = []
    crawler.ledger.client.next_block.execute.return_value = (
        'forward',
        MagicMock(height=100),
        block,
        None
    )
    gen = crawler.crawlBlockDo()
    next(gen)
    next(gen)
    assert not mock_ledger.updateTrans.called

def test_crawlBlockDo_stops_when_on_tip_and_retries_on_new_block(mock_ledger):
    """
    Simulate:
    - tipHeight is 99, fetch block 100, process it
    - tipHeight is now 100, so don't fetch another block, just yield
    - tipHeight becomes 101, so fetch and process block 101
    """
    crawler = crawling.Crawler(mock_ledger)
    crawler.ledger.client.find_intersection.execute.side_effect = lambda *a, **kw: (None, None, None)
    # Initial tip is 99
    mock_ledger.tipHeight = 99

    # Setup mock client methods
    crawler.ledger.client.query_block_height.execute.side_effect = [
        (100, None), (100, None), (101, None)
    ]

    # Block 100
    block_100 = crawling.ogmios.Block()
    block_100.blocktype = None
    block_100.height = 100
    block_100.slot = 50
    block_100.id = "block_100"
    block_100.transactions = [{'id': 'tx100'}]

    # Block 101
    block_101 = crawling.ogmios.Block()
    block_101.blocktype = None
    block_101.height = 101
    block_101.slot = 51
    block_101.id = "block_101"
    block_101.transactions = [{'id': 'tx101'}]

    # Dummy block for "on tip" yield
    dummy_block = crawling.ogmios.Origin()

    # next_block returns block 100, then yields dummy block (on tip), then block 101
    crawler.ledger.client.next_block.execute.side_effect = [
        ('forward', MagicMock(height=100), block_100, None),
        ('forward', MagicMock(height=100), dummy_block, None),  # Now an Origin, will be skipped
        ('forward', MagicMock(height=101), block_101, None),
    ]

    # Simulate confirming transaction type
    mock_ledger.getConfirmingTrans.return_value = '{"type": "CARDANO_KEL"}'

    gen = crawler.crawlBlockDo()
    next(gen)  # prime generator

    # First: fetch and process block 100
    next(gen)
    assert mock_ledger.updateTrans.called
    mock_ledger.updateTip.assert_called_with(100)

    # Second: on tip, should just yield, not call updateTrans again
    mock_ledger.updateTrans.reset_mock()
    mock_ledger.updateTip.reset_mock()
    yielded = next(gen)
    assert not mock_ledger.updateTrans.called
    assert not mock_ledger.updateTip.called
    assert yielded == 1.0

    # Third: tipHeight increases to 101, fetch and process block 101
    next(gen)
    assert mock_ledger.updateTrans.called
    mock_ledger.updateTip.assert_called_with(101)
