import pickle
import atexit

DB_FILE  = "creators.db"

# Load database at startup
try:
    with open(DB_FILE, "rb") as f:
        creators_db = pickle.load(f)
except (FileNotFoundError, EOFError):
    creators_db = {}  # Default to an empty dictionary if the file is missing or empty

def save_database():
    """Saves the database automatically when the script exits."""
    with open(DB_FILE, "wb") as f:
        pickle.dump(creators_db, f)

# Ensure data is saved when the script exits
atexit.register(save_database)

def insert_creator(creator_name, creator_id):
    """Inserts a new creator into the database."""
    if creator_name in creators_db:
        print(f"already")
        return False  
    creators_db[creator_name] = creator_id
    print(f"success")
    save_database()
    return True

def remove_none_creators():
    # Filter out creators with the name "None"
    global creators_db
    creators_db = {k: v for k, v in creators_db.items() if v["name"] != "None"}

def get_creator_id(creator_name):
    """Retrieves the creator ID based on the name."""
    return creators_db.get(creator_name, None)

def get_creator_name(creator_id):
    """Finds the creator's name based on their ID."""
    for name, cid in creators_db.items():
        if cid == creator_id:
            return name
    return None

def get_all_creators():
    #remove_none_creators()
    """Returns all creators in the database."""
    return creators_db

def get_all_creators_with_none():
    return creators_db

# Example Usage
#if  __name__ == "__main__":
    #insert_creator('meexal', '36c7012a4f5b40069bab68ae374e4f2e')

    #print("ID of 'meexal':", get_creator_id('meexal'))  
    #print("Name of ID '36c7012a4f5b40069bab68ae374e4f2e':", get_creator_name('36c7012a4f5b40069bab68ae374e4f2e'))  
    #print("All creators:", get_all_creators())
    
for k, v in creators_db.items():
    if k == None:
        print(k, v)

print("ID of 'apfel':", get_creator_id('apfel'))
creators = get_all_creators()
    
print(len(creators))