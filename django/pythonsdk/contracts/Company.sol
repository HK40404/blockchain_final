import "./Table.sol";

contract Company {
    event RegisterCompany(int count);
    event RemoveCompany(int count);
    event CreateCompanyTable(int count);

    // 加公司电话、公司介绍
    function create() public returns(int){
        TableFactory tf = TableFactory(0x1001);  // TableFactory的地址固定为0x1001
        // 创建t_test表，表的key_field为name，value_field为item_id,item_name 
        // key_field表示AMDB主key value_field表示表中的列，可以有多列，以逗号分隔
        int count = tf.createTable("t_company", "company", "owner,name,address,credit,type");
        emit CreateCompanyTable(count);
        return count;
    }

    function openTable() private returns(Table) {
        TableFactory tf = TableFactory(0x1001);
        Table table = tf.openTable("t_company");
        return table;
    }

    // 查询机构是否存在，机构名字是唯一的
    function isExist(string name) public constant returns (bool) {
        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("company", "company");
        condition.EQ("name", name);
        Entries entries = table.select("company", condition);

        if (uint256(entries.size()) == 0) {
            return false;
        } else {
            return true;
        }
    }

    // 插入公司数据
    // 返回码: -1:公司已存在; 0:成功; -2:使用了保留名; -3:其他错误; 
    function register(string name, string addr, string credit, string companyType) public returns(int ret) {
        if (isEqualString("此公司不存在", name)) {
            return -2;
        }
        if (isExist(name) == false) {
            Table table = openTable();

            Entry entry = table.newEntry();
            entry.set("company", "company");
            entry.set("name", name);
            entry.set("owner", msg.sender);
            entry.set("address", addr);
            entry.set("credit", credit);
            entry.set("type", companyType);

            int res = table.insert("company", entry);
            if (res == 1) {
                ret = 0; // 成功
            } else {
                ret = -3; // 失败? 无权限或者其他错误
            }
        } else {
            ret = -1;
        }
        emit RegisterCompany(ret);
    }

    // 得到公司的所有资料
    function queryCompanyByName(string name) public constant returns(string name0, address owner, string addr, string credit, string companyType) {
        Table table = openTable();
        Condition condition = table.newCondition();
        condition.EQ("company", "company");
        condition.EQ("name", name);
        Entries entries = table.select("company", condition);

        if (uint256(entries.size()) == 0) {
            name0 = "此公司不存在";
        } else {
            Entry entry = entries.get(0);
            name0 = name;
            owner = entry.getAddress("owner");
            addr = entry.getString("address");
            credit = entry.getString("credit");
            companyType = entry.getString("type");
        }
    }

    // 删除公司数据
    // 返回码: -1:公司不存在; 0:成功; -2:非本人删除; -3:其他错误
    function erase(string name) public returns(int ret) {
        if (isExist(name) == false) {
            return -1;
        } else {
            address owner;
            (, owner, , , ) = queryCompanyByName(name);
            if (owner != msg.sender) {
                return -2;
            } else {
                Table table = openTable();
                Condition condition = table.newCondition();
                condition.EQ("company", "company");
                condition.EQ("name", name);
                
                int count = table.remove("company", condition);
                
                if (count == 1) {
                    ret = 0;
                } else {
                    ret = -3;
                }
            }
        }
        emit RemoveCompany(ret);
    }

    function isEqualString(string a, string b) returns (bool equal) {
        if (bytes(a).length != bytes(b).length) {
            return false;
        } else {
            return keccak256(bytes(a)) == keccak256(bytes(b));
        }
    }

    // enum Creditlevel { // 银行可以对企业进行信用评级
    //     Verygood, // 0
    //     Good,     // 1
    //     Normal,   // 2
    //     Notgood,  // 3
    //     Bad       // 4
    // }

    // enum Type {
    //     Bank, // 银行
    //     State_owned_enterprise, // 国有企业
    //     Foreign_enterprise, // 外企
    //     Private_enterprise, // 私人企业
    //     Joint_venture // 合资企业
    // }
}