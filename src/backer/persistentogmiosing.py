from typing import List, Union
from pycardano import OgmiosV6ChainContext
from pycardano.address import Address
from pycardano.backend.base import ProtocolParameters
from ogmios import Client
from ogmios.datatypes import Tip, Utxo


class PersistentOgmiosV6ChainContext(OgmiosV6ChainContext):
    """Persistent OgmiosV6ChainContext

    Original OgmiosV6ChainContext will open a new ogmios websocket connection per request.
    Some functions can even involve multiple requests to ogmios.

    This re-uses an externally handled client.
    """
    def __init__(self, client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client: Client = client

    def submit_tx_cbor(self, cbor: Union[bytes, str]):
        if isinstance(cbor, bytes):
            cbor = cbor.hex()
        self._client.submit_transaction.execute(cbor)

    def _query_utxos_by_address(self, address: Address) -> List[Utxo]:
        utxos, _ = self._client.query_utxo.execute([address])
        return utxos

    def _query_chain_tip(self) -> Tip:
        tip, _ = self._client.query_network_tip.execute()
        return tip

    def _fetch_protocol_param(self) -> ProtocolParameters:
        protocol_parameters, _ = self._client.query_protocol_parameters.execute()
        pyc_protocol_params = ProtocolParameters(
            min_fee_constant=protocol_parameters.min_fee_constant.lovelace,
            min_fee_coefficient=protocol_parameters.min_fee_coefficient,
            min_pool_cost=protocol_parameters.min_stake_pool_cost.lovelace,
            max_block_size=protocol_parameters.max_block_body_size.get("bytes"),
            max_tx_size=protocol_parameters.max_transaction_size.get("bytes"),
            max_block_header_size=protocol_parameters.max_block_header_size.get(
                "bytes"
            ),
            key_deposit=protocol_parameters.stake_credential_deposit.lovelace,
            pool_deposit=protocol_parameters.stake_pool_deposit.lovelace,
            pool_influence=eval(protocol_parameters.stake_pool_pledge_influence),
            monetary_expansion=eval(protocol_parameters.monetary_expansion),
            treasury_expansion=eval(protocol_parameters.treasury_expansion),
            decentralization_param=None,  # type: ignore[arg-type]
            extra_entropy=protocol_parameters.extra_entropy,
            protocol_major_version=protocol_parameters.version.get("major"),
            protocol_minor_version=protocol_parameters.version.get("minor"),
            min_utxo=None,  # type: ignore[arg-type]
            price_mem=eval(
                protocol_parameters.script_execution_prices.get("memory")
            ),
            price_step=eval(protocol_parameters.script_execution_prices.get("cpu")),
            max_tx_ex_mem=protocol_parameters.max_execution_units_per_transaction.get(
                "memory"
            ),
            max_tx_ex_steps=protocol_parameters.max_execution_units_per_transaction.get(
                "cpu"
            ),
            max_block_ex_mem=protocol_parameters.max_execution_units_per_block.get(
                "memory"
            ),
            max_block_ex_steps=protocol_parameters.max_execution_units_per_block.get(
                "cpu"
            ),
            max_val_size=protocol_parameters.max_value_size.get("bytes"),
            collateral_percent=protocol_parameters.collateral_percentage,
            max_collateral_inputs=protocol_parameters.max_collateral_inputs,
            coins_per_utxo_word=34482,
            coins_per_utxo_byte=protocol_parameters.min_utxo_deposit_coefficient,
            cost_models=self._parse_cost_models(
                protocol_parameters.plutus_cost_models
            ),
            maximum_reference_scripts_size=protocol_parameters.max_ref_script_size,
            min_fee_reference_scripts=protocol_parameters.min_fee_ref_scripts,
        )
        return pyc_protocol_params
