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
from backend.lnd.types import LnFeeLimit, LnRawPaymentInput, LnRoute
from backend.lnd.utils import (build_grpc_channel_manual,
                               build_lnd_wallet_config, process_lnd_doc_string)


class SendPaymentSuccess(graphene.ObjectType):
    payment_preimage = graphene.String(description="Preimage of the payment")
    payment_route = graphene.Field(LnRoute)


class SendPaymentError(graphene.ObjectType):
    payment_error = graphene.String(
        description="Error message if payment fails")


class SendPaymentPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, ServerError, SendPaymentError,
                 SendPaymentSuccess, WalletInstanceNotRunning)


class SendPaymentMutation(graphene.Mutation):
    class Arguments:
        payment_raw = LnRawPaymentInput()
        payment_request = graphene.String(
            description=
            "A bare-bones invoice for a payment within the Lightning Network. With the details of the invoice, the sender has all the data necessary to send a payment to the recipient."
        )
        final_cltv_delta = graphene.Int(
            description=
            "The CLTV delta from the current height that should be used to set the timelock for the final hop."
        )
        fee_limit = LnFeeLimit()

    payment_result = SendPaymentPayload()

    @staticmethod
    def description():
        """Returns the description for this mutation. 
        The String is fetched directly from the lnd grpc package
        """
        return process_lnd_doc_string(
            lnrpc.LightningServicer.SendPaymentSync.__doc__)

    def mutate(self,
               info,
               payment_raw: LnRawPaymentInput = None,
               payment_request: str = "",
               final_cltv_delta: int = 0,
               fee_limit: LnFeeLimit = None):

        if not info.context.user.is_authenticated:
            return SendPaymentMutation(payment_result=Unauthenticated())

        res = LNDWallet.objects.filter(owner=info.context.user)

        if not res:
            return SendPaymentMutation(payment_result=WalletInstanceNotFound())

        cfg = build_lnd_wallet_config(res.first().pk)

        channel_data = build_grpc_channel_manual(
            rpc_server="127.0.0.1",
            rpc_port=cfg.rpc_listen_port_ipv4,
            cert_path=cfg.tls_cert_path,
            macaroon_path=cfg.admin_macaroon_path,
        )
        if channel_data.error is not None:
            return SendPaymentMutation(payment_result=channel_data.error)

        stub = lnrpc.LightningStub(channel_data.channel)
        request = ln.SendRequest(payment_request=payment_request)
        try:
            response = stub.SendPaymentSync(
                request, metadata=[('macaroon', channel_data.macaroon)])
        except RpcError as exc:
            # pylint: disable=E1101
            print(exc)
            if exc.details().startswith("invoice expired"):
                return SendPaymentMutation(
                    payment_result=SendPaymentError(exc.details()))
            return SendPaymentMutation(
                payment_result=ServerError.generic_rpc_error(
                    exc.code(), exc.details()))

        json_data = json.loads(MessageToJson(response))

        if response.payment_error:
            err = SendPaymentError(payment_error=response.payment_error)
            return SendPaymentMutation(payment_result=err)

        res = SendPaymentSuccess(
            payment_preimage=response.payment_preimage,
            payment_route=LnRoute(json_data["payment_route"]))
        return SendPaymentMutation(payment_result=res)
