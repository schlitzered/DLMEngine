Introduction
************

Opinionated Distributed Lock Manager, meant to be used for Ops related system orchestration tasks


Installing
----------

pip install DlmEngine

the configuration is expected to be placed in /etc/dlm_engine/dlm_engine.ini

an example configuration looks like this

```

[main]
host = 0.0.0.0
port = 9000

[file:logging]
acc_log = /var/log/dlm_engine/access.log
acc_retention = 7
app_log = /var/log/dlm_engine/application.log
app_retention = 7
app_loglevel = DEBUG

[session:redispool]
host = 192.168.33.12
#pass = dummy

[main:mongopool]
hosts = 192.168.33.12
db = dlm_engine
#pass =
#user =

[locks:mongocoll]
coll = locks
pool = main

[permissions:mongocoll]
coll = permissions
pool = main

[users:mongocoll]
coll = users
pool = main

[users_credentials:mongocoll]
coll = users_credentials
pool = main

```


Author
------

Stephan Schultchen <stephan.schultchen@gmail.com>

License
-------

Unless stated otherwise on-file foreman-dlm-updater uses the MIT license,
check LICENSE file.

Contributing
------------

If you'd like to contribute, fork the project, make a patch and send a pull
request.