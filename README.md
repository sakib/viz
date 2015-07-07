Vizness card application repository. Flask App in development.

To get set up on the project:

1. Set up virtualenv
    - run "virtualenv -p python3 venv"
    - to activate run "source venv/bin/activate"
    - to deactivate run "deactivate"
2. Use pip to install dependencies (in the virtualenv)
    - run "pip install -r pip.req". Try skipping next two commands.
    - run "pip install -i https://testpypi.python.org/pypi Flask-Auth"
    - run "pip install https://launchpad.net/oursql/py3k/py3k-0.9.4/+download/oursql-0.9.4.zip":
3. Run "python run.py"

Database stuff:

Ubuntu: sudo apt-get install mysql-server libmysqlclient-dev
Fedora: yum install python-migrate

Run the following commands:
- "sudo mysql"
- "create database viz;"
- "create user 'viz'@'localhost' identified by 'viz';"
- "grant all privileges on viz.* to 'viz'@'localhost';"
- "flush privileges;"
Quit out of mysql with "quit". Then run:
- "./migrate.py db migrate"
- "./migrate.py db upgrade"

To check the database subsequently, run "mysql -uviz -pviz"
To change database structure, edit viz/models.py, then run migrate and upgrade again.
If you happen to remove the migrations folder, then run init, migrate, then upgrade.
