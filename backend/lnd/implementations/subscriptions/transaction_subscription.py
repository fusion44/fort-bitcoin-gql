import json

import graphene
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnTransaction
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class TransactionSubSuccess(graphene.ObjectType):
    transaction = graphene.Field(
        LnTransaction, description="The newly discovered transaction.")


class TransactionSubError(graphene.ObjectType):
    transaction_error = graphene.String(
        description="Error message with an error description")


class TransactionSubPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, TransactionSubError,
                 TransactionSubSuccess)


class TransactionSubscription(graphene.ObjectType):
    transaction_subscription = graphene.Field(
        TransactionSubPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.SubscribeTransactions.__doc__))

    async def resolve_transaction_subscription(
            self,
            info,
    ):
        try:
            if not info.context["user"].is_authenticated:
                yield Unauthenticated()
        except AttributeError as exc:
            print(exc)
            yield ServerError(
                "A server internal error (AttributeError) has occurred. :-(")

        res = LNDWallet.objects.filter(owner=info.context["user"])

        if not res:
            yield WalletInstanceNotFound()

        cfg = build_lnd_wallet_config(res.first().pk)

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path,
            is_async=True)

        if channel_data.error is not None:
            yield ServerError(error_message=channel_data.error)

        try:
            stub = lnrpc.LightningStub(channel_data.channel)
            request = ln.GetTransactionsRequest()
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=exc)

        try:
            async for response in stub.SubscribeTransactions(
                    request, metadata=[('macaroon', channel_data.macaroon)]):
                if not info.context["user"].is_authenticated:
                    yield Unauthenticated()
                else:
                    json_data = json.loads(MessageToJson(response))
                    transaction = TransactionSubSuccess(
                        LnTransaction(json_data))
                    yield transaction
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=exc)
