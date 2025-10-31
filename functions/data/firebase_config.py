import pyrebase

firebaseConfig = {
    "apiKey": "AIzaSyCvNgRDVftYYYOO4NntYy6yjo9hUOrH_CU",
    "authDomain": "greenway-450aa.firebaseapp.com",
    "databaseURL": "https://greenway-450aa-default-rtdb.firebaseio.com",
    "projectId": "greenway-450aa",
    "storageBucket": "greenway-450aa.firebasestorage.app",
    "messagingSenderId": "107049448583",
    "appId": "1:107049448583:web:2f8a6eece8d2e21d913422"
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()
db = firebase.database()