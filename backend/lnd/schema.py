"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/."""

import json

import graphene
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
import backend.lnd.types as types
import backend.exceptions as exceptions
from backend.lnd.utils import ChannelData, build_grpc_channel
from grpc import RpcError
"""A simple GraphQL API for the c-lightning software
For a full description of all available API"s see https://github.com/ElementsProject/lightning
"""


class Query(graphene.ObjectType):
    """Contains all Lightning RPC queries"""

    ln_get_info = graphene.Field(
        types.LnInfoType,
        description=
        "GetInfo returns general information concerning the lightning node including it’s identity pubkey, alias, the chains it is connected to, and information concerning the number of open+pending channels.",
        testnet=graphene.Boolean())

    def resolve_ln_get_info(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.GetInfoRequest()
        response = stub.GetInfo(
            request, metadata=[('macaroon', channel_data.macaroon)])
        json_data = json.loads(MessageToJson(response))
        return types.LnInfoType(json_data)

    ln_get_channel_balance = graphene.Field(
        types.LnChannelBalance,
        description=
        "ChannelBalance returns the total funds available across all open channels in satoshis.",
        testnet=graphene.Boolean(),
    )

    def resolve_ln_get_channel_balance(self, info, **kwargs):
        """https://api.lightning.community/#channelbalance"""
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()
        testnet = kwargs.get("testnet")
        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.ChannelBalanceRequest()
        response = stub.ChannelBalance(
            request, metadata=[('macaroon', channel_data.macaroon)])
        json_data = json.loads(MessageToJson(response))
        return types.LnChannelBalance(json_data)

    ln_get_wallet_balance = graphene.Field(
        types.LnWalletBalance,
        description=
        "WalletBalance returns total unspent outputs(confirmed and unconfirmed), all confirmed unspent outputs and all unconfirmed unspent outputs under control of the wallet.",
        testnet=graphene.Boolean(),
    )

    def resolve_ln_get_wallet_balance(self, info, **kwargs):
        """https://api.lightning.community/#walletbalance"""
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()
        testnet = kwargs.get("testnet")
        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.WalletBalanceRequest()
        response = stub.WalletBalance(
            request, metadata=[('macaroon', channel_data.macaroon)])
        json_data = json.loads(MessageToJson(response))
        return types.LnWalletBalance(json_data)

    ln_get_transactions = graphene.Field(
        types.LnTransactionDetails,
        description=
        "GetTransactions returns a list describing all the known transactions relevant to the wallet.",
        testnet=graphene.Boolean(),
    )

    def resolve_ln_get_transactions(self, info, **kwargs):
        """https://api.lightning.community/?python#gettransactions"""
        if not info.context.user.is_authenticated:
            raise exceptions.unauthenticated()

        testnet = kwargs.get("testnet")
        channel_data = build_grpc_channel(testnet)
        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.GetTransactionsRequest()
        response = stub.GetTransactions(
            request, metadata=[('macaroon', channel_data.macaroon)])
        json_data = json.loads(MessageToJson(response))
        return types.LnTransactionDetails(json_data)

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


class LnMutations(graphene.ObjectType):
    class Meta:
        description = "Contains all mutations related to Lightning Network"

    ln_send_payment = SendPayment.Field()