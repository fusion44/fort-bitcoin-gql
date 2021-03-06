"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

import backend.lnd.types as types
from faker import Faker
fake = Faker()

# pylint: skip-file


def make_fake_htlcs():
    return [
        {
            "incoming": True,
            "amount": 13235425345,
            "hash_lock": fake.sha256(),
            "expiration_height": 525243,
        },
        {
            "incoming": False,
            "amount": 2252,
            "hash_lock": fake.sha256(),
            "expiration_height": 525246,
        },
    ]


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


def test_ln_channel_balance():
    inst = types.LnChannelBalance({"balance": 1, "pending_open_balance": 2})
    assert inst
    inst.balance == 1
    inst.pending_open_balance == 2


def test_ln_wallet_balance():
    inst = types.LnWalletBalance({
        "total_balance": 1,
        "confirmed_balance": 2,
        "unconfirmed_balance": 3
    })
    assert inst
    assert inst.total_balance == 1
    assert inst.confirmed_balance == 2
    assert inst.unconfirmed_balance == 3


def test_ln_transaction():
    fake_transaction = {
        'amount': fake.pyint(),
        'block_hash': fake.sha256(),
        'block_height': fake.pyint(),
        'dest_addresses': [fake.sha256(), fake.sha256()],
        'num_confirmations': fake.pyint(),
        'time_stamp': fake.unix_time(),
        'tx_hash': fake.sha256()
    }
    inst = types.LnTransaction(fake_transaction)

    assert inst
    assert inst.amount == fake_transaction["amount"]
    assert inst.block_hash == fake_transaction["block_hash"]
    assert inst.block_height == fake_transaction["block_height"]
    assert len(inst.dest_addresses) == len(fake_transaction["dest_addresses"])
    assert inst.dest_addresses[0] == fake_transaction["dest_addresses"][0]
    assert inst.dest_addresses[1] == fake_transaction["dest_addresses"][1]
    assert inst.num_confirmations == fake_transaction["num_confirmations"]
    assert inst.time_stamp == fake_transaction["time_stamp"]
    assert inst.tx_hash == fake_transaction["tx_hash"]


def test_ln_transaction_details():
    fake_transactions = [
        {
            'amount': fake.pyint(),
            'block_hash': fake.sha256(),
            'block_height': fake.pyint(),
            'dest_addresses': [fake.sha256(), fake.sha256()],
            'num_confirmations': fake.pyint(),
            'time_stamp': fake.unix_time(),
            'tx_hash': fake.sha256()
        },
        {
            'amount': fake.pyint(),
            'block_hash': fake.sha256(),
            'block_height': fake.pyint(),
            'dest_addresses': [fake.sha256(), fake.sha256()],
            'num_confirmations': fake.pyint(),
            'time_stamp': fake.unix_time(),
            'tx_hash': fake.sha256()
        },
    ]
    inst = types.LnTransactionDetails({'transactions': fake_transactions})

    assert inst
    assert len(inst.transactions) == 2


def test_ln_invoice():
    hop_hints = [
        {
            "node_id": fake.pystr(),
            "chan_id": fake.pyint(),
            "fee_base_msat": fake.pyint(),
            "fee_proportional_millionths": fake.pyint(),
            "cltv_expiry_delta": fake.pyint()
        },
        {
            "node_id": fake.pystr(),
            "chan_id": fake.pyint(),
            "fee_base_msat": fake.pyint(),
            "fee_proportional_millionths": fake.pyint(),
            "cltv_expiry_delta": fake.pyint()
        },
    ]
    invoice = {
        "memo": fake.pystr(),
        "receipt": fake.sha256(),
        "r_preimage": fake.sha256(),
        "r_hash": fake.sha256(),
        "value": fake.pyint(),
        "settled": fake.pybool(),
        "creation_date": fake.unix_time(),
        "settle_date": fake.unix_time(),
        "payment_request": fake.pystr(),
        "description_hash": fake.pystr(),
        "expiry": fake.unix_time(),
        "fallback_addr": fake.pystr(),
        "cltv_expiry": fake.unix_time(),
        "route_hints": hop_hints,
        "private": fake.pybool(),
        "add_index": fake.pyint(),
        "settle_index": fake.pyint(),
        "amt_paid": fake.pyint(),
    }
    inst = types.LnInvoice(invoice)
    assert inst
    assert inst.memo == invoice["memo"]
    assert inst.receipt == invoice["receipt"]
    assert inst.r_preimage == invoice["r_preimage"]
    assert inst.r_hash == invoice["r_hash"]
    assert inst.value == invoice["value"]
    assert inst.settled == invoice["settled"]
    assert inst.creation_date == invoice["creation_date"]
    assert inst.settle_date == invoice["settle_date"]
    assert inst.payment_request == invoice["payment_request"]
    assert inst.description_hash == invoice["description_hash"]
    assert inst.expiry == invoice["expiry"]
    assert inst.fallback_addr == invoice["fallback_addr"]
    assert inst.cltv_expiry == invoice["cltv_expiry"]
    assert len(inst.route_hints) == 2
    assert inst.private == invoice["private"]
    assert inst.add_index == invoice["add_index"]
    assert inst.settle_index == invoice["settle_index"]
    assert inst.amt_paid == invoice["amt_paid"]


def test_ln_payment():
    payment = {
        "payment_hash": fake.sha256(),
        "value": fake.pyint(),
        "creation_date": fake.unix_time(),
        "path": [fake.sha256(), fake.sha256()],
        "fee": fake.pyint(),
        "payment_preimage": fake.sha256()
    }

    inst = types.LnPayment(payment)

    assert inst
    assert inst.payment_hash == payment["payment_hash"]
    assert inst.value == payment["value"]
    assert inst.creation_date == payment["creation_date"]
    assert len(inst.path) == len(payment["path"])
    assert inst.path[0] == payment["path"][0]
    assert inst.path[1] == payment["path"][1]
    assert inst.fee == payment["fee"]
    assert inst.payment_preimage == payment["payment_preimage"]


def test_ln_payment_response():
    fake_payments = [
        {
            "payment_hash": fake.sha256(),
            "value": fake.pyint(),
            "creation_date": fake.unix_time(),
            "path": [fake.sha256(), fake.sha256()],
            "fee": fake.pyint(),
            "payment_preimage": fake.sha256()
        },
        {
            "payment_hash": fake.sha256(),
            "value": fake.pyint(),
            "creation_date": fake.unix_time(),
            "path": [fake.sha256(), fake.sha256()],
            "fee": fake.pyint(),
            "payment_preimage": fake.sha256()
        },
    ]

    inst = types.LnListPaymentsResponse({'payments': fake_payments})

    assert inst
    assert len(inst.payments) == 2


def test_ln_htlc():
    fakehtlcs = make_fake_htlcs()
    inst = types.LnHTLC(fakehtlcs[0])

    assert inst
    assert inst.incoming == fakehtlcs[0]["incoming"]
    assert inst.amount == fakehtlcs[0]["amount"]
    assert inst.hash_lock == fakehtlcs[0]["hash_lock"]
    assert inst.expiration_height == fakehtlcs[0]["expiration_height"]

    inst = types.LnHTLC(fakehtlcs[1])

    assert inst
    assert inst.incoming == fakehtlcs[1]["incoming"]
    assert inst.amount == fakehtlcs[1]["amount"]
    assert inst.hash_lock == fakehtlcs[1]["hash_lock"]
    assert inst.expiration_height == fakehtlcs[1]["expiration_height"]


def test_ln_channel():
    fake_channels = [
        {
            "active": True,
            "remote_pubkey": fake.sha256(),
            "channel_point": fake.sha256(),
            "chan_id": "1578842622393712641",
            "capacity": 5708945,
            "local_balance": 5708480,
            "remote_balance": 0,
            "commit_fee": 465,
            "commit_weight": 600,
            "fee_per_kw": 643,
            "unsettled_balance": 0,
            "total_satoshis_sent": 0,
            "total_satoshis_received": 0,
            "num_updates": 15,
            "csv_delay": 686,
            "private": False,
            "pending_htlcs": make_fake_htlcs()
        },
        {
            "active": True,
            "remote_pubkey": fake.sha256(),
            "channel_point": fake.sha256(),
            "chan_id": "1554865572332175360",
            "capacity": 16777215,
            "local_balance": 16776676,
            "remote_balance": 0,
            "commit_fee": 539,
            "commit_weight": 600,
            "fee_per_kw": 745,
            "unsettled_balance": 0,
            "total_satoshis_sent": 0,
            "total_satoshis_received": 0,
            "num_updates": 47,
            "csv_delay": 2016,
            "private": True,
            "pending_htlcs": make_fake_htlcs()
        },
    ]
    inst = types.LnChannel(fake_channels[1])
    assert inst
    assert inst.active == fake_channels[1]["active"]
    assert inst.remote_pubkey == fake_channels[1]["remote_pubkey"]
    assert inst.channel_point == fake_channels[1]["channel_point"]
    assert inst.chan_id == fake_channels[1]["chan_id"]
    assert inst.capacity == fake_channels[1]["capacity"]
    assert inst.local_balance == fake_channels[1]["local_balance"]
    assert inst.remote_balance == fake_channels[1]["remote_balance"]
    assert inst.commit_fee == fake_channels[1]["commit_fee"]
    assert inst.commit_weight == fake_channels[1]["commit_weight"]
    assert inst.fee_per_kw == fake_channels[1]["fee_per_kw"]
    assert inst.unsettled_balance == fake_channels[1]["unsettled_balance"]
    assert inst.total_satoshis_sent == fake_channels[1]["total_satoshis_sent"]
    assert inst.total_satoshis_received == fake_channels[1][
        "total_satoshis_received"]
    assert inst.num_updates == fake_channels[1]["num_updates"]
    assert len(inst.pending_htlcs) == len(fake_channels[1]["pending_htlcs"])
    assert inst.csv_delay == fake_channels[1]["csv_delay"]
    assert inst.private == fake_channels[1]["private"]


def test_ln_peer():
    fake_peers = [
        {
            "pub_key": fake.sha256(),
            "address": "1.2.3.4:19735",
            "bytes_sent": "80021",
            "bytes_recv": "165970",
            "sat_sent": "0",
            "sat_recv": "0",
            "inbound": False,
            "ping_time": "65354"
        },
        {
            "pub_key": fake.sha256(),
            "address": "11.12.13.14:19735",
            "bytes_sent": "92681",
            "bytes_recv": "75375",
            "sat_sent": "0",
            "sat_recv": "0",
            "inbound": False,
            "ping_time": "65645"
        },
    ]

    inst = types.LnPeer(fake_peers[1])
    assert inst
    assert inst.pub_key == fake_peers[1]["pub_key"]
    assert inst.address == fake_peers[1]["address"]
    assert inst.bytes_sent == fake_peers[1]["bytes_sent"]
    assert inst.bytes_recv == fake_peers[1]["bytes_recv"]
    assert inst.sat_sent == fake_peers[1]["sat_sent"]
    assert inst.sat_recv == fake_peers[1]["sat_recv"]
    assert inst.inbound == fake_peers[1]["inbound"]
    assert inst.ping_time == fake_peers[1]["ping_time"]
