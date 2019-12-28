from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from blog import create_app, db, models

app = create_app("development")
# 使用manager管理app
manager = Manager(app)
# 引入数据库迁移，关联app与db，并添加迁移命令
Migrate(app, db)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    print(app.url_map)
    manager.run()
