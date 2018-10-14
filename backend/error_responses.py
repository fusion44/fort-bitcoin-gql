"""Contains all common response statuses"""
import graphene

from backend.lnd.types import ResponseStatus


class Unauthenticated(graphene.ObjectType):
    error_message = graphene.String(default_value="Unauthenticated")


class ServerError(graphene.ObjectType):
    error_message = graphene.String()

    @staticmethod
    def generic_rpc_error(code: int, details: str):
        return ServerError(
            error_message="RPC call failed {0}: {1}".format(code, details))


class WalletInstanceNotFound(graphene.ObjectType):
    error_message = graphene.String(
        default_value="No wallet instance found for User")
    suggestions = graphene.String(
        default_value=
        "Use createLightningWallet and lnInitWallet to create the wallet")


class WalletInstanceNotRunning(graphene.ObjectType):
    error_message = graphene.String(
        default_value="Wallet instance found, but it is not running")
    suggestions = graphene.String(
        default_value="Use startDaemon start the wallet")


def ok() -> ResponseStatus:
    return ResponseStatus(200)


def custom(code: int, msg: str) -> ResponseStatus:
    return ResponseStatus(code, msg)


def unknown() -> ResponseStatus:
    return ResponseStatus(500, "An unknown error occurred")


def internal_server_error() -> ResponseStatus:
    return ResponseStatus(500, "Internal server error")


def unauthenticated() -> ResponseStatus:
    return ResponseStatus(403, "Unauthenticated")
