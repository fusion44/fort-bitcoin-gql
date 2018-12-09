"""A GraphQL API for the LND software
For a full description of all available API"s see https://api.lightning.community
"""

import graphene

from backend.lnd.implementations import (
    AddInvoiceMutation, CloseChannelSubscription, ConnectPeerMutation,
    CreateLightningWalletMutation, DecodePayReqQuery, DisconnectPeerMutation,
    GenSeedQuery, GetChannelBalanceQuery, GetInfoQuery, GetTransactionsQuery,
    GetWalletBalanceQuery, InitWalletMutation, InvoiceSubscription,
    ListChannelsQuery, ListPaymentsQuery, ListPeersQuery, NewAddressQuery,
    OpenChannelSubscription, SendPaymentMutation, StartDaemonMutation,
    StopDaemonMutation, TransactionSubscription)


class Queries(
        DecodePayReqQuery,
        GenSeedQuery,
        GetChannelBalanceQuery,
        GetInfoQuery,
        GetTransactionsQuery,
        GetWalletBalanceQuery,
        ListChannelsQuery,
        ListPaymentsQuery,
        ListPeersQuery,
        NewAddressQuery,
):
    pass


class LnMutations(graphene.ObjectType):
    class Meta:
        description = "Contains all mutations related to Lightning Network"

    create_lightning_wallet = CreateLightningWalletMutation.Field(
        description=CreateLightningWalletMutation.description())
    ln_send_payment = SendPaymentMutation.Field(
        description=SendPaymentMutation.description())
    ln_add_invoice = AddInvoiceMutation.Field(
        description=AddInvoiceMutation.description())
    ln_connect_peer = ConnectPeerMutation.Field(
        description=ConnectPeerMutation.description())
    ln_disconnect_peer = DisconnectPeerMutation.Field(
        description=DisconnectPeerMutation.description())
    ln_init_wallet = InitWalletMutation.Field(
        description=InitWalletMutation.description())
    start_daemon = StartDaemonMutation.Field(
        description=StartDaemonMutation.description())
    ln_stop_daemon = StopDaemonMutation.Field(
        description=StopDaemonMutation.description())


class LnSubscriptions(CloseChannelSubscription, InvoiceSubscription,
                      OpenChannelSubscription, TransactionSubscription):
    pass
