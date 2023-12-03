from cat.plugins.sql_gpt.database.database_manager import DatabaseManager
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TestDatabaseManager(DatabaseManager):
    class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        age = Column(Integer)

    class Order(Base):
        __tablename__ = 'orders'

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        product = Column(String)
        quantity = Column(Integer)

    def __init__(self, db_uri='sqlite:///sample.db'):
        super().__init__(db_uri)

    def drop_tables(self):
        Base.metadata.drop_all(self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def insert_sample_data(self):
        session = self.Session()

        # Sample data for demonstration
        user1 = self.User(name='John Doe', age=30)
        user2 = self.User(name='Jane Doe', age=25)
        user3 = self.User(name='Bob Smith', age=40)

        order1 = self.Order(user_id=1, product='Product A', quantity=2)
        order2 = self.Order(user_id=1, product='Product A', quantity=5)
        order3 = self.Order(user_id=2, product='Product B', quantity=1)
        order4 = self.Order(user_id=3, product='Product C', quantity=3)

        session.add_all([user1, user2, user3, order1, order2, order3, order4])
        session.commit()
        session.close()
