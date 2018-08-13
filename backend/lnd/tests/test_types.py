"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import backend.lnd.types as types
from faker import Faker
fake = Faker()

# pylint: skip-file


def make_fake_ln_hop_type():
    return {
        "chan_id": fake.pystr(),
        "chan_capacity": fake.pyint(),
        "amt_to_forward": fake.pyint(),
        "fee": fake.pyint(),
        "expiry": fake.unix_time(),
        "amt_to_forward_msat": fake.pyint(),
        "fee_msat": fake.pyint(),
    }


def test_ln_fee_limit_type():
    inst = types.LnFeeLimit()
    assert inst


def test_ln_hop_type():
    fake_hop = make_fake_ln_hop_type()
    inst = types.LnHop(fake_hop)
    assert inst
    assert inst.chan_id == fake_hop['chan_id']
    assert inst.chan_capacity == fake_hop['chan_capacity']
    assert inst.amt_to_forward == fake_hop['amt_to_forward']
    assert inst.fee == fake_hop['fee']
    assert inst.expiry == fake_hop['expiry']
    assert inst.amt_to_forward_msat == fake_hop['amt_to_forward_msat']
    assert inst.fee_msat == fake_hop['fee_msat']


def test_ln_hop_hint():
    hop_hint = {
        "node_id": fake.pystr(),
        "chan_id": fake.pyint(),
        "fee_base_msat": fake.pyint(),
        "fee_proportional_millionths": fake.pyint(),
        "cltv_expiry_delta": fake.pyint()
    }
    inst = types.LnHopHint(hop_hint)
    assert inst
    assert inst.node_id == hop_hint["node_id"]
    assert inst.chan_id == hop_hint["chan_id"]
    assert inst.fee_base_msat == hop_hint["fee_base_msat"]
    assert inst.fee_proportional_millionths == hop_hint[
        "fee_proportional_millionths"]
    assert inst.cltv_expiry_delta == hop_hint["cltv_expiry_delta"]


def test_ln_info_type():
    info = {
        "identity_pubkey": fake.sha256(),
        "alias": fake.name(),
        "num_pending_channels": fake.pyint(),
        "num_active_channels": fake.pyint(),
        "num_peers": fake.pyint(),
        "block_height": 155000,
        "block_hash": fake.sha256(),
        "synced_to_chain": fake.pybool(),
        "testnet": fake.pybool(),
        "chains": ["BTC", "LTC"],
        "uris": ["uri1", "uri2"],
        "best_header_timestamp": fake.unix_time(),
        "version": fake.pystr()
    }
    inst = types.LnInfoType(info)
    assert inst
    assert inst.identity_pubkey == info["identity_pubkey"]
    assert inst.alias == info["alias"]
    assert inst.num_pending_channels == info["num_pending_channels"]
    assert inst.num_active_channels == info["num_active_channels"]
    assert inst.num_peers == info["num_peers"]
    assert inst.block_height == info["block_height"]
    assert inst.block_hash == info["block_hash"]
    assert inst.synced_to_chain == info["synced_to_chain"]
    assert inst.testnet == info["testnet"]
    assert len(inst.chains) == len(info["chains"])
    assert inst.chains[0] == info["chains"][0]
    assert inst.chains[1] == info["chains"][1]
    assert len(inst.uris) == len(info["uris"])
    assert inst.uris[0] == info["uris"][0]
    assert inst.uris[1] == info["uris"][1]
    assert inst.best_header_timestamp == info["best_header_timestamp"]
    assert inst.version == info["version"]


def test_pay_req_type():
    hop_hint_a = types.LnHopHint({
        "node_id": fake.pystr(),
        "chan_id": fake.pyint(),
        "fee_base_msat": fake.pyint(),
        "fee_proportional_millionths": fake.pyint(),
        "cltv_expiry_delta": fake.pyint()
    })

    hop_hint_b = types.LnHopHint({
        "node_id": fake.pystr(),
        "chan_id": fake.pyint(),
        "fee_base_msat": fake.pyint(),
        "fee_proportional_millionths": fake.pyint(),
        "cltv_expiry_delta": fake.pyint()
    })
    fake_pay_req = {
        "destination": fake.pystr(),
        "payment_hash": fake.sha256(),
        "num_satoshis": fake.pyint(),
        "timestamp": fake.unix_time(),
        "expiry": fake.pyint(),
        "description": fake.pystr(),
        "description_hash": fake.sha256(),
        "fallback_addr": fake.pystr(),
        "cltv_expiry": fake.pyint(),
        "route_hints": [hop_hint_a, hop_hint_b]
    }
    inst = types.LnPayReqType(fake_pay_req)
    assert inst
    assert inst.destination == fake_pay_req['destination']
    assert inst.payment_hash == fake_pay_req['payment_hash']
    assert inst.num_satoshis == fake_pay_req['num_satoshis']
    assert inst.timestamp == fake_pay_req['timestamp']
    assert inst.expiry == fake_pay_req['expiry']
    assert inst.description == fake_pay_req['description']
    assert inst.description_hash == fake_pay_req['description_hash']
    assert inst.fallback_addr == fake_pay_req['fallback_addr']
    assert inst.cltv_expiry == fake_pay_req['cltv_expiry']
    assert inst.route_hints == fake_pay_req['route_hints']


def test_ln_raw_payment_input():
    inst = types.LnRawPaymentInput()
    assert inst


def test_ln_route():
    route = {
        "total_time_lock": fake.pyint(),
        "total_fees": fake.pyint(),
        "total_amt": fake.pyint(),
        "hops": [make_fake_ln_hop_type(),
                 make_fake_ln_hop_type()],
        "total_fees_msat": fake.pyint(),
        "total_amt_msat": fake.pyint()
    }
    inst = types.LnRoute(route)
    assert inst
    assert inst.total_time_lock == route["total_time_lock"]
    assert inst.total_fees == route["total_fees"]
    assert inst.total_amt == route["total_amt"]
    assert len(inst.hops) == 2
    assert inst.total_fees_msat == route["total_fees_msat"]
    assert inst.total_amt_msat == route["total_amt_msat"]


def test_ln_route_hint():
    inst = types.LnRouteHint()
    assert inst