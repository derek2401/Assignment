import csv
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://b00120626:webservca@cluster0.len2ad4.mongodb.net/?appName=Cluster0"

DB_NAME = "productsdb"
COLLECTION_NAME = "products"

CSV_FILE = "products.csv"

def send_csv():
    
    client = MongoClient(MONGO_URI)
    
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    products = []
    
    with open(CSV_FILE, mode = "r", encoding = "utf-8-sig") as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            product = {
                "ProductID": int(row["ProductID"]),
                "Name": row["Name"].strip(),
                "UnitPrice": float(row["UnitPrice"]),
                "StockQuantity": int(row["StockQuantity"]),
                "Description": row["Description"].strip()
            }
            
            products.append(product)
            
    if products:
        collection.insert_many(products)
        print(f"CSV has been saved to Mongo")
        
if __name__ == "__main__":
    send_csv()