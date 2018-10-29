"""Implementation for the init wallet mutation"""
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
from backend.lnd.types import LnAddInvoiceResponse
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class AddInvoiceSuccess(graphene.ObjectType):
    invoice = graphene.Field(LnAddInvoiceResponse)


class AddInvoiceError(graphene.ObjectType):
    payment_error = graphene.String(
        description="Error message if payment fails")


class AddInvoicePayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, AddInvoiceError,
                 AddInvoiceSuccess, WalletInstanceNotFound,
                 WalletInstanceNotRunning)


class AddInvoiceMutation(graphene.Mutation):
    class Arguments:
        value = graphene.Int(
            description="The value of this invoice in satoshis", required=True)

        memo = graphene.String(
            description=
            "An optional memo to attach along with the invoice. Used for record keeping purposes for the invoice’s creator, and will also be set in the description field of the encoded payment request if the description_hash field is not being used."
        )

    result = AddInvoicePayload()

    @staticmethod
    def description():
        """Returns the description for this mutation. 
        The String is fetched directly from the lnd grpc package
        """
        return process_lnd_doc_string(
            lnrpc.LightningServicer.AddInvoice.__doc__)

    def mutate(self, info, value, memo: str = ""):
        if not info.context.user.is_authenticated:
            return AddInvoiceMutation(result=Unauthenticated())

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return AddInvoiceMutation(result=WalletInstanceNotFound())

        cfg = build_lnd_wallet_config(res.first().pk)

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path,
        )
        if channel_data.error is not None:
            return AddInvoiceMutation(result=channel_data.error)

        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.Invoice(
            value=value,
            memo=memo,
            add_index=1,
        )

        try:
            response = stub.AddInvoice(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except RpcError as exc:
            # pylint: disable=E1101
            print(exc)
            return AddInvoiceMutation(
                result=ServerError.generic_rpc_error(exc.code(), exc.
                                                     details()))

        json_data = json.loads(MessageToJson(response))
        return AddInvoiceMutation(
            result=AddInvoiceSuccess(LnAddInvoiceResponse(json_data)))
