import subprocess

import psutil
import pytest
from mixer.backend.django import mixer

import backend.lnd.utils as utils
from backend.lnd.models import IPAddress, LNDWallet
from backend.test_utils.utils import fake_lnd_wallet_config, raise_error

pytestmark = pytest.mark.django_db


def test_lnd_startup_args(monkeypatch):
    address = IPAddress()
    address.ip_address = "1.1.1.1"
    address.save()

    wallet = LNDWallet()
    wallet.testnet = True
    wallet.initialized = True
    wallet.owner = mixer.blend("auth.User")
    wallet.save()

    config = {
        "DEFAULT": {
            "bitcoin_node": "btcd",
            "network": "mainnet",
            "lnd_data_path": "/test/1234",
        },
        "BTCD_MAINNET": {
            "btc_rpc_username": "btcdmainnet",
            "btc_rpc_password": "123",
            "btc_rpc_host": "0.0.0.0",
            "btc_rpc_port": "0000",
        },
        "BTCD_TESTNET": {
            "btc_rpc_username": "btcdtestnet",
            "btc_rpc_password": "234",
            "btc_rpc_host": "1.1.1.1",
            "btc_rpc_port": "1111",
        },
        "BITCOIND_MAINNET": {
            "btc_rpc_use_https": "false",
            "btc_rpc_username": "bitcoindmainnet",
            "btc_rpc_password": "345",
            "btc_rpc_host": "2.2.2.2",
            "btc_rpc_port": "2222",
            "btc_zmqpubrawblock": "tcp://127.0.0.1:39000main",
            "btc_zmqpubrawtx": "tcp://127.0.0.1:39000main",
        },
        "BITCOIND_TESTNET": {
            "btc_rpc_use_https": "false",
            "btc_rpc_username": "bitcoindtestnet",
            "btc_rpc_password": "456",
            "btc_rpc_host": "3.3.3.3",
            "btc_rpc_port": "3333",
            "btc_zmqpubrawblock": "tcp://127.0.0.1:39000test",
            "btc_zmqpubrawtx": "tcp://127.0.0.1:39000test",
        },
    }

    monkeypatch.setattr(utils, "CONFIG", config)

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
    assert "--externalip={}:19740".format(
        address.ip_address) in args["args"], (
            "Should contain the external ip address")


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


def test_get_node_config(monkeypatch):
    config = {
        "DEFAULT": {
            "bitcoin_node": "btcd_fail",
            "network": "mainnet_fail",
            "lnd_data_path": "/test/1234",
        },
        "BTCD_MAINNET": {
            "btc_rpc_username": "btcdmainnet",
            "btc_rpc_password": "123",
            "btc_rpc_host": "0.0.0.0",
            "btc_rpc_port": "0000",
        },
        "BTCD_TESTNET": {
            "btc_rpc_username": "btcdtestnet",
            "btc_rpc_password": "234",
            "btc_rpc_host": "1.1.1.1",
            "btc_rpc_port": "1111",
        },
        "BITCOIND_MAINNET": {
            "btc_rpc_use_https": "false",
            "btc_rpc_username": "bitcoindmainnet",
            "btc_rpc_password": "345",
            "btc_rpc_host": "2.2.2.2",
            "btc_rpc_port": "2222",
            "btc_zmqpubrawblock": "tcp://127.0.0.1:39000main",
            "btc_zmqpubrawtx": "tcp://127.0.0.1:39000main",
        },
        "BITCOIND_TESTNET": {
            "btc_rpc_use_https": "false",
            "btc_rpc_username": "bitcoindtestnet",
            "btc_rpc_password": "456",
            "btc_rpc_host": "3.3.3.3",
            "btc_rpc_port": "3333",
            "btc_zmqpubrawblock": "tcp://127.0.0.1:39000test",
            "btc_zmqpubrawtx": "tcp://127.0.0.1:39000test",
        },
    }

    monkeypatch.setattr(utils, "CONFIG", config)

    with pytest.raises(ValueError):
        utils.get_node_config()
    config["DEFAULT"]["network"] = "mainnet"

    with pytest.raises(ValueError):
        utils.get_node_config()
    config["DEFAULT"]["bitcoin_node"] = "btcd"

    # test mainnet with btcd
    cfg = utils.get_node_config()
    assert cfg.bitcoin_node == "btcd", "Node should be btcd"
    assert cfg.network == "mainnet", "Network should be mainnet"
    assert cfg.rpc_username == "btcdmainnet", "Mainnet btcd username should be btcdmainnet"
    assert cfg.rpc_password == "123", "Mainnet btcd RPC password should be 123"
    assert cfg.rpc_host == "0.0.0.0", "Mainnet btcd RPC host should be 0.0.0.0"
    assert cfg.rpc_port == "0000", "Mainnet btcd RPC host should be 0000"

    # test testnet with btcd
    config["DEFAULT"]["network"] = "testnet"
    cfg = utils.get_node_config()
    assert cfg.network == "testnet", "Network should be testnet"
    assert cfg.rpc_username == "btcdtestnet", "Testnet btcd username should be btcdtestnet"
    assert cfg.rpc_password == "234", "Testnet btcd RPC password should be 234"
    assert cfg.rpc_host == "1.1.1.1", "Testnet btcd RPC host should be 1.1.1.1"
    assert cfg.rpc_port == "1111", "Testnet btcd RPC host should be 1111"

    # test mainnet with bitcoind (core)
    config["DEFAULT"]["bitcoin_node"] = "bitcoind"
    config["DEFAULT"]["network"] = "mainnet"
    cfg = utils.get_node_config()
    assert cfg.bitcoin_node == "bitcoind", "Node should be bitcoind"
    assert cfg.network == "mainnet", "Network should be mainnet"
    assert cfg.rpc_username == "bitcoindmainnet", "Mainnet core username should be bitcoindmainnet"
    assert cfg.rpc_password == "345", "Mainnet core RPC password should be 345"
    assert cfg.rpc_host == "2.2.2.2", "Mainnet core RPC host should be 2.2.2.2"
    assert cfg.rpc_port == "2222", "Mainnet core RPC host should be 2222"
    assert cfg.bitcoind_rpc_use_https == "false", "Should not use https"
    assert cfg.bitcoind_zmqpubrawblock == "tcp://127.0.0.1:39000main"
    assert cfg.bitcoind_zmqpubrawtx == "tcp://127.0.0.1:39000main"

    # test testnet with bitcoind (core)
    config["DEFAULT"]["network"] = "testnet"
    cfg = utils.get_node_config()
    assert cfg.bitcoin_node == "bitcoind", "Node should be bitcoind"
    assert cfg.network == "testnet", "Network should be testnet"
    assert cfg.rpc_username == "bitcoindtestnet", "Testnet core username should be bitcoindtestnet"
    assert cfg.rpc_password == "456", "Testnet core RPC password should be 456"
    assert cfg.rpc_host == "3.3.3.3", "Testnet core RPC host should be 3.3.3.3"
    assert cfg.rpc_port == "3333", "Testnet core RPC host should be 3333"
    assert cfg.bitcoind_rpc_use_https == "false", "Should not use https"
    assert cfg.bitcoind_zmqpubrawblock == "tcp://127.0.0.1:39000test"
    assert cfg.bitcoind_zmqpubrawtx == "tcp://127.0.0.1:39000test"


def fake_open_channel(rpc_server, rpc_port, cert_path, macaroon_path,
                      is_async):
    # avoid building a real channel
    return utils.ChannelData(
        channel="Channel with {}".format(rpc_server),
        macaroon="Macaroon",
        error=None)


def test_channel_cache_class(monkeypatch):
    cache = utils.ChannelCache()
    monkeypatch.setattr(cache, "_open_channel", fake_open_channel)
    channel_data = cache.get("1.1.1.1", "1337", "/some/macaroon",
                             "/another/path", False, False)
    assert channel_data.channel == "Channel with 1.1.1.1", "Should return the correct channel"

    # patch the cache so we can test if we really receive
    # a cached channel instead of a newly created channel
    monkeypatch.setattr(
        cache,
        "_cache",
        {
            list(cache._cache.keys())[0]:
            utils.ChannelData(
                channel="Channel with 1.1.1.1 patched",
                macaroon="Macaroon",
                error=None)
        },
    )

    channel_data = cache.get("1.1.1.1", "1337", "/some/macaroon",
                             "/another/path", False, False)
    assert channel_data.channel == "Channel with 1.1.1.1 patched", \
        "Should return the channel from cache which was patched"
