import "./Table.sol";
import "./Company.sol";

contract Receipt1 {
    event InsertReceipt(int count);
    event RemoveReceipt(int count);
    event CreateReceiptTable(int count);
    event UpdateReceipt(int count);
    event TransferReceipt(int count);

    Company public company = Company(0x2d1c577e41809453c50e7e5c3f57d06f3cdd90ce);

    function create() public returns(int){
        TableFactory tf = TableFactory(0x1001);  // TableFactory的地址固定为0x1001
        int count = tf.createTable("t_rep1", "receipt", "title,from,to,amount,createTime,lastTime,bankConfirm,comment");
        emit CreateReceiptTable(count);
        return count;
    }

    function openTable() private returns(Table) {
        TableFactory tf = TableFactory(0x1001);
        Table table = tf.openTable("t_rep1");
        return table;
    }

    // 查询账款是否存在
    function isExist(string title) public returns (bool) {
        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("receipt", "receipt");
        condition.EQ("title", title);
        Entries entries = table.select("receipt", condition);

        if (uint256(entries.size()) == 0) {
            return false;
        } else {
            return true;
        }
    }

    // 插入新账款, 还要检查from和to
    // 返回码: 0:成功; -1:账款不存在; -2:from和to相同; -3:公司from或to不存在 -4:其他错误
    function insert(string title, string from, string to, int amount, int lastTime, int bankConfirm, 
        string comment) public returns(int ret) {
        // 检查from != to
        if (isEqualString(from, to)) {
            ret = -2;
        } 
        // 检查from和to存在
        else if (company.isExist(from) == false || company.isExist(to) == false) {
            ret = -3;
        }
        else if (isExist(title) == false) {
            Table table = openTable();

            Entry entry = table.newEntry();
            entry.set("receipt", "receipt");
            entry.set("title", title);
            entry.set("from", from);
            entry.set("to", to);
            entry.set("amount", amount);
            entry.set("createTime", int(now));
            entry.set("lastTime", lastTime);
            entry.set("bankConfirm", bankConfirm);
            entry.set("comment", comment);

            int res = table.insert("receipt", entry);
            if (res == 1) {
                ret = 0; // 成功
            } else {
                ret = -4; // 失败? 无权限或者其他错误
            }
        } else {
            ret = -1;
        }
        emit InsertReceipt(ret);
    }

    // 得到账款情况
    function queryReceiptByTitle(string receiptTitle) public constant returns(string title, string from, string to, int amount, 
        int createTime, int lastTime, int bankConfirm, string comment) {

        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("receipt", "receipt");
        condition.EQ("title", receiptTitle);
        Entries entries = table.select("receipt", condition);

        if (uint256(entries.size()) == 0) {
            title = "此账款不存在";
        } else {
            Entry entry = entries.get(0);

            title = receiptTitle;
            from = entry.getString("from");
            to = entry.getString("to");
            amount = entry.getInt("amount");
            createTime = entry.getInt("createTime");
            lastTime = entry.getInt("lastTime");
            bankConfirm = entry.getInt("bankConfirm");
            comment = entry.getString("comment");
        }
    }

    // 查看某一个公司的（欠/收）账款总数, 所有人可查
    function queryReceiptNumber(string companyName, bool from) public returns(int number) {
        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("receipt", "receipt");
        if (from == true) {
            // 欠款
            condition.EQ("from", companyName);
        } else {
            // 收款
            condition.EQ("to", companyName);
        }
        Entries entries = table.select("receipt", condition);
        return entries.size();
    }

    // 查看某一个公司的账款，只显示title，可根据title深入查看，选择看该公司为欠款方还是收款方
    function queryReceiptByCompany(string companyName, bool from) public returns(bytes32[]) {
        
        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("receipt", "receipt");
        if (from == true) {
            condition.EQ("from", companyName);
        } else {
            condition.EQ("to", companyName);
        }

        Entries entries = table.select("receipt", condition);
        bytes32[] memory receipt_title_list = new bytes32[](uint256(entries.size()));

        for(int i=0; i<entries.size(); ++i) {
            Entry entry = entries.get(i);
            receipt_title_list[uint256(i)] = entry.getBytes32("title");
        }

        return receipt_title_list;
    }

    // 账款转让
    // 错误码: -1:待转让公司不存在; -2:账款不存在; -3:转让人不是公司所有者; -4:余额不足; -5:公司相同
    function transferReceipt(string target, string from, string middle, string to, int amount, string title) public returns(int ret) {
        
        if (company.isExist(to) == false) {
            ret = -1;
        } 
        else if (isEqualString(middle, to)){
            ret = -5;
        }
        else if (isExist(target) == false) {
            ret = -2;
        }
        else {
            address owner;
            (, owner, , , ) = company.queryCompanyByName(middle);
            // 转让人必须为公司所有者
            if (msg.sender != owner) {
                ret = -3;
            } else {
                int balance;
                int bankConfirm;
                int createTime;
                int lastTime;
                (, , , balance, createTime, lastTime, bankConfirm, ) = queryReceiptByTitle(target);
                if (balance < amount) {
                    ret = -4;
                } else {
                    int newBalance = balance - amount;
                    if (newBalance == 0) {
                        deleteReceipt(target);
                    } else {
                        updateReciptAmount(target, newBalance);
                    }

                    int newLastTime = createTime - int(now);
                    newLastTime += lastTime;
                    insert(title, from, to, amount, newLastTime, bankConfirm, "");
                    ret = 0;
                }
            }
        }
        emit TransferReceipt(ret);
    }

    function updateReciptAmount(string title, int amount) private returns(int) {
        Table table = openTable();

        Entry entry = table.newEntry();
        entry.set("amount", amount);

        Condition condition = table.newCondition();
        condition.EQ("receipt", "receipt");
        condition.EQ("title", title);

        int count = table.update("receipt", entry, condition);
        emit UpdateReceipt(count);
        return count;
    }

    // 只有账款持有者可以消除
    // 错误码: -1:账款不存在 -2:非持有人操作 1:正常
    function removeReceipt(string title) public returns(int ret) {
        if (isExist(title) == false) {
            return -1;
        } 
        string memory to;
        (, , to, , , , , ) = queryReceiptByTitle(title);

        address owner;
        (, owner, , , ) = company.queryCompanyByName(to);

        if (msg.sender != owner) {
            return -2;
        } 

        ret = deleteReceipt(title); 
        return ret;       
    }

    function deleteReceipt(string title) private returns(int) {
        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("receipt", "receipt");
        condition.EQ("title", title);
        int count = table.remove("receipt", condition);
        emit RemoveReceipt(count);
        return count;
    }
    
    function isEqualString(string a, string b) public returns (bool equal) {
        if (bytes(a).length != bytes(b).length) {
            return false;
        } else {
            return keccak256(bytes(a)) == keccak256(bytes(b));
        }
    }

}
