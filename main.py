import os
import random
from fastapi import FastAPI, Request, Depends, HTTPException, status, UploadFile, File,WebSocket, WebSocketDisconnect,Form
from fastapi.responses import HTMLResponse, RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from firebase_admin import auth
from auth import verify_firebase_token
from google.cloud import firestore,storage
from db import list_restaurants, get_restaurant, create_order, upload_image_to_bucket,update_user_profile
from datetime import datetime
from google.oauth2 import service_account

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
PROJECT = "examples-471711"  # Your Firebase/Google Cloud Project ID
BUCKET_NAME = "examples-471711.appspot.com"  # Your storage bucket

# Initialize Firestore and Storage clients
firestore_client = firestore.Client(project=PROJECT)
storage_client = storage.Client(project=PROJECT)




cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not cred_json:
    raise RuntimeError("Firestore credentials not set! Add GOOGLE_APPLICATION_CREDENTIALS_JSON in Render Secrets.")

credentials = service_account.Credentials.from_service_account_info(json.loads(cred_json))
firestore_client = firestore.Client(credentials=credentials)



# -------------------------------
# Public Routes
# -------------------------------

@app.get("/", response_class=HTMLResponse)
async def root():
    """Always redirect to login page"""
    return RedirectResponse(url="/signin", status_code=302)


@app.get("/signin", response_class=HTMLResponse)
async def signin(request: Request):
    """Firebase login page"""
    return templates.TemplateResponse("auth.html", {"request": request})





# -------------------------------
# Firebase Session Handling
# -------------------------------

# ------------------- SESSION LOGIN -------------------
@app.post("/sessionLogin")
async def session_login(request: Request):
    """Verify Firebase ID token and create session cookie"""
    data = await request.json()
    id_token = data.get("idToken")

    if not id_token:
        raise HTTPException(status_code=400, detail="Missing ID token")

    try:
        # Verify ID token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token["uid"]

        # Create a secure cookie to store the token (httponly + samesite)
        response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="token",
            value=id_token,           # Store the ID token in cookie
            httponly=True,
            secure=True,             # Ensure HTTPS in production
            samesite="Lax",
        )
        print(f"✅ Firebase token verified for UID: {uid}")
        return response

    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {e}")


@app.get("/logout")
async def logout():
    """Clear session and redirect to signin"""
    response = RedirectResponse(url="/signin", status_code=302)
    response.delete_cookie("firebase_uid")
    return response


# -------------------------------
# Protected Routes
# -------------------------------
restaurants = [
    {"id": 1, "name": "Burger Deluxe", "price": 1200, "category": "meals", "photo_url": "/static/images/burger.jpg"},
    {"id": 2, "name": "Fried Plantain", "price": 300, "category": "sides", "photo_url": "/static/images/burger.jpg"},
    {"id": 3, "name": "Chips & Dip", "price": 500, "category": "snacks", "photo_url": "/static/images/burger.jpg"},
    {"id": 4, "name": "Grilled Chicken", "price": 1500, "category": "meals", "photo_url": "/static/images/burger.jpg"},
    {"id": 5, "name": "Coleslaw", "price": 800, "category": "sides", "photo_url": "/static/images/burger.jpg"},
    {"id": 6, "name": "Popcorn", "price": 400, "category": "snacks", "photo_url": "/static/images/burger.jpg"},]
@app.get("/home")
async def home_page(request: Request):
    featured = restaurants[:3]
    categories = [
        {"name": "Combo", "key": "meals"},
        {"name": "Sweet Dish", "key": "sides"},
        {"name": "Snake", "key": "snacks"}
    ]
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "restaurants": restaurants, "featured": featured, "categories": categories}
    )

@app.post("/api/orders")
async def create_order_api(request: Request, token_user=Depends(verify_firebase_token)):
    """Create order endpoint (Firebase protected)"""
    data = await request.json()
    order = create_order(user=token_user, order_data=data)
    return {"ok": True, "order_id": order["id"]}


@app.post("/api/upload-image")
async def upload_image_api(file: UploadFile = File(...), token_user=Depends(verify_firebase_token)):
    """Upload image (for owners/admins)"""
    url = upload_image_to_bucket(file)
    return {"url": url}
@app.get("/menu", response_class=HTMLResponse)
async def menu_page(request: Request, user=Depends(verify_firebase_token)):
    """Menu page showing all restaurants / food items"""
    restaurants = list_restaurants()  # Returns a list of dicts
    return templates.TemplateResponse(
        "menu.html",
        {
            "request": request,
            "restaurants": restaurants,
            "user": user,  # Optional: can use for greeting, etc.
        }
    )
# Keep track of active connections
# ---------------- WebSocket Manager ----------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()


# ---------------- Chat Page ----------------
@app.get("/chat")
async def chat_page(request: Request, user=Depends(verify_firebase_token)):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})


# ---------------- WebSocket ----------------
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            user_message = await websocket.receive_text()
            await manager.send_personal_message(f"You: {user_message}", websocket)

            # Generate a single AI response
            ai_message = await generate_ai_reply(user_message)
            await manager.send_personal_message(f"AI: {ai_message}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


## ---------------- AI Logic ----------------
async def generate_ai_reply(user_message: str):
    """
    Generate a single random AI reply locally (no OpenAI API needed).
    """
    # Default random responses
    responses = [
        "I'm here to help you with your order!",
        "Have you checked our combo meals today?",
        "Remember, you can add items to your favorites ❤️",
        "Would you like a recommendation?",
        "Our special today is Grilled Chicken 🍗",
        "Don't forget to check our desserts section 🍰",
        "Please contact customer care at 📞 123-456-7890 if needed."
    ]

    # If user mentions a complaint, give a specific response
    if "complain" in user_message.lower() or "issue" in user_message.lower():
        return "⚠️ Sorry, we couldn't process your request. Please contact customer care at 📞 123-456-7890."

    # Otherwise, pick one random response
    return random.choice(responses)
@app.get("/favorites", response_class=HTMLResponse)
def favorites_page(request: Request, user=Depends(verify_firebase_token)):

    favorite_ids = ["rest1", "rest3"]  # Replace with real user favorites

    # Get restaurant details
    all_restaurants = list_restaurants()
    favorites = [r for r in all_restaurants if r["id"] in favorite_ids]

    return templates.TemplateResponse(
        "favorites.html",
        {
            "request": request,
            "favorites": favorites,
            "user": user
        }
    )
# ---------------- Profile Page ----------------

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, token_user=Depends(verify_firebase_token)):
    """
    Show profile page with user info from Firestore.
    """
    uid = token_user["uid"]
    doc = firestore_client.collection("users").document(uid).get()
    user_data = doc.to_dict() or {}

    # Convert timestamps to ISO string
    for key, value in user_data.items():
        if isinstance(value, datetime):
            user_data[key] = value.isoformat()

    user_data["uid"] = uid

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user_data}
    )
@app.post("/api/profile/update")
async def update_profile(
    name: str = Form(...),
    file: UploadFile = File(None),
    user=Depends(verify_firebase_token)
):
    """
    Update user's profile info: name and optionally profile photo.
    """
    uid = user["uid"]
    photo_url = upload_image_to_bucket(file) if file else None
    updated_user = update_user_profile(uid, name, photo_url)

    return JSONResponse({"ok": True, "user": updated_user})

restaurants = [
    {"id": 1, "name": "Burger Deluxe", "price": 1200, "category": "meals", "photo_url": "/static/images/burger.jpg"},
    {"id": 2, "name": "Fried Plantain", "price": 300, "category": "sides", "photo_url": "/static/images/pizza.jpg"},
    {"id": 3, "name": "Chips & Dip", "price": 500, "category": "snacks", "photo_url": "/static/images/food.jpg"},
    {"id": 4, "name": "Grilled Chicken", "price": 1500, "category": "meals", "photo_url": "/static/images/sushi.jpg"},
    {"id": 5, "name": "Coleslaw", "price": 800, "category": "sides", "photo_url": "/static/images/pizza.jpg"},
    {"id": 6, "name": "Popcorn", "price": 400, "category": "snacks", "photo_url": "/static/images/sushi.jpg"}
]

async def menu_page(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request, "restaurants": restaurants})
@app.get("/cart", response_class=HTMLResponse)
async def cart_page(request: Request, user=Depends(verify_firebase_token)):
    """Cart page showing current items"""
    return templates.TemplateResponse("cart.html", {"request": request, "user": user})
