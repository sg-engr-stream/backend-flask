from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import app, db, app_settings

app.config.from_object(app_settings)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
