## Vizness card flask app repo.

##### To get set up on the project:

Set up virtualenv: `$ virtualenv -p python3 venv`

Activate virtualenv: `source venv/bin/activate` 

Use pip to install dependencies in the virtualenv: `$ pip install -r pip.req`

Run the server (CTRL+C to quit): `./run.py`

Deactivate virtualenv: `deactivate`

##### Dependency Resolution:

Ubuntu: `sudo apt-get install mysql-server libmysqlclient-dev systemctl`

Fedora: `yum install mysql python-migrate postfix systemctl`

##### Database Setup:
```
$ sudo mysql
$ create database viz;
$ create user 'viz'@'localhost' identified by 'viz';
$ grant all privileges on viz.* to 'viz'@'localhost';
$ flush privileges;
```

Quit out of mysql with "quit". Then run:

```
$ ./migrate.py db migrate
$ ./migrate.py db upgrade
```

To check the database subsequently, run "mysql -uviz -pviz"
To change database structure, edit viz/models.py, then run migrate and upgrade again.
If you happen to remove the migrations folder, then run init, migrate, then upgrade.

Upon errors like "Cannot find MySQLd service" or "MySQL.sock" try `sudo systemctl start mariadb`

Upon errors like "Email confirmation failed to send" try `sudo systemctl start postfix`
