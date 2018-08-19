"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene


class LnInfoType(graphene.ObjectType):
    """lightning-cli getinfo
    https://api.lightning.community/?python#getinforesponse
    """

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    identity_pubkey = graphene.String(
        description="The identity pubkey of the current node.")
    alias = graphene.String(
        description="If applicable, the alias of the current node, e.g. 'bob'")
    num_pending_channels = graphene.Int(
        description="Number of pending channels")
    num_active_channels = graphene.Int(description="Number of active channels")
    num_peers = graphene.Int(description="Number of peers")
    block_height = graphene.Int(
        description="The node’s current view of the height of the best block")
    block_hash = graphene.String(
        description="The node’s current view of the hash of the best block")
    synced_to_chain = graphene.Boolean(
        description="Whether the wallet’s view is synced to the main chain")
    testnet = graphene.Boolean(
        description="Whether the current node is connected to testnet")
    chains = graphene.List(
        graphene.String,
        description="A list of active chains the node is connected to")
    uris = graphene.List(
        graphene.String, description="The URIs of the current node.")
    best_header_timestamp = graphene.Int(
        description="Timestamp of the block best known to the wallet")
    version = graphene.String(
        description="The version of the LND software that the node is running."
    )


class LnChannelBalance(graphene.ObjectType):
    """https://api.lightning.community/#channelbalance"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    balance = graphene.Int(
        description="Sum of channels balances denominated in satoshis",
        default_value=0)
    pending_open_balance = graphene.Int(
        description="Sum of channels pending balances denominated in satoshis",
        default_value=0)


class LnWalletBalance(graphene.ObjectType):
    """https://api.lightning.community/#walletbalance"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    total_balance = graphene.Int(
        description="The balance of the wallet", default_value=0)
    confirmed_balance = graphene.Int(
        description=
        "The confirmed balance of a wallet(with >= 1 confirmations)",
        default_value=0)
    unconfirmed_balance = graphene.Int(
        description="The unconfirmed balance of a wallet(with 0 confirmations)",
        default_value=0)


class LnHopHint(graphene.ObjectType):
    """https://api.lightning.community/?python#hophint"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    node_id = graphene.String(
        description="The public key of the node at the start of the channel.")
    chan_id = graphene.Int(description="The unique identifier of the channel.")
    fee_base_msat = graphene.Int(
        description="The base fee of the channel denominated in millisatoshis."
    )
    fee_proportional_millionths = graphene.Int(
        description=
        "The fee rate of the channel for sending one satoshi across it denominated in millionths of a satoshi."
    )
    cltv_expiry_delta = graphene.Int(
        description="The time-lock delta of the channel.")


class LnHop(graphene.ObjectType):
    """https://api.lightning.community/?python#hop"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    chan_id = graphene.String(
        description=
        "The unique channel ID for the channel. The first 3 bytes are the block height, the next 3 the index within the block, and the last 2 bytes are the output index for the channel."
    )
    chan_capacity = graphene.Int()
    amt_to_forward = graphene.Int()
    fee = graphene.Int()
    expiry = graphene.Int()
    amt_to_forward_msat = graphene.Int()
    fee_msat = graphene.Int()


class LnRoute(graphene.ObjectType):
    """https://api.lightning.community/?python#route"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                if attr == 'hops':
                    hops = []
                    for hop in data[attr]:
                        hops.append(LnHop(hop))
                    setattr(self, attr, hops)
                else:
                    setattr(self, attr, data[attr])

    total_time_lock = graphene.Int(
        description=
        "The cumulative (final) time lock across the entire route. This is the CLTV value that should be extended to the first hop in the route. All other hops will decrement the time-lock as advertised, leaving enough time for all hops to wait for or present the payment preimage to complete the payment."
    )
    total_fees = graphene.Int(
        description=
        "The sum of the fees paid at each hop within the final route. In the case of a one-hop payment, this value will be zero as we don’t need to pay a fee it ourself."
    )
    total_amt = graphene.Int(
        description=
        "The total amount of funds required to complete a payment over this route. This value includes the cumulative fees at each hop. As a result, the HTLC extended to the first-hop in the route will need to have at least this many satoshis, otherwise the route will fail at an intermediate node due to an insufficient amount of fees."
    )
    hops = graphene.List(
        LnHop,
        description=
        "Contains details concerning the specific forwarding details at each hop."
    )
    total_fees_msat = graphene.Int(
        description="The total fees in millisatoshis.")
    total_amt_msat = graphene.Int(
        description="The total amount in millisatoshis.")


class LnRouteHint(graphene.ObjectType):
    """https://api.lightning.community/?python#routehint"""
    hop_hints = graphene.List(
        LnHopHint,
        description=
        "A list of hop hints that when chained together can assist in reaching a specific destination."
    )


class LnPayReqType(graphene.ObjectType):
    """https://api.lightning.community/?python#payreq"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    destination = graphene.String()
    payment_hash = graphene.String()
    num_satoshis = graphene.Int()
    timestamp = graphene.Int()
    expiry = graphene.Int()
    description = graphene.String()
    description_hash = graphene.String()
    fallback_addr = graphene.String()
    cltv_expiry = graphene.Int()
    route_hints = graphene.List(LnRouteHint)


class LnRawPaymentInput(graphene.InputObjectType):
    class Meta:
        description = "Describes a send payment request using components that make up a payment"

    dest = graphene.String(
        description="The identity pubkey of the payment recipient")
    dest_string = graphene.String(
        description="The hex-encoded identity pubkey of the payment recipient")
    amt = graphene.Int(description="Number of satoshis to send.")
    payment_hash = graphene.String(
        description="The hash to use within the payment’s HTLC.")
    payment_hash_string = graphene.String(
        description="The hex-encoded hash to use within the payment’s HTLC")


class LnFeeLimit(graphene.InputObjectType):
    class Meta:
        description = "The maximum number of satoshis that will be paid as a fee of the payment. This value can be represented either as a percentage of the amount being sent, or as a fixed amount of the maximum fee the user is willing the pay to send the payment."

    fixed = graphene.Int(
        description="The fee limit expressed as a fixed amount of satoshis.")
    percent = graphene.Int(
        description=
        "The fee limit expressed as a percentage of the payment amount.")
