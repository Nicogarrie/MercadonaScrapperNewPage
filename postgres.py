import psycopg2
import os
from configs import init_config_postgres
from utils import store_already_saved_ids
import sqlalchemy as sql


params = init_config_postgres()

TABLE = 'products'
LOCAL_DB = "db_type://user:passw@host:port/dbname"


def connect_db():
    db_engine = None
    try:
        db_engine = sql.create_engine(LOCAL_DB)
    finally:
        return db_engine


def create_table(db_engine):
    with db_engine.connect() as db_connection:
        metaData = sql.MetaData(bind=db_engine)

        try:
            products_table = sql.Table(TABLE,
                                       metaData,
                                       sql.Column("id", sql.String(64),
                                                  primary_key=True),
                                       sql.Column("name", sql.String()),
                                       sql.Column("price", sql.Float()),
                                       sql.Column("price_quantity",
                                                  sql.String()),
                                       sql.Column("price_unit", sql.String()),
                                       sql.Column("size", sql.Float()),
                                       sql.Column("size_units", sql.String()),
                                       sql.Column("category", sql.String()),
                                       sql.Column("subcategory", sql.String()),
                                       sql.Column("section",
                                                  sql.String()),
                                       sql.Column("image_url", sql.String()),
                                       sql.Column("container",
                                                  sql.String()),
                                       extend_existing=True)
            products_table.create(db_connection, checkfirst=True)
        except Exception as e:
            logging.exception(
                f"Exception creating products table: {str(e)}")


def save_df(df):
    if db_engine := connect_db():
        try:
            create_table(db_engine)
            df.to_sql(name=TABLE, con=db_engine, if_exists="append",
                      index=False)
            store_already_saved_ids(df['id'].to_list())
        except Exception as e:
            print(f"There was an error in the postgres db: {e}")
            