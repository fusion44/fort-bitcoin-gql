"""Contains all types necessary for the Server

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene


class RejectType(graphene.ObjectType):
    status = graphene.Boolean()

    def __init__(self, status=True):
        self.status = status


class SoftforkType(graphene.ObjectType):
    """Object describing a soft fork"""
    id = graphene.String()
    version = graphene.Int()
    reject = graphene.Field(RejectType)

    @staticmethod
    def resolve_id(self, context, **kwargs):
        return self["id"]

    @staticmethod
    def resolve_version(self, context, **kwargs):
        return self["version"]

    @staticmethod
    def resolve_reject(self, context, **kwargs):
        return RejectType(status=self["reject"]["status"])


class NetworkType(graphene.ObjectType):
    """Describing the network connection type"""
    name = graphene.String()
    limited = graphene.Boolean()
    reachable = graphene.Boolean()
    proxy = graphene.String()
    proxy_randomize_credentials = graphene.Boolean()


class BlockchainInfoType(graphene.ObjectType):
    """bitcoin-cli getblockchaininfo"""
    chain = graphene.String()
    blocks = graphene.Int()
    headers = graphene.Int()
    best_block_hash = graphene.String()
    difficulty = graphene.String()
    median_time = graphene.Int()
    verification_progress = graphene.String()
    initial_block_download = graphene.Boolean()
    chain_work = graphene.String()
    size_on_disk = graphene.String()
    pruned = graphene.Boolean()
    softforks = graphene.List(SoftforkType)
    bip9_softforks = graphene.JSONString()
    warnings = graphene.String()


class MiningInfoType(graphene.ObjectType):
    """bitcoin-cli getmininginfo"""
    blocks = graphene.Int()
    current_block_weight = graphene.Int()
    current_block_tx = graphene.Int()
    difficulty = graphene.String()
    network_hash_hps = graphene.String()
    pooled_tx = graphene.Int()
    chain = graphene.String()
    warnings = graphene.String()


class NetworkInfoType(graphene.ObjectType):
    """bitcoin-cli getnetworkinfo"""
    version = graphene.Int()
    subversion = graphene.String()
    protocol_version = graphene.Int()
    local_services = graphene.String()
    local_relay = graphene.Boolean()
    time_offset = graphene.Int()
    network_active = graphene.Boolean()
    connections = graphene.Int()
    networks = graphene.List(NetworkType)
    relay_fee = graphene.String()
    incremental_fee = graphene.String()
    local_addresses = graphene.List(graphene.String)
    warnings = graphene.String()


class WalletInfoType(graphene.ObjectType):
    """bitcoin-cli getwalletinfo"""
    wallet_name = graphene.String()
    wallet_version = graphene.Int()
    balance = graphene.Float()
    unconfirmed_balance = graphene.Float()
    immature_balance = graphene.Float()
    tx_count = graphene.Int()
    keypool_oldest = graphene.Int()
    keypool_size = graphene.Int()
    keypool_size_hd_internal = graphene.Int()
    pay_tx_fee = graphene.Float()
    hd_master_key_id = graphene.String()
