"""A GraphQL API for the LND software
For a full description of all available API"s see https://api.lightning.community
"""

import graphene

from backend.lnd.implementations import (
    AddInvoiceMutation, CreateLightningWalletMutation, DecodePayReqQuery,
    GenSeedQuery, GetChannelBalanceQuery, GetInfoQuery, GetTransactionsQuery,
    GetWalletBalanceQuery, InitWalletMutation, InvoiceSubscription,
    ListPaymentsQuery, SendPaymentMutation, StartDaemonMutation,
    StopDaemonMutation)
from backend.lnd.utils import build_grpc_channel


class Queries(
        DecodePayReqQuery,
        GenSeedQuery,
        GetChannelBalanceQuery,
        GetInfoQuery,
        GetTransactionsQuery,
        GetWalletBalanceQuery,
        ListPaymentsQuery,
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
    ln_init_wallet = InitWalletMutation.Field(
        description=InitWalletMutation.description())
    start_daemon = StartDaemonMutation.Field(
        description=StartDaemonMutation.description())
    ln_stop_daemon = StopDaemonMutation.Field(
        description=StopDaemonMutation.description())


class LnSubscriptions(InvoiceSubscription):
    pass
