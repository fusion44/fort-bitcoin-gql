import json

import graphene
import grpc
from google.protobuf.json_format import MessageToJson

import backend.lnd.rpc_pb2 as ln
import backend.lnd.rpc_pb2_grpc as lnrpc
from backend.error_responses import (ServerError, Unauthenticated,
                                     WalletInstanceNotFound,
                                     WalletInstanceNotRunning)
from backend.lnd.models import LNDWallet
from backend.lnd.types import LnInvoice
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ListInvoicesError(graphene.ObjectType):
    error_message = graphene.String()


class ListInvoicesSuccess(graphene.ObjectType):
    def __init__(self, data: dict):
        super().__init__()
        self.invoices = []
        self.first_index_offset = int(data["first_index_offset"])
        self.last_index_offset = int(data["last_index_offset"])
        if "invoices" in data:
            for invoice in data["invoices"]:
                self.invoices.append(LnInvoice(invoice))

    invoices = graphene.List(
        LnInvoice,
        description=
        "A list of invoices from the time slice of the time series specified in the request."
    )
    last_index_offset = graphene.Int(
        description=
        "The index of the last item in the set of returned invoices. This can be used to seek further, pagination style."
    )
    first_index_offset = graphene.Int(
        description=
        "The index of the last item in the set of returned invoices. This can be used to seek backwards, pagination style."
    )


class ListInvoicesResponse(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, ListInvoicesError,
                 ListInvoicesSuccess, WalletInstanceNotFound,
                 WalletInstanceNotRunning)


class ListInvoicesQuery(graphene.ObjectType):
    ln_list_invoices = graphene.Field(
        ListInvoicesResponse,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.ListInvoices.__doc__),
        pending_only=graphene.Boolean(
            default_value=False,
            description=
            "If set, only unsettled invoices will be returned in the response."
        ),
        index_offset=graphene.Int(
            default_value=0,
            description=
            "The index of an invoice that will be used as either the start or end of a query to determine which invoices should be returned in the response."
        ),
        num_max_invoices=graphene.Int(
            default_value=100,
            description=
            "The max number of invoices to return in the response to this query."
        ),
        reverse=graphene.Boolean(
            default_value=True,
            description=
            "If set, the invoices returned will result from seeking backwards from the specified index offset. This can be used to paginate backwards."
        ),
    )

    def resolve_ln_list_invoices(self, info, pending_only, index_offset,
                                 num_max_invoices, reverse):
        """https://api.lightning.community/?python#listinvoices"""

        if not info.context.user.is_authenticated:
            return Unauthenticated()

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return WalletInstanceNotFound()

        cfg = build_lnd_wallet_config(res.first().pk)

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path)
        if channel_data.error is not None:
            return channel_data.error

        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.ListInvoiceRequest(
            pending_only=pending_only,
            index_offset=index_offset,
            num_max_invoices=num_max_invoices,
            reversed=reverse,
        )

        try:
            response = stub.ListInvoices(
                request, metadata=[('macaroon', channel_data.macaroon)])
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
        return ListInvoicesSuccess(json_data)
