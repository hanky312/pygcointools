import json
import os
import random
import unittest

import gcoin.ripemd as ripemd
from gcoin import *


class TestECCArithmetic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('Starting ECC arithmetic tests')

    def test_all(self):
        for i in range(8):
            print('### Round %d' % (i+1))
            x, y = random.randrange(2**256), random.randrange(2**256)
            self.assertEqual(
                multiply(multiply(G, x), y)[0],
                multiply(multiply(G, y), x)[0]
            )
            self.assertEqual(

                add_pubkeys(multiply(G, x), multiply(G, y))[0],
                multiply(G, add_privkeys(x, y))[0]
            )

            hx, hy = encode(x % N, 16, 64), encode(y % N, 16, 64)
            self.assertEqual(
                multiply(multiply(G, hx), hy)[0],
                multiply(multiply(G, hy), hx)[0]
            )
            self.assertEqual(
                add_pubkeys(multiply(G, hx), multiply(G, hy))[0],
                multiply(G, add_privkeys(hx, hy))[0]
            )
            self.assertEqual(
                b58check_to_hex(pubtoaddr(privtopub(x))),
                b58check_to_hex(pubtoaddr(multiply(G, hx), 23))
            )

            p = privtopub(sha256(str(x)))
            if i % 2 == 1:
                p = changebase(p, 16, 256)
            self.assertEqual(p, decompress(compress(p)))
            self.assertEqual(G[0], multiply(divide(G, x), x)[0])


class TestBases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('Starting base change tests')

    def test_all(self):
        data = [
            [10, '65535', 16, 'ffff'],
            [16, 'deadbeef', 10, '3735928559'],
            [10, '0', 16, ''],
            [256, b'34567', 10, '219919234615'],
            [10, '444', 16, '1bc'],
            [256, b'\x03\x04\x05\x06\x07', 10, '12952339975'],
            [16, '3132333435', 256, b'12345']
        ]
        for prebase, preval, postbase, postval in data:
            self.assertEqual(changebase(preval, prebase, postbase), postval)

        for i in range(100):
            x = random.randrange(1, 9999999999999999)
            frm = random.choice([2, 10, 16, 58, 256])
            to = random.choice([2, 10, 16, 58, 256])
            self.assertEqual(decode(encode(x, to), to), x)
            self.assertEqual(changebase(encode(x, frm), frm, to), encode(x, to))
            self.assertEqual(decode(changebase(encode(x, frm), frm, to), to), x)


class TestRawSignRecover(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Basic signing and recovery tests")

    def test_all(self):
        for i in range(20):
            k = sha256(str(i))
            s = ecdsa_raw_sign('35' * 32, k)
            self.assertEqual(
                ecdsa_raw_recover('35' * 32, s),
                decode_pubkey(privtopub(k))
            )


class TestTransactionSignVerify(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Transaction-style signing and verification tests")

    def test_all(self):
        alphabet = "1234567890qwertyuiopasdfghjklzxcvbnm"
        for i in range(10):
            msg = ''.join([random.choice(alphabet) for i in range(random.randrange(20, 200))])
            priv = sha256(str(random.randrange(2**256)))
            pub = privtopub(priv)
            sig = ecdsa_tx_sign(msg, priv)
            self.assertTrue(
                ecdsa_tx_verify(msg, sig, pub),
                "Verification error"
            )

            self.assertIn(
                pub,
                ecdsa_tx_recover(msg, sig),
                "Recovery failed"
            )


class TestSerialize(unittest.TestCase):

    def test_serialize(self):
        tx = '0100000001239f932c780e517015842f3b02ff765fba97f9f63f9f1bc718b686a56ed9c73400000000fd5d010047304402200c40fa58d3f6d5537a343cf9c8d13bc7470baf1d13867e0de3e535cd6b4354c802200f2b48f67494835b060d0b2ff85657d2ba2d9ea4e697888c8cb580e8658183a801483045022056f488c59849a4259e7cef70fe5d6d53a4bd1c59a195b0577bd81cb76044beca022100a735b319fa66af7b178fc719b93f905961ef4d4446deca8757a90de2106dd98a014cc95241046c7d87fd72caeab48e937f2feca9e9a4bd77f0eff4ebb2dbbb9855c023e334e188d32aaec4632ea4cbc575c037d8101aec73d029236e7b1c2380f3e4ad7edced41046fd41cddf3bbda33a240b417a825cc46555949917c7ccf64c59f42fd8dfe95f34fae3b09ed279c8c5b3530510e8cca6230791102eef9961d895e8db54af0563c410488d618b988efd2511fc1f9c03f11c210808852b07fe46128c1a6b1155aa22cdf4b6802460ba593db2d11c7e6cbe19cedef76b7bcabd05d26fd97f4c5a59b225053aeffffffff0310270000000000001976a914a89733100315c37d228a529853af341a9d290a4588ac409c00000000000017a9142b56f9a4009d9ff99b8f97bea4455cd71135f5dd87409c00000000000017a9142b56f9a4009d9ff99b8f97bea4455cd71135f5dd8700000000'
        self.assertEqual(
            serialize(deserialize(tx)),
            tx,
            "Serialize roundtrip failed"
        )

    def test_serialize_script(self):
        script = '47304402200c40fa58d3f6d5537a343cf9c8d13bc7470baf1d13867e0de3e535cd6b4354c802200f2b48f67494835b060d0b2ff85657d2ba2d9ea4e697888c8cb580e8658183a801483045022056f488c59849a4259e7cef70fe5d6d53a4bd1c59a195b0577bd81cb76044beca022100a735b319fa66af7b178fc719b93f905961ef4d4446deca8757a90de2106dd98a014cc95241046c7d87fd72caeab48e937f2feca9e9a4bd77f0eff4ebb2dbbb9855c023e334e188d32aaec4632ea4cbc575c037d8101aec73d029236e7b1c2380f3e4ad7edced41046fd41cddf3bbda33a240b417a825cc46555949917c7ccf64c59f42fd8dfe95f34fae3b09ed279c8c5b3530510e8cca6230791102eef9961d895e8db54af0563c410488d618b988efd2511fc1f9c03f11c210808852b07fe46128c1a6b1155aa22cdf4b6802460ba593db2d11c7e6cbe19cedef76b7bcabd05d26fd97f4c5a59b225053ae'
        self.assertEqual(
            serialize_script(deserialize_script(script)),
            script,
            "Script serialize roundtrip failed"
        )


class TestTransaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Attempting transaction creation")

    # FIXME: I don't know how to write this as a unit test.
    # What should be asserted?
    def test_all(self):
        privs = [sha256(str(random.randrange(2**256))) for x in range(4)]
        pubs = [privtopub(priv) for priv in privs]
        addresses = [pubtoaddr(pub) for pub in pubs]
        mscript = mk_multisig_script(pubs[1:], 2, 3)
        msigaddr = p2sh_scriptaddr(mscript)
        tx = mktx(['01'*32+':1', '23'*32+':2'], [msigaddr+':20202', addresses[0]+':40404'])
        tx1 = sign(tx, 1, privs[0])

        sig1 = multisign(tx, 0, mscript, privs[1])
        self.assertTrue(verify_tx_input(tx1, 0, mscript, sig1, pubs[1]), "Verification Error")

        sig3 = multisign(tx, 0, mscript, privs[3])
        self.assertTrue(verify_tx_input(tx1, 0, mscript, sig3, pubs[3]), "Verification Error")

        tx2 = apply_multisignatures(tx1, 0, mscript, [sig1, sig3])
        print("Outputting transaction: ", tx2)

    # https://github.com/vbuterin/pybitcointools/issues/71
    def test_multisig(self):
        script = mk_multisig_script(["0254236f7d1124fc07600ad3eec5ac47393bf963fbf0608bcce255e685580d16d9",
                                     "03560cad89031c412ad8619398bd43b3d673cb5bdcdac1afc46449382c6a8e0b2b"],
                                     2)

        self.assertEqual(p2sh_scriptaddr(script), "33byJBaS5N45RHFcatTSt9ZjiGb6nK4iV3")

        self.assertEqual(p2sh_scriptaddr(script, 0x05), "33byJBaS5N45RHFcatTSt9ZjiGb6nK4iV3")
        self.assertEqual(p2sh_scriptaddr(script, 5), "33byJBaS5N45RHFcatTSt9ZjiGb6nK4iV3")

        self.assertEqual(p2sh_scriptaddr(script, 0xc4), "2MuABMvWTgpZRd4tAG25KW6YzvcoGVZDZYP")
        self.assertEqual(p2sh_scriptaddr(script, 196), "2MuABMvWTgpZRd4tAG25KW6YzvcoGVZDZYP")


class TestDeterministicGenerate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Beginning RFC6979 deterministic signing tests")

    def test_all(self):
        # Created with python-ecdsa 0.9
        # Code to make your own vectors:
        # class gen:
        #     def order(self): return 115792089237316195423570985008687907852837564279074904382605163141518161494337
        # dummy = gen()
        # for i in range(10): ecdsa.rfc6979.generate_k(dummy, i, hashlib.sha256, hashlib.sha256(str(i)).digest())
        test_vectors = [
            32783320859482229023646250050688645858316445811207841524283044428614360139869,
            109592113955144883013243055602231029997040992035200230706187150761552110229971,
            65765393578006003630736298397268097590176526363988568884298609868706232621488,
            85563144787585457107933685459469453513056530050186673491900346620874099325918,
            99829559501561741463404068005537785834525504175465914981205926165214632019533,
            7755945018790142325513649272940177083855222863968691658328003977498047013576,
            81516639518483202269820502976089105897400159721845694286620077204726637043798,
            52824159213002398817852821148973968315579759063230697131029801896913602807019,
            44033460667645047622273556650595158811264350043302911918907282441675680538675,
            32396602643737403620316035551493791485834117358805817054817536312402837398361
        ]

        for i, ti in enumerate(test_vectors):
            mine = deterministic_generate_k(bin_sha256(str(i)), encode(i, 256, 32))
            self.assertEqual(
                ti,
                mine,
                "Test vector does not match. Details:\n%s\n%s" % (
                    ti,
                    mine
                )
            )


class TestStartingAddressAndScriptGenerationConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Starting address and script generation consistency tests")

    def test_all(self):
        for i in range(5):
            a = privtoaddr(random_key())
            self.assertEqual(a, script_to_address(address_to_script(a)))
            self.assertEqual(a, script_to_address(address_to_script(a), 0))
            self.assertEqual(a, script_to_address(address_to_script(a), 0x00))

            b = privtoaddr(random_key(), 5)
            self.assertEqual(b, script_to_address(address_to_script(b)))
            self.assertEqual(b, script_to_address(address_to_script(b), 0))
            self.assertEqual(b, script_to_address(address_to_script(b), 0x00))
            self.assertEqual(b, script_to_address(address_to_script(b), 5))
            self.assertEqual(b, script_to_address(address_to_script(b), 0x05))


        for i in range(5):
            a = privtoaddr(random_key(), 0x6f)
            self.assertEqual(a, script_to_address(address_to_script(a), 111))
            self.assertEqual(a, script_to_address(address_to_script(a), 0x6f))

            b = privtoaddr(random_key(), 0xc4)
            self.assertEqual(b, script_to_address(address_to_script(b), 111))
            self.assertEqual(b, script_to_address(address_to_script(b), 0x6f))
            self.assertEqual(b, script_to_address(address_to_script(b), 196))
            self.assertEqual(b, script_to_address(address_to_script(b), 0xc4))


class TestRipeMD160PythonBackup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('Testing the pure python backup for ripemd160')

    def test_all(self):
        strvec = [
            '',
            'The quick brown fox jumps over the lazy dog',
            'The quick brown fox jumps over the lazy cog',
            'Nobody inspects the spammish repetition'
        ]

        target = [
            '9c1185a5c5e9fc54612808977ee8f548b2258d31',
            '37f332f68db77bd9d7edd4969571ad671cf9dd3b',
            '132072df690933835eb8b6ad0b77e7b6f14acad7',
            'cc4a5ce1b3df48aec5d22d1f16b894a0b894eccc'
        ]

        hash160target = [
            'b472a266d0bd89c13706a4132ccfb16f7c3b9fcb',
            '0e3397b4abc7a382b3ea2365883c3c7ca5f07600',
            '53e0dacac5249e46114f65cb1f30d156b14e0bdc',
            '1c9b7b48049a8f98699bca22a5856c5ef571cd68'
        ]

        for i, s in enumerate(strvec):
            digest = ripemd.RIPEMD160(s).digest()
            hash160digest = ripemd.RIPEMD160(bin_sha256(s)).digest()
            self.assertEqual(bytes_to_hex_string(digest), target[i])
            self.assertEqual(bytes_to_hex_string(hash160digest), hash160target[i])
            self.assertEqual(bytes_to_hex_string(bin_hash160(from_string_to_bytes(s))), hash160target[i])
            self.assertEqual(hash160(from_string_to_bytes(s)), hash160target[i])


class TestScriptVsAddressOutputs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('Testing script vs address outputs')

    def test_all(self):
        addr0 = '1Lqgj1ThNfwLgHMp5qJUerYsuUEm8vHmVG'
        script0 = '76a914d99f84267d1f90f3e870a5e9d2399918140be61d88ac'
        addr1 = '31oSGBBNrpCiENH3XMZpiP6GTC4tad4bMy'
        script1 = 'a9140136d001619faba572df2ef3d193a57ad29122d987'

        inputs = [{
            'output': 'cd6219ea108119dc62fce09698b649efde56eca7ce223a3315e8b431f6280ce7:0',
            'value': 158000
        }]

        outputs = [
            [{'address': addr0, 'value': 1000}, {'address': addr1, 'value': 2000}],
            [{'script': script0, 'value': 1000}, {'address': addr1, 'value': 2000}],
            [{'address': addr0, 'value': 1000}, {'script': script1, 'value': 2000}],
            [{'script': script0, 'value': 1000}, {'script': script1, 'value': 2000}],
            [addr0 + ':1000', addr1 + ':2000'],
            [script0 + ':1000', addr1 + ':2000'],
            [addr0 + ':1000', script1 + ':2000'],
            [script0 + ':1000', script1 + ':2000']
        ]

        for outs in outputs:
            tx_struct = deserialize(mktx(inputs, outs))
            self.assertEqual(tx_struct['outs'], outputs[3])


class TestConversions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.privkey_hex = (
            "e9873d79c6d87dc0fb6a5778633389f4453213303da61f20bd67fc233aa33262"
        )
        cls.privkey_bin = (
            b"\xe9\x87=y\xc6\xd8}\xc0\xfbjWxc3\x89\xf4E2\x130=\xa6\x1f \xbdg\xfc#:\xa32b"
        )

        cls.pubkey_hex = (
            "04588d202afcc1ee4ab5254c7847ec25b9a135bbda0f2bc69ee1a714749fd77dc9f88ff2a00d7e752d44cbe16e1ebcf0890b76ec7c78886109dee76ccfc8445424"
        )
        cls.pubkey_bin = (
            b"\x04X\x8d *\xfc\xc1\xeeJ\xb5%LxG\xec%\xb9\xa15\xbb\xda\x0f+\xc6\x9e\xe1\xa7\x14t\x9f\xd7}\xc9\xf8\x8f\xf2\xa0\r~u-D\xcb\xe1n\x1e\xbc\xf0\x89\x0bv\xec|x\x88a\t\xde\xe7l\xcf\xc8DT$"
        )

    def test_privkey_to_pubkey(self):
        pubkey_hex = privkey_to_pubkey(self.privkey_hex)
        self.assertEqual(pubkey_hex, self.pubkey_hex)

    def test_changebase(self):
        self.assertEqual(
            self.pubkey_bin,
            changebase(
                self.pubkey_hex, 16, 256, minlen=len(self.pubkey_bin)
            )
        )

        self.assertEqual(
            self.pubkey_hex,
            changebase(
                self.pubkey_bin, 256, 16, minlen=len(self.pubkey_hex)
            )
        )

        self.assertEqual(
            self.privkey_bin,
            changebase(
                self.privkey_hex, 16, 256, minlen=len(self.privkey_bin)
            )
        )

        self.assertEqual(
            self.privkey_hex,
            changebase(
                self.privkey_bin, 256, 16, minlen=len(self.privkey_hex)
            )
        )


if __name__ == '__main__':
    unittest.main()
