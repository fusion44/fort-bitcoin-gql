"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import graphene
from graphene_django.types import DjangoObjectType
from backend.lnd import models


class ResponseStatus(graphene.ObjectType):
    def __init__(self, code: int, form_error: str = "", suggestions: str = ""):
        super().__init__()
        self.code = code
        self.form_error = form_error
        self.suggestions = suggestions

    code = graphene.Int(
        description=
        "200 if successful or an appropriate HTTP statuscode is returned upon error"
    )
    form_error = graphene.String(
        description="Additional information about the error")
    suggestions = graphene.String(
        description=
        "If available, a suggestion how to fix this problem will be included")


class WalletType(DjangoObjectType):
    class Meta:
        model = models.LNDWallet


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


class LnPayment(graphene.ObjectType):
    """https://api.lightning.community/?shell#payment"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    payment_hash = graphene.String(description="The payment hash")
    value = graphene.Int(
        description="The value of the payment in satoshis", default_value=0)
    creation_date = graphene.Int(
        description="The date of this payment", default_value=0)
    path = graphene.List(
        graphene.String,
        description="The path this payment took",
        default_value=[])
    fee = graphene.Int(
        description="The fee paid for this payment in satoshis",
        default_value=0)
    payment_preimage = graphene.String(description="The payment preimage")


class LnGenSeedResponse(graphene.ObjectType):
    """https://api.lightning.community/?python#genseed"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    cipher_seed_mnemonic = graphene.List(
        graphene.String,
        description=
        "A 24-word mnemonic that encodes a prior aezeed cipher seed obtained by the user. This field is optional, as if not provided, then the daemon will generate a new cipher seed for the user. Otherwise, then the daemon will attempt to recover the wallet state linked to this cipher seed."
    )
    enciphered_seed = graphene.String(
        description=
        "The raw aezeed cipher seed bytes. This is the raw cipher text before run through our mnemonic encoding scheme."
    )


class LnListPaymentsResponse(graphene.ObjectType):
    """https://api.lightning.community/?python#listpaymentsresponse"""

    def __init__(self, data: dict):
        super().__init__()
        self.payments = []
        if "payments" in data:
            for payment in data["payments"]:
                self.payments.append(LnPayment(payment))

    payments = graphene.List(LnPayment, description="The list of payments")


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


class LnTransaction(graphene.ObjectType):
    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    tx_hash = graphene.String(description="The transaction hash")
    amount = graphene.Int(
        description="The transaction amount, denominated in satoshis",
        default_value=0)
    num_confirmations = graphene.Int(
        description="The number of confirmations", default_value=0)
    block_hash = graphene.String(
        description="The hash of the block this transaction was included in")
    block_height = graphene.Int(
        description="The height of the block this transaction was included in",
        default_value=0)
    time_stamp = graphene.Int(
        description="Timestamp of this transaction", default_value=0)
    total_fees = graphene.Int(
        description="Fees paid for this transaction", default_value=0)
    dest_addresses = graphene.List(
        graphene.String,
        description="Addresses that received funds for this transaction")


class LnTransactionDetails(graphene.ObjectType):
    def __init__(self, data: dict):
        super().__init__()
        self.transactions = []
        if "transactions" in data:
            for ta in data["transactions"]:
                self.transactions.append(LnTransaction(ta))

    transactions = graphene.List(
        LnTransaction,
        description="The list of transactions relevant to the wallet.")


class LnInvoice(graphene.ObjectType):
    class Meta:
        description = ""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                if attr == 'route_hints':
                    hints = []
                    for hint in data[attr]:
                        hints.append(LnHopHint(hint))
                    setattr(self, attr, hints)
                else:
                    setattr(self, attr, data[attr])

    memo = graphene.String(
        description=
        "An optional memo to attach along with the invoice. Used for record keeping purposes for the invoice’s creator, and will also be set in the description field of the encoded payment request if the description_hash field is not being used."
    )
    receipt = graphene.String(
        description="An optional cryptographic receipt of payment")
    r_preimage = graphene.String(
        description=
        "The hex-encoded preimage (32 byte) which will allow settling an incoming HTLC payable to this preimage"
    )
    r_hash = graphene.String(description="The hash of the preimage")
    value = graphene.Int(description="The value of this invoice in satoshis")
    settled = graphene.Boolean(
        description="Whether this invoice has been fulfilled")
    creation_date = graphene.Int(description="When this invoice was created")
    settle_date = graphene.Int(description="When this invoice was settled")
    payment_request = graphene.String(
        description=
        "A bare-bones invoice for a payment within the Lightning Network. With the details of the invoice, the sender has all the data necessary to send a payment to the recipient."
    )
    description_hash = graphene.String(
        description=
        "Hash (SHA-256) of a description of the payment. Used if the description of payment (memo) is too long to naturally fit within the description field of an encoded payment request."
    )
    expiry = graphene.Int(
        description=
        "Payment request expiry time in seconds. Default is 3600 (1 hour).")
    fallback_addr = graphene.String(description="Fallback on-chain address.")
    cltv_expiry = graphene.Int(
        description=
        "Delta to use for the time-lock of the CLTV extended to the final hop."
    )
    route_hints = graphene.List(
        LnHopHint,
        description=
        "Route hints that can each be individually used to assist in reaching the invoice’s destination."
    )
    private = graphene.Boolean(
        description=
        "Whether this invoice should include routing hints for private channels."
    )
    add_index = graphene.Int(
        description=
        "The “add” index of this invoice. Each newly created invoice will increment this index making it monotonically increasing. Callers to the SubscribeInvoices call can use this to instantly get notified of all added invoices with an add_index greater than this one."
    )
    settle_index = graphene.Int(
        description=
        "The “settle” index of this invoice. Each newly settled invoice will increment this index making it monotonically increasing. Callers to the SubscribeInvoices call can use this to instantly get notified of all settled invoices with an settle_index greater than this one."
    )
    amt_paid = graphene.Int(
        description=
        "The amount that was accepted for this invoice. This will ONLY be set if this invoice has been settled. We provide this field as if the invoice was created with a zero value, then we need to record what amount was ultimately accepted. Additionally, it’s possible that the sender paid MORE that was specified in the original invoice. So we’ll record that here as well."
    )


class LnAddInvoiceResponse(graphene.ObjectType):
    """https://api.lightning.community/?python#addinvoiceresponse"""

    def __init__(self, data: dict):
        super().__init__()
        for attr in self.__dict__.keys():  # type: str
            if attr in data:
                setattr(self, attr, data[attr])

    r_hash = graphene.String()
    payment_request = graphene.String(
        description=
        "A bare-bones invoice for a payment within the Lightning Network. With the details of the invoice, the sender has all the data necessary to send a payment to the recipient."
    )
    add_index = graphene.Int(
        description=
        "The “add” index of this invoice. Each newly created invoice will increment this index making it monotonically increasing. Callers to the SubscribeInvoices call can use this to instantly get notified of all added invoices with an add_index greater than this one.",
        default_value=0)


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
