# -*- coding: utf-8 -*- 
import os
import json
from client.bcosclient import BcosClient
from client.datatype_parser import DatatypeParser
from client.bcoserror import BcosException, BcosError
from eth_account.account import Account
from eth_account.messages import encode_defunct
from client_config import client_config
from client.precompile.permission.permission_service import PermissionService
from client.precompile.crud.condition import Condition
from client.precompile.crud.crud_service import Entry, CRUDService

# 实例化client
class ChainManager:

    def __init__(self):        
        self.client = BcosClient()
        self.dataparser = DatatypeParser()

        self.dataparser.load_abi_file("./pythonsdk/contracts/Receipt2.abi")
        self.RECEIPT_ABI = self.dataparser.contract_abi
        self.dataparser.load_abi_file("./pythonsdk/contracts/Company.abi")
        self.COMPANY_ABI = self.dataparser.contract_abi
        self.COMPANY_ADDRESS = "0x2d1c577e41809453c50e7e5c3f57d06f3cdd90ce"
        self.RECEIPT_ADDRESS = "0x98bc6df6b170d66fb5de93cf69b1f8746908f6d5"
        # res = self.client.load_default_account()
        self.BANK_ADDRESS = "0x3e4bf936a2ede27947a2c161abbdfc39df4619ab"

    def __del__(self):
        self.client.finish()

    def hexstr2int(self, hexstr):
        bit = (len(hexstr) - 2) * 4
        num = int(hexstr, 16)
        # hex str to int
        if num > 2 ** (bit - 1) - 1:
            num = 2 ** bit - num
            num = 0 - num
        return num

    def login(self, username, password):
        keystore_file = "{}/{}".format(client_config.account_keyfile_path,
                                            username + ".keystore")
        if os.path.exists(keystore_file) is False:
            return -1
        try:
            with open(keystore_file, "r") as dump_f:
                keytext = json.load(dump_f)
                privkey = Account.decrypt(keytext, password)
                self.client.client_account = Account.from_key(privkey)
        except Exception as e:
            return -1
        return 0
    
    def register(self, username, password):
        ac = Account.create(password)
        kf = Account.encrypt(ac.privateKey, password)
        keyfile = "{}/{}.keystore".format(client_config.account_keyfile_path, username)
        
        # file is exist, account is registed
        if os.access(keyfile, os.F_OK):
            return -1
        try:
            with open(keyfile, "w") as dump_f:
                json.dump(kf, dump_f)
                dump_f.close()

            with open(keyfile, "r") as dump_f:
                keytext = json.load(dump_f)
                privkey = Account.decrypt(keytext, password)
                client_account = Account.from_key(privkey)
                ps = PermissionService("./pythonsdk/contracts/precompile")
                ps.grant("t_rep1", client_account.address)
                ps.grant("t_company", client_account.address)
                del ps
        # write file failed
        except Exception as e:
            return -2
        return 0

    def sign(self, username, password, info):
        keystore_file = "{}/{}".format(client_config.account_keyfile_path,
                                            username + ".keystore")
        if os.path.exists(keystore_file) is False:
            return -1
        try:
            with open(keystore_file, "r") as dump_f:
                keytext = json.load(dump_f)
                privkey = Account.decrypt(keytext, password)
                msg = encode_defunct(text=info)
                signed_msg = Account.sign_message(msg, privkey)
                v = signed_msg['v']
                r = signed_msg['r']
                s = signed_msg['s']
                return v, r, s
        except Exception as e:
            print(e)
            return -1

    def registerCom(self, username, name, addr, credit, comtype, vrs):
        ''' authority '''
        info = username + name + addr + credit + comtype
        msg = encode_defunct(text=info)
        bank_addr = Account.recover_message(msg, vrs=vrs)

        # 没有授权
        if not bank_addr.lower() == self.BANK_ADDRESS:
            return -4

        ''' register company '''
        log = self.client.sendRawTransactionGetReceipt(self.COMPANY_ADDRESS, self.COMPANY_ABI, "register", [name,addr,credit,comtype])
        output = log['output']
        ret = self.hexstr2int(output)
        return ret

    def queryCom(self, name):
        info = self.client.call(self.COMPANY_ADDRESS, self.COMPANY_ABI, "queryCompanyByName", [name])
        if info[0] == "此公司不存在":
            return -1
        return info

    def eraseCom(self, name):
        log = self.client.sendRawTransactionGetReceipt(self.COMPANY_ADDRESS, self.COMPANY_ABI, "erase", [name])
        ret = log['output']
        ret = self.hexstr2int(ret)
        return ret

    def createReceipt(self, title, fromc, toc, amount, lastTime, comment, vrs=None):
        bankConfirm = 0
        if vrs:
            info = title+fromc+toc+str(amount)+str(lastTime)
            msg = encode_defunct(text=info)
            bank_addr = Account.recover_message(msg, vrs=vrs)
            if bank_addr.lower() == self.BANK_ADDRESS:
                bankConfirm = 1
        
        info = self.client.call(self.COMPANY_ADDRESS, self.COMPANY_ABI, "queryCompanyByName", [fromc])
        owner = info[1]
        # 账款必须由欠款方创建
        if self.client.client_account.address.lower() != owner.lower():
            return -5

        log = self.client.sendRawTransactionGetReceipt(self.RECEIPT_ADDRESS, self.RECEIPT_ABI, "insert", [title, fromc, toc, amount, lastTime, bankConfirm, comment])
        output = log['output']
        ret = self.hexstr2int(output)
        return ret
    
    def queryReceipt(self, title):
        info = self.client.call(self.RECEIPT_ADDRESS, self.RECEIPT_ABI, "queryReceiptByTitle", [title])
        if info[0] == "此账款不存在":
            return -1
        return info

    def queryReceiptOfCom(self, company, isfrom):
        receipts = self.client.call(self.RECEIPT_ADDRESS, self.RECEIPT_ABI, "queryReceiptByCompany", [company, isfrom])
        receipts = receipts[0]
        res = []
        for receipt in receipts:
            tmp = str(receipt, encoding='utf8').strip('\x00')
            res.append(tmp)
        return res

    def transferReceipt(self, title, fromc, middle, to, amount, newtitle):
        ret = self.client.sendRawTransactionGetReceipt(self.RECEIPT_ADDRESS, self.RECEIPT_ABI, "transferReceipt", [title, fromc, middle, to, amount, newtitle])
        ret = ret['output']
        ret = self.hexstr2int(ret)
        return ret

    def deleteReceipt(self, title):
        ret = self.client.sendRawTransactionGetReceipt(self.RECEIPT_ADDRESS, self.RECEIPT_ABI, "removeReceipt", [title])
        ret = ret['output']
        ret = self.hexstr2int(ret)
        return ret

