"""Implementation for the create wallet mutation"""
import collections
import os
import subprocess

import graphene

from backend.error_responses import Unauthenticated
from backend.lnd import models
from backend.lnd.types import WalletType
from backend.lnd.utils import build_lnd_startup_args

CreateWalletMutationData = collections.namedtuple('CreateWalletMutationData',
                                                  ['lnd_wallet', 'status'])


class CreateWalletSuccess(graphene.ObjectType):
    wallet = graphene.Field(WalletType)


class CreateWalletExistsError(graphene.ObjectType):
    error_message = graphene.String(default_value="Max wallet limit reached")


class CreateWalletPayload(graphene.Union):
    class Meta:
        types = (Unauthenticated, CreateWalletExistsError, CreateWalletSuccess)


class CreateLightningWalletMutation(graphene.Mutation):
    """Starts up a new LND process for the user if he doesn't have one
    Once started GenSeed can be called on the instance.
    InitWallet must be called after creating the wallet
    """

    class Arguments:
        autopilot = graphene.Boolean(
            default_value=False,
            description="Whether the autopilot should be used")
        name = graphene.String(required=True, description="Name of the wallet")
        public_alias = graphene.String(
            description="Network visible alias for the node")

    Output = CreateWalletPayload

    @staticmethod
    def description():
        """Returns the description for this mutation. 
        """
        return "Creates a LND instance for the requesting user. This only creates the instance but does not initialize the wallet. This instance can be used to fetch the Wallet Seed now, until the user accepts the seed and initializes the wallet"

    def mutate(self, info, autopilot: bool, name: str, public_alias: str):
        if not info.context.user.is_authenticated:
            return Unauthenticated()

        return create_wallet_mutation(autopilot, name, public_alias,
                                      info.context.user)


def create_wallet_mutation(autopilot: bool, name: str, public_alias: str,
                           user):
    """Creates a LND instance for the requesting user
    This only creates the instance but does not initialize the wallet.
    This instance can be used to fetch the Wallet Seed now, until the
    user accepts the seed and initializes the wallet
    """
    res = models.LNDWallet.objects.filter(owner=user)

    # technically it is possible to have more, but we
    # don't allow more than one wallet per user
    if res:
        return CreateWalletExistsError()

    wallet = models.LNDWallet()
    wallet.owner = user
    wallet.public_alias = public_alias
    wallet.name = name
    wallet.testnet = True
    wallet.initialized = False
    wallet.save()

    args = build_lnd_startup_args(autopilot, wallet)

    if not os.path.exists(args["data_dir"]):
        os.makedirs(args["data_dir"])

    # Start LND instance
    subprocess.Popen(
        args["args"],
        cwd=r'{}'.format(args["data_dir"]),
        preexec_fn=os.setpgrp)

    return CreateWalletSuccess(wallet=wallet)
