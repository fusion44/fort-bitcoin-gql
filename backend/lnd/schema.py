"""A GraphQL API for the LND software
For a full description of all available API"s see https://api.lightning.community
"""
import json

import graphene
from google.protobuf.json_format import MessageToJson
from grpc import RpcError

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend import exceptions
from backend.lnd import types
from backend.lnd.implementations import (
    CreateLightningWalletMutation, GenSeedQuery, GetChannelBalanceQuery,
    GetInfoQuery, GetTransactionsQuery, GetWalletBalanceQuery,
    InitWalletMutation, StartDaemonMutation, StopDaemonMutation)
from backend.lnd.utils import build_grpc_channel


class Query(graphene.ObjectType):
    """Contains some Lightning RPC queries"""

    ln_decode_pay_req = graphene.Field(
        types.LnPayReqType,
        description=
        "DecodePayReq takes an encoded payment request string and attempts to decode it, returning a full description of the conditions encoded within the payment request.",
        testnet=graphene.Boolean(),
        pay_req=graphene.String(
            required=True,
            description="The payment request string to be decoded"))

    def resolve_ln_decode_pay_req(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()
        testnet = kwargs.get("testnet")
        pay_req = kwargs.get("pay_req")
        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.PayReqString(pay_req=pay_req)
        response = stub.DecodePayReq(
            request, metadata=[('macaroon', channel_data.macaroon)])
        json_data = json.loads(MessageToJson(response))
        return types.LnPayReqType(json_data)

    ln_list_payments = graphene.Field(
        types.LnListPaymentsResponse,
        description="ListPayments returns a list of all outgoing payments.",
        testnet=graphene.Boolean())

    def resolve_ln_list_payments(self, info, **kwargs):
        """https://api.lightning.community/?python#listpayments"""
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.ListPaymentsRequest()
        response = stub.ListPayments(
            request, metadata=[('macaroon', channel_data.macaroon)])
        json_data = json.loads(MessageToJson(response))
        return types.LnListPaymentsResponse(json_data)


def request_generator(testnet=True,
                      dest="",
                      dest_string="",
                      amt=0,
                      payment_hash="",
                      payment_hash_string="",
                      payment_request="",
                      final_cltv_delta=0,
                      fee_limit=None):
    if payment_request != "":
        while True:
            print("trying...")
            request = ln.SendRequest(
                payment_request=str.encode(payment_request))
            yield request
    else:
        while True:
            request = ln.SendRequest(
                dest=dest,
                dest_string=dest_string,
                amt=amt,
                payment_hash=payment_hash,
                payment_hash_string=payment_hash_string,
                final_cltv_delta=final_cltv_delta,
                fee_limit=fee_limit)
            yield request
            # Do things between iterations here.


class AddInvoice(graphene.Mutation):
    class Arguments:
        testnet = graphene.Boolean()
        memo = graphene.String(
            description=
            "An optional memo to attach along with the invoice. Used for record keeping purposes for the invoice’s creator, and will also be set in the description field of the encoded payment request if the description_hash field is not being used."
        )
        value = graphene.Int(
            description="The value of this invoice in satoshis", required=True)

    description = "AddInvoice attempts to add a new invoice to the invoice database. Any duplicated invoices are rejected, therefore all invoices must have a unique payment preimage."

    response = graphene.Field(types.LnAddInvoiceResponse)

    @classmethod
    def mutate(cls, root, info, value, testnet: bool = True, memo: str = ""):
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.Invoice(
            value=value,
            memo=memo,
            add_index=1,
        )

        try:
            response = stub.AddInvoice(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except RpcError as e:
            raise exceptions.custom(str(e))

        json_data = json.loads(MessageToJson(response))
        return AddInvoice(response=types.LnAddInvoiceResponse(json_data))


class SendPayment(graphene.Mutation):
    class Arguments:
        testnet = graphene.Boolean()
        payment_raw = types.LnRawPaymentInput()
        payment_request = graphene.String(
            description=
            "A bare-bones invoice for a payment within the Lightning Network. With the details of the invoice, the sender has all the data necessary to send a payment to the recipient."
        )
        final_cltv_delta = graphene.Int(
            description=
            "The CLTV delta from the current height that should be used to set the timelock for the final hop."
        )
        fee_limit = types.LnFeeLimit()

    description = "SendPayment sends a payment through the Lightning Network"

    payment_error = graphene.String(
        description="Error message if payment fails")
    payment_preimage = graphene.String(description="Preimage of the payment")
    payment_route = graphene.Field(types.LnRoute)

    @classmethod
    def mutate(cls,
               root,
               info,
               testnet: bool = True,
               payment_raw: types.LnRawPaymentInput = None,
               payment_request: str = "",
               final_cltv_delta: int = 0,
               fee_limit: types.LnFeeLimit = None):

        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.SendRequest(payment_request=payment_request)
        try:
            response = stub.SendPaymentSync(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except RpcError as e:
            return SendPayment(
                payment_error=e.details(),  # pylint: disable=E1101
                payment_preimage="",
                payment_route=None)

        json_data = json.loads(MessageToJson(response))
        if response.payment_error is not "":
            return SendPayment(
                payment_error=response.payment_error,
                payment_preimage="",
                payment_route=None)
        else:
            return SendPayment(
                payment_error=response.payment_error,
                payment_preimage=response.payment_preimage,
                payment_route=types.LnRoute(json_data["payment_route"]))


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
        GenSeedQuery,
        GetChannelBalanceQuery,
        GetInfoQuery,
        GetTransactionsQuery,
        GetWalletBalanceQuery,
):
    pass


class LnMutations(graphene.ObjectType):
    class Meta:
        description = "Contains all mutations related to Lightning Network"

    create_lightning_wallet = CreateLightningWalletMutation.Field(
        description="Creates a new wallet for the logged in user")
    ln_send_payment = SendPayment.Field()
    ln_add_invoice = AddInvoice.Field()
    ln_init_wallet = InitWalletMutation.Field(
        description=
        "Used when lnd is starting up for the first time to fully initialize the daemon and its internal wallet. At the very least a wallet password must be provided. This will be used to encrypt sensitive material on disk. In the case of a recovery scenario, the user can also specify their aezeed mnemonic and passphrase. If set, then the daemon will use this prior state to initialize its internal wallet. Alternatively, this can be used along with the GenSeed RPC to obtain a seed, then present it to the user. Once it has been verified by the user, the seed can be fed into this RPC in order to commit the new wallet."
    )
    start_daemon = StartDaemonMutation.Field(
        description=
        "StartDaemon will start the daemon and initialize the wallet if the password is provided"
    )
    ln_stop_daemon = StopDaemonMutation.Field(
        description=
        "StopDaemon will send a shutdown request to the interrupt handler, triggering a graceful shutdown of the daemon."
    )
