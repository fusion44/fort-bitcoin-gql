import subprocess

import psutil
import pytest
from mixer.backend.django import mixer

import backend.lnd.utils as utils
from backend.lnd.models import LNDWallet
from backend.test_utils.utils import fake_lnd_wallet_config, raise_error

pytestmark = pytest.mark.django_db


def test_lnd_startup_args(monkeypatch):
    wallet = LNDWallet()
    wallet.testnet = True
    wallet.initialized = True
    wallet.owner = mixer.blend("auth.User")
    wallet.save()

    config = {
        "DEFAULT": {
            "lnd_data_path": "/test/1234",
            "bitcoin_node": "wrong",
        },
    }

    monkeypatch.setattr(utils, "CONFIG", config)

    with pytest.raises(ValueError):
        args = utils.build_lnd_startup_args(False, wallet)

    config["DEFAULT"]["bitcoin_node"] = "btcd"
    monkeypatch.setattr(utils, "CONFIG", config)

    args = utils.build_lnd_startup_args(False, wallet)
    assert args["args"]
    assert "--datadir={}".format(
        args["data_dir"]
    ) in args["args"], "Should contain the correct data dir path"
    assert "--bitcoin.node=btcd" in args[
        "args"], "Should contain the args for BTCD"
    assert "--autopilot.active" not in args[
        "args"], "Should not contain the autopilot args"
    assert "--bitcoin.testnet" in args[
        "args"], "Should contain the bitcoin testnet argument"

    config["DEFAULT"]["bitcoin_node"] = "bitcoind"
    monkeypatch.setattr(utils, "CONFIG", config)

    wallet.testnet = False
    wallet.save()
    args = utils.build_lnd_startup_args(True, wallet)
    assert "--bitcoin.node=bitcoind" in args[
        "args"], "Should contain the args for Bitcoin Core"
    assert "--autopilot.active" in args[
        "args"], "Should contain the autopilot args"
    assert "--bitcoin.mainnet" in args[
        "args"], "Should contain the bitcoin mainnet argument"


def test_lnd_instance_is_running(monkeypatch):
    cfg = fake_lnd_wallet_config()
    # Pretend that no running process can be found
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: raise_error(
                          subprocess.CalledProcessError(1, "check_output")))
    ret = utils.lnd_instance_is_running(cfg)
    assert ret is False, "Should return False because no process is running"

    # Some other error happended and command return code is not 0 or 1
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: raise_error(
                          subprocess.CalledProcessError(2, "check_output")))
    with pytest.raises(RuntimeError):
        ret = utils.lnd_instance_is_running(cfg)

    # Pretend that one process is running using this data dir
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: b"601\n")
    monkeypatch.setattr(psutil, "pid_exists", lambda *args, **kwargs: True)

    ret = utils.lnd_instance_is_running(cfg)
    assert ret is True, "Should return True because one process is running"

    # Pretend that more than one lnd process is found with the given data dir
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: b"601\n602\n603\n")

    with pytest.raises(RuntimeError):
        ret = utils.lnd_instance_is_running(cfg)
