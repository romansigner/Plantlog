from app import db 
from modules import User, Plant, Entry  

db.create_all()

print("Datenbank wurde erfolgreich erstellt.")
