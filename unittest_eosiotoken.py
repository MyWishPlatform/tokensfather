import setup
import json
import eosf
from termcolor import cprint
import node
import unittest

setup.set_verbose(False)
setup.set_json(False)
setup.use_keosd(False)


class CrowdsaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def run(self, result=None):
        """ Stop after first error """
        if not result.failures:
            super().run(result)

    def setUp(self):
        # start node
        assert (not node.reset().error)

        # create wallet
        eosf.set_verbosity([])  # disable logs
        self.wallet = eosf.Wallet()

        # create eosio account
        self.eosio_acc = eosf.AccountMaster()
        self.wallet.import_key(self.eosio_acc)
        eosf.set_verbosity()  # enable logs

        # create token deployer account
        self.token_deployer_acc = eosf.account(self.eosio_acc, "tkn.deployer")
        self.wallet.import_key(self.token_deployer_acc)

        # deploy eosio.bios contract
        self.eosio_bios_contract = eosf.Contract(self.eosio_acc, "eosio.bios")
        assert (not self.eosio_bios_contract.error)
        deployment_bios = self.eosio_bios_contract.deploy()
        assert (not deployment_bios.error)

        # deploy custom eosio.token contract
        self.token_contract = eosf.Contract(
            self.token_deployer_acc,
            "eosiotoken/eosio.token",
            wast_file='eosio.token.wast',
            abi_file='eosio.token.abi'
        )
        assert (not self.token_contract.error)
        deployment_token = self.token_contract.deploy()
        assert (not deployment_token.error)
        assert (not self.token_deployer_acc.code().error)

    def tearDown(self):
        node.stop()

    def test_01(self):
        cprint(".1. Check that locked tokens cannot be transferred", 'green')

        # create accounts
        issuer = eosf.account(self.eosio_acc, "issuer")
        holder = eosf.account(self.eosio_acc, "holder")
        self.wallet.import_key(issuer)
        self.wallet.import_key(holder)

        # create and issue asset
        assert (not self.token_contract.push_action(
            "create",
            json.dumps({
                "issuer": str(issuer),
                "maximum_supply": "10000.0000 ABC",
                "lock": True
            }),
            self.token_deployer_acc
        ).error)
        assert (not self.token_contract.push_action(
            "issue",
            json.dumps({
                "to": str(holder),
                "quantity": "500.0000 ABC",
                "memo": ""
            }),
            issuer
        ).error)

        # try to transfer locked tokens
        assert (self.token_contract.push_action(
            "transfer",
            json.dumps({
                "from": str(holder),
                "to": str(issuer),
                "quantity": "250.0000 ABC",
                "memo": ""
            }),
            holder
        ).error)

    def test_02(self):
        cprint("2. Check that unlocked tokens can be transferred", 'green')

        # create accounts
        issuer = eosf.account(self.eosio_acc, "issuer")
        holder = eosf.account(self.eosio_acc, "holder")
        self.wallet.import_key(issuer)
        self.wallet.import_key(holder)

        # create and issue asset
        assert (not self.token_contract.push_action(
            "create",
            json.dumps({
                "issuer": str(issuer),
                "maximum_supply": "10000.0000 ABC",
                "lock": True
            }),
            self.token_deployer_acc
        ).error)
        assert (not self.token_contract.push_action(
            "issue",
            json.dumps({
                "to": str(holder),
                "quantity": "500.0000 ABC",
                "memo": ""
            }),
            issuer
        ).error)

        # check that not issuer can't unlock tokens
        assert (self.token_contract.push_action(
            "unlock",
            json.dumps({
                "symbol": "4,ABC"
            }),
            holder
        ).error)

        # unlock tokens by issuer
        assert (not self.token_contract.push_action(
            "unlock",
            json.dumps({
                "symbol": "4,ABC"
            }),
            issuer
        ).error)

        # try to transfer unlocked tokens
        assert (not self.token_contract.push_action(
            "transfer",
            json.dumps({
                "from": str(holder),
                "to": str(issuer),
                "quantity": "250.0000 ABC",
                "memo": ""
            }),
            holder
        ).error)

    def test_03(self):
        cprint("3. Check that nonlocked tokens can be transferred", 'green')

        # create accounts
        issuer = eosf.account(self.eosio_acc, "issuer")
        holder = eosf.account(self.eosio_acc, "holder")
        self.wallet.import_key(issuer)
        self.wallet.import_key(holder)

        # create and issue asset
        assert (not self.token_contract.push_action(
            "create",
            json.dumps({
                "issuer": str(issuer),
                "maximum_supply": "10000.0000 ABC",
                "lock": False
            }),
            self.token_deployer_acc
        ).error)
        assert (not self.token_contract.push_action(
            "issue",
            json.dumps({
                "to": str(holder),
                "quantity": "500.0000 ABC",
                "memo": ""
            }),
            issuer
        ).error)

        # try to transfer tokens
        assert (not self.token_contract.push_action(
            "transfer",
            json.dumps({
                "from": str(holder),
                "to": str(issuer),
                "quantity": "250.0000 ABC",
                "memo": ""
            }),
            holder
        ).error)


if __name__ == "__main__":
    unittest.main()
