import json

import graphene
from google.protobuf.json_format import MessageToJson
from grpc import RpcError

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInvoice
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class InvoiceSubSuccess(graphene.ObjectType):
    invoice = graphene.Field(
        LnInvoice, description="A new changed or changed invoice state")


class InvoiceSubError(graphene.ObjectType):
    payment_error = graphene.String(
        description="Error message with an error description")


class InvoiceSubPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, InvoiceSubError,
                 InvoiceSubSuccess)


class InvoiceSubscription(graphene.ObjectType):
    invoice_subscription = graphene.Field(
        InvoiceSubPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.SubscribeInvoices.__doc__),
        add_index=graphene.Int(),
        settle_index=graphene.Int())

    async def resolve_invoice_subscription(self,
                                           info,
                                           add_index=None,
                                           settle_index=None):
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
            request = ln.InvoiceSubscription(
                add_index=add_index,
                settle_index=settle_index,
            )
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=exc)

        try:
            async for response in stub.SubscribeInvoices(
                    request, metadata=[('macaroon', channel_data.macaroon)]):
                if not info.context["user"].is_authenticated:
                    yield Unauthenticated()
                else:
                    json_data = json.loads(MessageToJson(response))
                    invoice = InvoiceSubSuccess(LnInvoice(json_data))
                    yield invoice
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=exc)