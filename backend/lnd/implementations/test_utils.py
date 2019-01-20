"""Contains all utility functions for testing"""

import backend.lnd.utils as lnd_utils


def fake_build_wallet_cfg(pk):
    """Fakes the build wallet config function"""
    path = "/fake/path/" + str(pk)

    default_listen_port = 19739
    default_rpc_port = 12009
    default_rest_port = 8079

    return lnd_utils.LNDWalletConfig(
        data_dir=path,
        tls_cert_path=path + "/tls.cert",
        tls_key_path=path + "/tls.key",
        admin_macaroon_path=path + "/admin.macaroon",
        read_only_macaroon_path=path + "/readonly.macaroon",
        log_dir=path + "/logs",
        listen_port_ipv6=default_listen_port + pk * 2,
        listen_port_ipv4=default_listen_port + pk * 2 - 1,
        rpc_listen_port_ipv6=default_rpc_port + pk * 2,
        rpc_listen_port_ipv4=default_rpc_port + pk * 2 - 1,
        rest_port_ipv6=default_rest_port + pk * 2,
        rest_port_ipv4=default_rest_port + pk * 2 - 1)
