import os
import uuid
from datetime import datetime
from google.cloud import firestore, storage

# ---------------------------
# Google Cloud Project Config
# ---------------------------
PROJECT = "examples-471711"  # Your Firebase/Google Cloud Project ID
BUCKET_NAME = "examples-471711.appspot.com"  # Your storage bucket

# Initialize Firestore and Storage clients
firestore_client = firestore.Client(project=PROJECT)
storage_client = storage.Client(project=PROJECT)


# ---------------------------
# Restaurants & Orders
# ---------------------------
def list_restaurants():
    docs = firestore_client.collection("restaurants").stream()
    restaurants = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        restaurants.append(data)
    return restaurants


def get_restaurant(restaurant_id: str):
    doc = firestore_client.collection("restaurants").document(restaurant_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data

def create_order(user, order_data):
    restaurant_id = order_data.get("restaurant_id", "unknown")
    items = order_data.get("items", [])
    total = order_data.get("total", sum(item.get("price", 0) for item in items))

    order_ref = firestore_client.collection("orders").document()
    payload = {
        "user_uid": user["uid"],
        "user_email": user.get("email"),
        "restaurant_id": restaurant_id,
        "items": items,
        "total": total,
        "status": "received",
        "created_at": datetime.utcnow(),
    }
    order_ref.set(payload)
    payload["id"] = order_ref.id
    return payload


# ---------------------------
# Upload image to GCS
# ---------------------------
def upload_image_to_bucket(upload_file):
    """
    Upload file to Google Cloud Storage and return public URL
    """
    if not upload_file:
        return None

    bucket = storage_client.bucket(BUCKET_NAME)
    ext = upload_file.filename.split(".")[-1]
    blob_name = f"images/{uuid.uuid4()}.{ext}"
    blob = bucket.blob(blob_name)

    blob.upload_from_file(upload_file.file, content_type=upload_file.content_type)
    blob.make_public()  # Make the image public

    return blob.public_url


# ---------------------------
# Update user profile
# ---------------------------

def update_user_profile(uid: str, name: str, photo_url: str = None):
    """
    Update Firestore user document and return a JSON-serializable dict
    """
    doc_ref = firestore_client.collection("users").document(uid)
    update_data = {"name": name}
    if photo_url:
        update_data["photo_url"] = photo_url
    doc_ref.set(update_data, merge=True)

    # Get the updated document
    doc = doc_ref.get()
    user_data = doc.to_dict() or {}

    # Convert all Firestore timestamp fields to ISO strings
    for key, value in user_data.items():
        if isinstance(value, datetime):
            user_data[key] = value.isoformat()

    user_data["uid"] = uid
    return user_data
