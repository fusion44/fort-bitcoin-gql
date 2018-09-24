"""A GraphQL API for the LND software
For a full description of all available API"s see https://api.lightning.community
"""
import json

import graphene
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.lnd import types
from backend.lnd.implementations import (
    AddInvoiceMutation, CreateLightningWalletMutation, DecodePayReqQuery,
    GenSeedQuery, GetChannelBalanceQuery, GetInfoQuery, GetTransactionsQuery,
    GetWalletBalanceQuery, InitWalletMutation, ListPaymentsQuery,
    SendPaymentMutation, StartDaemonMutation, StopDaemonMutation)
from backend.lnd.utils import build_grpc_channel


class InvoiceSubscription(graphene.ObjectType):
    invoice_subscription = graphene.Field(
        types.LnInvoice,
        description=
        "SubscribeInvoices returns a uni-directional stream (server -> client) for notifying the client of newly added/settled invoices. The caller can optionally specify the add_index and/or the settle_index. If the add_index is specified, then we’ll first start by sending add invoice events for all invoices with an add_index greater than the specified value. If the settle_index is specified, the next, we’ll send out all settle events for invoices with a settle_index greater than the specified value. One or both of these fields can be set. If no fields are set, then we’ll only send out the latest add/settle events.",
        testnet=graphene.Boolean(),
        add_index=graphene.Int(),
        settle_index=graphene.Int())

    async def resolve_invoice_subscription(self,
                                           info,
                                           testnet=True,
                                           add_index=None,
                                           settle_index=None):
        channel_data = build_grpc_channel(testnet, True)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.InvoiceSubscription(
            add_index=add_index,
            settle_index=settle_index,
        )

        async for response in stub.SubscribeInvoices(
                request, metadata=[('macaroon', channel_data.macaroon)]):
            json_data = json.loads(MessageToJson(response))
            invoice = types.LnInvoice(json_data)
            yield invoice


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
