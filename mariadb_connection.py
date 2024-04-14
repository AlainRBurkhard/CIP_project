from sqlalchemy import create_engine, MetaData, Table
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection parameters
DB_USER = 'root'         # Replace with your MariaDB username
DB_PASSWORD = 'new_password' # Replace with your MariaDB password
DB_HOST = 'localhost'    # Replace with your MariaDB host
DB_PORT = '3306'         # Replace with your MariaDB port
DB_NAME = 'mediamarkt_db'   # Replace with your MariaDB database name

# Create a database connection URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Test the database connection
try:
    engine.connect()
    print("Connected to MariaDB successfully!")
    
    # Optional: List tables in the database
    metadata = MetaData()
    metadata.reflect(bind=engine)
    print("Tables in the database:")
    for table in metadata.tables.values():
        print(table.name)
        
except Exception as e:
    print(f"Error connecting to MariaDB: {e}")
    
    
df = pd.read_csv("data/stage03_mediamarkt.csv")
df.columns, df.dtypes


products = Table('products', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('brand', String(255)),
    Column('model', String(255)),
    Column('category', String(255)),
    Column('size', Float),
    Column('storage', String(50)),
    Column('color', String(50)),
    Column('rating', Float),
    Column('n_of_reviews', Integer),
    Column('delivery_time', Float),
    Column('price', Float),
    Column('source', String(255)),
    Column('date', Date)
)

# Create the table in the database
metadata.create_all(engine)

print("Table 'products' created successfully!")

df.to_sql('products', engine, if_exists='append', index=False, chunksize=1000)


Base = declarative_base()

# Define the products class
class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(255))
    model = Column(String(255))
    category = Column(String(255))
    size = Column(Float)
    storage = Column(String(50))
    color = Column(String(50))
    rating = Column(Float)
    n_of_reviews = Column(Integer)
    delivery_time = Column(Float)
    price = Column(Float)
    source = Column(String(255))
    date = Column(Date)


Session = sessionmaker(bind=engine)

# Create a session
session = Session()

# Execute a SELECT query to fetch all data from the 'products' table
products = session.query(Product).all()

# Convert the query results to a list of dictionaries for easier viewing
results = [product.__dict__ for product in products]