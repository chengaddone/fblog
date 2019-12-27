from flask_script import Manager

from blog import create_app

app = create_app()
# 使用manager管理app
manager = Manager(app)


if __name__ == '__main__':
    print(app.url_map)
    manager.run()
