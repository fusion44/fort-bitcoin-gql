"""A simple GraphQL API for the Bitcoin Core Node software
For a full description of all available API"s see https://bitcoin.org/en/developer-reference

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene

import backend.btc.types as types
import backend.exceptions as exceptions
from .utils import make_rpc_auth_url


class Query(graphene.ObjectType):
    """Contains all Bitcoin RPC queries"""

    get_blockchain_info = graphene.Field(
        types.BlockchainInfoType, testnet=graphene.Boolean())

    def resolve_get_blockchain_info(self, info, **kwargs):
        """bitcoin-cli getblockchaininfo
        https://bitcoin.org/en/developer-reference#getblockchaininfo
        """

        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        output = make_rpc_auth_url(testnet).getblockchaininfo()
        info = types.BlockchainInfoType()
        info.chain = output["chain"]
        info.blocks = output["blocks"]
        info.headers = output["headers"]
        info.best_block_hash = output["bestblockhash"]
        info.difficulty = output["difficulty"]
        info.median_time = output["mediantime"]
        info.verification_progress = output["verificationprogress"]
        info.initial_block_download = output["initialblockdownload"]
        info.chain_work = output["chainwork"]
        info.size_on_disk = output["size_on_disk"]
        info.pruned = output["pruned"]
        info.softforks = output["softforks"]
        info.bip9_softforks = output["bip9_softforks"]
        info.warnings = output["warnings"]
        return info

    get_mining_info = graphene.Field(
        types.MiningInfoType, testnet=graphene.Boolean())

    def resolve_get_mining_info(self, info, **kwargs):
        """bitcoin-cli getmininginfo
        https://bitcoin.org/en/developer-reference#getmininginfo
        """

        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        output = make_rpc_auth_url(testnet).getmininginfo()
        info = types.MiningInfoType()
        info.blocks = output["blocks"]
        info.current_block_weight = output["currentblockweight"]
        info.current_block_tx = output["currentblocktx"]
        info.difficulty = output["difficulty"]
        info.network_hash_hps = output["networkhashps"]
        info.pooled_tx = output["pooledtx"]
        info.chain = output["chain"]
        info.warnings = output["warnings"]
        return info

    get_network_info = graphene.Field(
        types.NetworkInfoType, testnet=graphene.Boolean())

    def resolve_get_network_info(self, info, **kwargs):
        """bitcoin-cli getnetworkinfo
        https://bitcoin.org/en/developer-reference#getnetworkinfo
        """

        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        output = make_rpc_auth_url(testnet).getnetworkinfo()
        info = types.NetworkInfoType()
        info.version = output["version"]
        info.subversion = output["subversion"]
        info.protocol_version = output["protocolversion"]
        info.local_services = output["localservices"]
        info.local_relay = output["localrelay"]
        info.time_offset = output["timeoffset"]
        info.network_active = output["networkactive"]
        info.connections = output["connections"]
        info.networks = output["networks"]
        info.relay_fee = output["relayfee"]
        info.incremental_fee = output["incrementalfee"]
        info.local_addresses = output["localaddresses"]
        info.warnings = output["warnings"]
        return info

    get_wallet_info = graphene.Field(
        types.WalletInfoType, testnet=graphene.Boolean())

    def resolve_get_wallet_info(self, info, **kwargs):
        """bitcoin-cli getwalletinfo
        https://bitcoin.org/en/developer-reference#getwalletinfo
        """

        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        output = make_rpc_auth_url(testnet).getwalletinfo()
        info = types.WalletInfoType()
        info.wallet_name = output["walletname"]
        info.wallet_version = output["walletversion"]
        info.balance = output["balance"]
        info.unconfirmed_balance = output["unconfirmed_balance"]
        info.immature_balance = output["immature_balance"]
        info.tx_count = output["txcount"]
        info.keypool_oldest = output["keypoololdest"]
        info.keypool_size = output["keypoolsize"]
        info.keypool_size_hd_internal = output["keypoolsize_hd_internal"]
        info.pay_tx_fee = output["paytxfee"]
        info.hd_master_key_id = output["hdmasterkeyid"]
        return info
