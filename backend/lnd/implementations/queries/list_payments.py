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
from backend.lnd.types import LnPayment
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class ListPaymentsError(graphene.ObjectType):
    error_message = graphene.String()


class ListPaymentsSuccess(graphene.ObjectType):
    def __init__(self, first_index_offset, last_index_offset, payments):
        super().__init__()
        self.payments = []
        self.first_index_offset = first_index_offset
        self.last_index_offset = last_index_offset
        for payment in payments:
            self.payments.append(LnPayment(payment))

    payments = graphene.List(
        LnPayment,
        description=
        "A list of payments from the time slice of the time series specified in the request."
    )
    last_index_offset = graphene.Int(
        description=
        "The index of the last item in the set of returned payments. This can be used to seek further, pagination style."
    )
    first_index_offset = graphene.Int(
        description=
        "The index of the last item in the set of returned payments. This can be used to seek backwards, pagination style."
    )


class ListPaymentsResponse(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, ListPaymentsError,
                 ListPaymentsSuccess, WalletInstanceNotFound,
                 WalletInstanceNotRunning)


class ListPaymentsQuery(graphene.ObjectType):
    ln_list_payments = graphene.Field(
        ListPaymentsResponse,
        description=process_lnd_doc_string(
            lnrpc.LightningServicer.ListPayments.__doc__),
        index_offset=graphene.Int(
            default_value=0,
            description=
            "The index of an invoice that will be used as either the start or end of a query to determine which invoices should be returned in the response."
        ),
        num_max_payments=graphene.Int(
            default_value=100,
            description=
            "The max number of payments to return in the response to this query."
        ),
        reverse=graphene.Boolean(
            default_value=True,
            description=
            "If set, the payments returned will result from seeking backwards from the specified index offset. This can be used to paginate backwards."
        ),
    )

    def resolve_ln_list_payments(self, info, index_offset, num_max_payments,
                                 reverse):
        """https://api.lightning.community/?python#listpayments
        
        LND does not have paging in this call yet. Every gRPC
        call will always return the complete payments dataset.
        The paging functionality is implemented on top of the
        full dataset we get from the LND daemon.
        """

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
        request = ln.ListPaymentsRequest()

        try:
            response = stub.ListPayments(
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

        if reverse:
            # reverse the list
            rev = json_data["payments"][::-1]
            payments = rev[index_offset:index_offset + num_max_payments]
        else:
            payments = json_data["payments"][index_offset:index_offset +
                                             num_max_payments]

        return ListPaymentsSuccess(index_offset,
                                   index_offset + num_max_payments, payments)
