from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from pydantic import BaseModel, Field  # Add new product
import re  # Search using letters
import requests  # Converting prices

MONGO_URI = "mongodb+srv://b00120626:webservca@cluster0.len2ad4.mongodb.net/?appName=Cluster0"

DB_NAME = "productsdb"
COLLECTION_NAME = "products"

app = FastAPI()

client = MongoClient(MONGO_URI)
    
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Create the container for a product for POST methods
class Product(BaseModel):
    ProductID : int = Field(..., gt = 0)  # Must be greater than 0
    Name : str
    UnitPrice : float = Field(..., ge = 0)  # Must be greater or equal to 0
    StockQuantity : int = Field(..., ge = 0)  # Must be greater or equal to 0
    Description : str
    
        
# Home Page
@app.get("/")
def homePage():
    return {"message" : "API Working"}


# Find one single product
@app.get("/getSingleProduct")
def get_single_product(product_id : int = Query(..., gt = 0)):  # Must be greater than 0
    
    product = collection.find_one(
        {"ProductID" : product_id},
        {"_id" : 0}
    )
    
    # If it cant be found, give error message
    if not product:
        raise HTTPException(status_code = 404, detail = "Product was not found")
    return product


# Find all products
@app.get("/getAll")
def get_all_products():
    products = list(collection.find({}, {"_id" : 0}))
    return {
        "count" : len(products),
        "products" : products
    }
    
    
# Add a new product
@app.post("/addNew")
def add_new(product : Product):
    pre_existing_product = collection.find_one({"ProductID" : product.ProductID})  # Defining pre existing products
    
    # If the user enteres in a product ID thats already been used
    if pre_existing_product:
        raise HTTPException(status_code = 400, detail = "ProductID already in use")
    
    # Add the product into the database
    collection.insert_one(product.model_dump())
    
    # Show the user the product added
    return{
        "message" : "The product has been added",
        "product" : product.model_dump()
    }
    
    
# Delete one single product
@app.get("/deleteOne")
def delete_one(product_id : int = Query(..., gt = 0)):  # Must be greater than 0
    
    deleted_product = collection.delete_one({"ProductID" : product_id})  # Find product and delete it
    
    # Check if the deleted product count went up
    if deleted_product.deleted_count == 0:
        raise HTTPException(status_code = 404, detail = "ProductID does not exist")  # If the count didnt increase
    
    # Show the user the product deleted
    return{
        "message" : f"The {product_id} product has been deleted"
    }
    
    
# Find a product starting with __ using regex
@app.get("/startsWith")
def starts_with(letters : str = Query(..., min_length = 1)):  # Must be at least 1 character long
    
    # Only allow letters, no numbers, spaces or special characters
    if not letters.isalpha():
        raise HTTPException(status_code = 400, detail = "Search must be in letters")
    
    # Regex for checking letter at beginning of product name
    searched = f"^{re.escape(letters)}"
    
    # Find all matching products
    products = list(collection.find(
        {"Name" : {"$regex" : searched, "$options" : "i"}},  # Allow for upper and lowercase
        {"_id" : 0}
    ))
    
    # If theres no products that match
    if not products:
        raise HTTPException(status_code = 404, detail = "No matching products found")
    
    # Show the list of matching products
    return {
        "count" : len(products),
        "products" : products
    }
    
    
# Show a list of products beteen two set Product IDs
@app.get("/paginate")
def paginate(starting_id : int = Query(..., gt = 0), ending_id : int = Query(..., gt = 0)):
    
    # If ending ID is smaller than starting ID then give error
    if ending_id < starting_id:
        raise HTTPException(status_code = 400, detail = "The Ending ID must be greater than Starting ID")
    
    # Find all products in the entered product ID range
    products = list(collection.find(
        # Show products greater/egual to starting ID and less/equal to ending ID
        {"ProductID" : {"$gte" : starting_id, "$lte" : ending_id}},  # Mongo will find nearest IDs to the entered ones
        {"_id" : 0}
    ).sort("ProductID", 1).limit(10))  # Sort all of them in decending orderr and only show a batch of 10
    
    # If no products are found in the entered product ID range
    if not products:
        raise HTTPException(status_code = 404, detail = "No products found within that range")
    
    # Show the list of products in that range
    return {
        "products" : products  # List all products in that range
    }


# Convert the price of a chosen product
@app.get("/convert")
def convert(product_id : int = Query(..., gt = 0)):
    
    # Searching for one specific product with Product ID
    product = collection.find_one(
        {"ProductID" : product_id},
        {"_id" : 0}
    )
    
    # If it cant be found, give error message
    if not product:
        raise HTTPException(status_code = 404, detail = "Product was not found")
    
    try:
        # Calling frankfurter API for current conversion rates for USD to Ero
        hear_back = requests.get(
            "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR",  # API
            timeout = 30  # Timeout time in seconds
        )
        
        hear_back.raise_for_status()  # Throw error if API is not working
        
        data = hear_back.json()  # Convert the API message to JSON
        
        euro = data["rates"]["EUR"]  # Pull EUR echange rate from JSON
        
        euro_ex = round(product["UnitPrice"] * euro, 2)  # Convert the USD price to EUR and round to 2 decimals
        
        # Return the producr details and new price
        return {
            "ProductID" : product["ProductID"],  # Product ID
            "Name" : product["Name"],  # Product name
            "USDPrice" : product["UnitPrice"],  # Original USD price
            "EURRate" : euro,  # The current echange rate for USD to EUR
            "EURConverted" : euro_ex  # The new EUR price
            
        }
        
    # API issue - Network or timeout
    except requests.exceptions.RequestException:
        raise HTTPException(status_code = 500, detail = "API not responding")
    
    # API issue - No data actuall returned
    except KeyError:
        raise HTTPException(status_code = 500, detail = "Invalid output")