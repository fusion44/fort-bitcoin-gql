import subprocess

import psutil
import pytest

from backend.lnd.utils import lnd_instance_is_running
from backend.test_utils.utils import fake_lnd_wallet_config, raise_error


def test_lnd_instance_is_running(monkeypatch):
    cfg = fake_lnd_wallet_config()
    # Pretend that no running process can be found
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: raise_error(
                          subprocess.CalledProcessError(1, "check_output")))
    ret = lnd_instance_is_running(cfg)
    assert ret is False, "Should return False because no process is running"

    # Some other error happended and command return code is not 0 or 1
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: raise_error(
                          subprocess.CalledProcessError(2, "check_output")))
    with pytest.raises(RuntimeError):
        ret = lnd_instance_is_running(cfg)

    # Pretend that one process is running using this data dir
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: b"601\n")
    monkeypatch.setattr(psutil, "pid_exists", lambda *args, **kwargs: True)

    ret = lnd_instance_is_running(cfg)
    assert ret is True, "Should return True because one process is running"

    # Pretend that more than one lnd process is found with the given data dir
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: b"601\n602\n603\n")

    with pytest.raises(RuntimeError):
        ret = lnd_instance_is_running(cfg)
