import codecs
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
from backend.lnd.types import ChannelPoint
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ChannelPendingUpdate(graphene.ObjectType):
    class Meta:
        description = "Update immediately after the funding tx was broadcast."

    channel_point = graphene.Field(ChannelPoint)


class ChannelConfirmationUpdate(graphene.ObjectType):
    class Meta:
        description = "Update when a new confirmation was found."

    block_sha = graphene.String()
    block_height = graphene.Int()
    num_confs_left = graphene.Int()


class ChannelOpenUpdate(graphene.ObjectType):
    class Meta:
        description = "Final update when the channel is open and fully usable"

    channel_point = graphene.Field(ChannelPoint)


class OpenChannelError(graphene.ObjectType):
    error_message = graphene.String()


class OpenChannelSubPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, OpenChannelError,
                 WalletInstanceNotRunning, ChannelPendingUpdate,
                 ChannelConfirmationUpdate, ChannelOpenUpdate)


class OpenChannelSubscription(graphene.ObjectType):

    open_channel_subscription = graphene.Field(
        OpenChannelSubPayload,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.OpenChannel.__doc__),
        node_pubkey=graphene.String(
            description=
            "The hex encoded pubkey of the node to open a channel with"),
        local_funding_amount=graphene.Int(
            description=
            "The number of satoshis the wallet should commit to the channel"),
        push_sat=graphene.Int(
            description=
            "The number of satoshis to push to the remote side as part of the initial commitment state"
        ),
        target_conf=graphene.Int(
            description=
            "The target number of blocks that the funding transaction should be confirmed by."
        ),
        sat_per_byte=graphene.Int(
            description=
            "A manual fee rate set in sat/byte that should be used when crafting the funding transaction."
        ),
        private=graphene.Boolean(
            description=
            "Whether this channel should be private, not announced to the greater network."
        ),
        min_htlc_msat=graphene.Int(
            description=
            "The minimum value in millisatoshi we will require for incoming HTLCs on the channel."
        ),
        remote_csv_delay=graphene.Int(
            description=
            "The delay we require on the remote’s commitment transaction. If this is not set, it will be scaled automatically with the channel size."
        ),
        min_confs=graphene.Int(
            description=
            "The minimum number of confirmations each one of your outputs used for the funding transaction must satisfy."
        ),
        spend_unconfirmed=graphene.Boolean(
            description=
            "Whether unconfirmed outputs should be used as inputs for the funding transaction."
        ))

    async def resolve_open_channel_subscription(self,
                                                info,
                                                node_pubkey,
                                                local_funding_amount,
                                                push_sat,
                                                private,
                                                min_htlc_msat,
                                                min_confs,
                                                spend_unconfirmed,
                                                sat_per_byte=None,
                                                remote_csv_delay=None,
                                                target_conf=None):
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

            request = ln.OpenChannelRequest(
                node_pubkey=codecs.decode(node_pubkey, 'hex'),
                local_funding_amount=local_funding_amount,
                push_sat=push_sat,
                target_conf=target_conf,
                sat_per_byte=sat_per_byte,
                private=private,
                min_htlc_msat=min_htlc_msat,
                remote_csv_delay=remote_csv_delay,
                min_confs=min_confs,
                # spend_unconfirmed=spend_unconfirmed
            )
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=str(exc))
            return

        try:
            async for response in stub.OpenChannel(
                    request, metadata=[('macaroon', channel_data.macaroon)]):
                if not info.context["user"].is_authenticated:
                    yield Unauthenticated()
                else:
                    json_data = json.loads(MessageToJson(response))

                    if "chan_pending" in json_data:
                        cp = json_data["chan_pending"]
                        txid = cp["txid"] if "txid" in cp else ""
                        output_index = cp[
                            "output_index"] if "output_index" in cp else 0

                        yield ChannelPendingUpdate(
                            channel_point=ChannelPoint(txid, output_index))
                    elif "confirmation" in json_data:
                        conf = json_data["confirmation"]
                        block_sha = conf[
                            "block_sha"] if "block_sha" in conf else ""
                        block_height = conf[
                            "block_height"] if "block_height" in conf else 0
                        num_confs_left = conf[
                            "num_confs_left"] if "num_confs_left" in conf else 0
                        yield ChannelConfirmationUpdate(
                            block_sha=block_sha,
                            block_height=block_height,
                            num_confs_left=num_confs_left)
                    elif "chan_open" in json_data:
                        co = json_data["chan_open"]["channel_point"]
                        txid = co["funding_txid_bytes"] if "funding_txid_bytes" in co else ""
                        output_index = cp[
                            "output_index"] if "output_index" in co else 0
                        yield ChannelOpenUpdate(
                            channel_point=ChannelPoint(txid, output_index))
        except RpcError as grpc_error:
            # pylint: disable=E1101
            print(grpc_error)
            print(grpc_error.details())
            yield OpenChannelError(grpc_error.details())
        except Exception as exc:
            print(exc)
            yield ServerError(error_message=exc)
