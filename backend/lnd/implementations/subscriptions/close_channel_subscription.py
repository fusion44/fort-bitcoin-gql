import json

import graphene
from google.protobuf.json_format import MessageToJson
from grpc import RpcError

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ChannelClosePendingUpdate(graphene.ObjectType):
    txid = graphene.String()


class ChannelCloseUpdate(graphene.ObjectType):
    closing_txid = graphene.String()
    success = graphene.Boolean()


class CloseChannelError(graphene.ObjectType):
    error_message = graphene.String()


class CloseChannelSubPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, CloseChannelError,
                 WalletInstanceNotRunning, ChannelClosePendingUpdate,
                 ChannelCloseUpdate)


class CloseChannelSubscription(graphene.ObjectType):

    close_channel_subscription = graphene.Field(
        CloseChannelSubPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.CloseChannel.__doc__),
        funding_txid=graphene.String(
            required=True,
            description=
            "Hex-encoded string representing the funding transaction"),
        output_index=graphene.Int(
            required=True,
            description="The index of the output of the funding transaction"),
        force=graphene.Boolean(
            description=
            "If true, then the channel will be closed forcibly. This means the current commitment transaction will be signed and broadcast."
        ),
        target_conf=graphene.Int(
            required=False,
            description=
            "The target number of blocks that the closure transaction should be confirmed by."
        ),
        sat_per_byte=graphene.Int(
            required=False,
            description=
            "A manual fee rate set in sat/byte that should be used when crafting the closure transaction."
        ),
    )

    async def resolve_close_channel_subscription(self,
                                                 info,
                                                 funding_txid,
                                                 output_index,
                                                 force,
                                                 target_conf=None,
                                                 sat_per_byte=None):
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
            yield channel_data.error

        try:
            stub = lnrpc.LightningStub(channel_data.channel)

            request = ln.CloseChannelRequest(
                channel_point={
                    "funding_txid_str": funding_txid,
                    "output_index": output_index
                },
                force=force,
                target_conf=target_conf,
                sat_per_byte=sat_per_byte,
            )
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=str(exc))

        try:
            async for response in stub.CloseChannel(
                    request, metadata=[('macaroon', channel_data.macaroon)]):
                if not info.context["user"].is_authenticated:
                    yield Unauthenticated()
                else:
                    json_data = json.loads(MessageToJson(response))

                    if "close_pending" in json_data:
                        cp = json_data["close_pending"]
                        txid = cp["txid"] if "txid" in cp else ""
                        output_index = cp[
                            "output_index"] if "output_index" in cp else 0

                        yield ChannelClosePendingUpdate(txid=txid)
                    elif "chan_close" in json_data:
                        cc = json_data["chan_close"]
                        txid = cc[
                            "closing_txid"] if "closing_txid" in cc else ""
                        success = cc["success"] if "success" in cc else False
                        yield ChannelCloseUpdate(closing_txid=txid, success=success)
                    else:
                        msg = "Unknown update from LND: {}".format(json_data)
                        print(msg)
                        yield ServerError(error_message=msg)
        except RpcError as grpc_error:
            # pylint: disable=E1101
            print(grpc_error)
            print(grpc_error.details())
            yield CloseChannelError(grpc_error.details())
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=exc)
