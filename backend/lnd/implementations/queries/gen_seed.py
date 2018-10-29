"""Implementation for the generate seed query"""

import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnGenSeedResponse
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config)


class GenSeedWalletInstanceNotFound(graphene.ObjectType):
    error_message = graphene.String(
        default_value="No wallet instance found for User")
    suggestions = graphene.String(
        default_value=
        "Use createLightningWallet and lnInitWallet to create the wallet")


class GenSeedError(graphene.ObjectType):
    error_message = graphene.String()


class GenSeedSuccess(graphene.ObjectType):
    ln_seed = graphene.Field(LnGenSeedResponse)


class GenSeedPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, GenSeedWalletInstanceNotFound,
                 WalletInstanceNotRunning, GenSeedError, GenSeedSuccess)


class GenSeedQuery(graphene.ObjectType):
    ln_gen_seed = graphene.Field(
        GenSeedPayload,
        description=
        "GenSeed is the first method that should be used to instantiate a new lnd instance. This method allows a caller to generate a new aezeed cipher seed given an optional passphrase. If provided, the passphrase will be necessary to decrypt the cipherseed to expose the internal wallet seed. Once the cipherseed is obtained and verified by the user, the InitWallet method should be used to commit the newly generated seed, and create the wallet.",
        aezeed_passphrase=graphene.String(
            description=
            "An optional user provided passphrase that will be used to encrypt the generated aezeed cipher seed."
        ),
        seed_entropy=graphene.String(
            description=
            "An optional 16-bytes generated via CSPRNG. If not specified, then a fresh set of randomness will be used to create the seed."
        ))

    def resolve_ln_gen_seed(self,
                            info,
                            aezeed_passphrase=None,
                            seed_entropy=None):
        """https://api.lightning.community/?python#genseed"""

        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return GenSeedWalletInstanceNotFound()

        # we currently only allow one wallet per user anyway,
        # so just get the first one
        return gen_seed_query(
            res.first(),
            aezeed_passphrase=aezeed_passphrase,
            seed_entropy=seed_entropy)


def gen_seed_query(
        wallet: LNDWallet,
        aezeed_passphrase: str,
        seed_entropy: str,
):
    cfg = build_lnd_wallet_config(wallet.pk)

    channel_data = build_grpc_channel_manual(
        rpc_server="127.0.0.1",
        rpc_port=cfg.rpc_listen_port_ipv4,
        cert_path=cfg.tls_cert_path,
    )

    if channel_data.error is not None:
        return channel_data.error

    stub = lnrpc.WalletUnlockerStub(channel_data.channel)
    request = ln.GenSeedRequest(
        aezeed_passphrase=aezeed_passphrase, seed_entropy=seed_entropy)
    try:
        response = stub.GenSeed(request)
    except grpc.RpcError as exc:
        # pylint: disable=E1101
        print(exc)
        return ServerError.generic_rpc_error(exc.code(), exc.details())

    json_data = json.loads(
        MessageToJson(
            response,
            preserving_proto_field_name=True,
            including_default_value_fields=True,
        ))
    return GenSeedSuccess(ln_seed=LnGenSeedResponse(json_data))
