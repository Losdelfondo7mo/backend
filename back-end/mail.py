from typing import Optional
from fastapi import FastAPI, Path

app = FastAPI()

inventory = {
    1: {
        "name": "Milk",
        "price": 3.99,
        "brand": "Regular"
    },
    2: {
        "name": "Bread",
        "price": 2.99,
        "brand": "brown"
    }
}
@app.get("/get-item/{item_id}")
def get_item(item_id: int = Path(description="The ID of the item you'd like to view")):
    return inventory[item_id]

@app.get("/get-by-name")
def get_item(name: Optional[str] = None ):
    for item_id in inventory:
        if inventory[item_id]["name"] == name:
            return inventory[item_id]
    return {"Data": "Not Found"}


        