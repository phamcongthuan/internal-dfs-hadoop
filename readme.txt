[ENGLISH BELOW]

Cấu trúc thư mục

app/
├── __init__.py
├── index.py
├── auth.py
├── models.py
├── utils.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── change_password.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js


Source chỉ bao gồm code frontend/backend, cần chuẩn bị thêm:

1. Cài đặt MySQL
- Tạo database tên "usersdb"
- Tạo bảng "users", "files", "shared_files" (như file "models.py")

2. 3 máy tính (máy ảo vmware) chạy hệ điều hành Ubuntu để làm 1 MasterNode và 2 SlaveNode
- MasterNode: IP 192.168.2.10, user “phamcongthuan”.
- SlaveNode1: IP 192.168.2.11, user “phamcongthuan”.
- SlaveNode2: IP 192.168.2.12, user “phamcongthuan”.

3. Cài đặt Hadoop và cấu hình HDFS (hướng dẫn tại chương 4, mục 4.1)
`

4. Cài các thư viện cần thiết: pip install flask flask_sqlalchemy flask_login flask_admin pymysql


5. Trong file "__init__.py", sửa lại username và password tương ứng
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/usersdb


*** Điều kiện để hệ thống hoạt động bình thường:
- Khởi động MySQL
- Khởi động Hadoop trên MasterNode, kiểm tra bằng lệnh jps. MasterNode phải có dòng Namenode, SlaveNode1 và SlaveNode2 phải có Datanode
- Chạy file "index.py"

######################

Directory Structure

app/
├── __init__.py
├── index.py
├── auth.py
├── models.py
├── utils.py
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── change_password.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js

This project includes only the frontend and backend source code. To run the system, you need to prepare the following:

1. Install MySQL
- Create a database named usersdb.
- Create the tables users, files, and shared_files (defined in models.py).

2. Set up 3 computers (VMware virtual machines) running Ubuntu to form a Hadoop cluster
- Master Node: IP 192.168.2.10, user phamcongthuan.
- Slave Node 1: IP 192.168.2.11, user phamcongthuan.
- Slave Node 2: IP 192.168.2.12, user phamcongthuan.

3. Install Hadoop and configure HDFS
See Chapter 4, Section 4.1 of the documentation for installation and configuration instructions.

4. Install required Python libraries: pip install flask flask_sqlalchemy flask_login flask_admin pymysql

5. Update in __init__.py, modify the following line to match your MySQL username and password:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/usersdb'

*** System Requirements for Proper Operation:
- MySQL service must be running.
- Hadoop must be started on the master node. Check with the jps command: Master node must show NameNode, Slave nodes must show DataNode
- Run index.py to start the web application.


