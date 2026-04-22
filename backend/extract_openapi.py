import json
from app.main import app

def extract():
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)
    print("OpenAPI schema extracted to openapi.json")

if __name__ == "__main__":
    extract()
