from unittest.mock import MagicMock
from backer.cardaning import Cardano, TransactionType


def test_publishEvents_submit_tx_exception(monkeypatch):
    serder_mock = MagicMock()
    serder_mock.pre = "mock_pre"
    serder_mock.said = "mock_said"
    monkeypatch.setattr("keri.core.serdering.SerderKERI", lambda raw, smellage=None: serder_mock)

    # Arrange
    monkeypatch.setenv('WALLET_ADDRESS_CBORHEX', '00' * 64)
    monkeypatch.setattr("pycardano.PaymentSigningKey.from_cbor", lambda x: MagicMock(
        to_verification_key=lambda: MagicMock(
            hash=lambda: b"\x00" * 28
        )
    ))
    monkeypatch.setattr("pycardano.Address", MagicMock())
    monkeypatch.setattr("pycardano.Address.from_primitive", lambda x: MagicMock())
    monkeypatch.setattr("pycardano.TransactionBuilder", lambda ctx: MagicMock(
        build_and_sign=MagicMock(return_value=MagicMock(
            to_cbor=MagicMock(return_value=b"123"),
            id="txid123"
        ))
    ))
    monkeypatch.setattr("pycardano.TransactionOutput", MagicMock())
    monkeypatch.setattr("pycardano.Value.from_primitive", lambda x: MagicMock())
    monkeypatch.setattr("pycardano.AuxiliaryData", MagicMock())
    monkeypatch.setattr("pycardano.Metadata", MagicMock())

    cardano = Cardano(MagicMock(), MagicMock())
    cardano.onTip = True

    # Mock queue with one event
    event = "mock_event"
    txType = TransactionType.KEL

    cardano.kelsQueued = MagicMock()
    cardano.kelsQueued.getItemIter.return_value = [(None, event)]
    cardano.hab = MagicMock()
    cardano.hab.db.cnt.return_value = 1

    # Mock UTXO selection
    utxo = MagicMock()
    cardano.selectAvailableUTXOs = MagicMock(return_value=[utxo])

    # Mock context.submit_tx_cbor to raise Exception
    cardano.context.submit_tx_cbor = MagicMock(side_effect=Exception("submit error"))

    # Spy on _addToPublished and _removeFromQueue
    cardano._addToPublished = MagicMock()
    cardano._removeFromQueue = MagicMock()

    # Mock confirmingTxs and dbConfirmingUtxos
    cardano.kelsConfirming.pin = MagicMock()
    cardano.kelsConfirming.rem = MagicMock()
    cardano.dbConfirmingUtxos.pin = MagicMock()
    cardano.dbConfirmingUtxos.rem = MagicMock()

    # Act
    cardano.publishEvents(txType)

    # Assert: should call remove on confirming UTXOs and KELs NOT call _addToPublished or _removeFromQueue if exception raised
    cardano.dbConfirmingUtxos.rem.assert_called_with(keys="txid123")
    cardano.kelsConfirming.rem.assert_called_with("txid123")  
    cardano._addToPublished.assert_not_called()
    cardano._removeFromQueue.assert_not_called()
