import firebase_admin
from firebase_admin import credentials
import requests
import time


cred = credentials.Certificate("/home/admin/Project/webserber/disaster-management-c53b3-firebase-adminsdk-x1j9h-228350f939.json")
default_app = firebase_admin.initialize_app(cred)

from firebase_admin import firestore
db = firestore.client()


def fetchFromDB(index):

    # Define the URL for the Flask server
    url = f'http://172.20.10.2:5000/get_data/{index}'

    # timestamp, edge_name, data = data.split(',')

   

    # # Data for the new Edge
    try:
        # Send a POST request to add the new Edge
        response = requests.get(url)
        if response.status_code == 200:

            doc = response.json()
            print(doc)
            db.collection("Edge").document(str(doc['id'])).set(doc)
            return index + 1
        else:
            print(f"Error: {response.status_code}")
            return index
    except:
        print("Error")
        return index
    # # Print the response
    # for doc in docs:
    #     db.collection("Edge").document(str(doc['id'])).set(doc)
    #     print(doc)
    #     time.sleep(1)
        
# while True :         
#     fetchFromDB(index)
#     index = index + 1
#     time.sleep(1)