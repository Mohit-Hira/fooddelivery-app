import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, sendPasswordResetEmail, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyBZegGPZx6MvrNvRQsFCvx2qkJ62oIkULM",
  authDomain: "mohit-45547.firebaseapp.com",
  projectId: "mohit-45547",
  storageBucket: "mohit-45547.firebasestorage.app",
  messagingSenderId: "778528943574",
  appId: "1:778528943574:web:ccd84ce0fad485619b0877",
  measurementId: "G-ES0PK3WFT3"
};

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);

let cart = [];
const menuItems = [
    {id:1,name:"Pizza",price:9.99,img:"/static/images/pizza.jpg"},
    {id:2,name:"Burger",price:5.99,img:"/static/images/burger.jpg"},
    {id:3,name:"Sushi",price:12.99,img:"/static/images/sushi.jpg"}
];

// ---------- AUTH FUNCTIONS ----------
function showMessage(msg, isError = true) {
    const el = document.getElementById("message");
    if(el) { el.textContent = msg; el.style.color = isError ? "red" : "green"; }
}

async function sendTokenToBackend(idToken) {
    await fetch("/sessionLogin", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ idToken }) });
}

// Login & Signup
document.getElementById("login-btn")?.addEventListener("click", async () => {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    if (!email || !password) return showMessage("Enter email & password!");
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const token = await userCredential.user.getIdToken(true);
        await sendTokenToBackend(token);
        showMessage("Logged in successfully!", false);
        // ✅ FIXED REDIRECT
        window.location.href = "/home";
    } catch (err) {
        showMessage("Login error: " + err.message);
    }
});

document.getElementById("signup-btn")?.addEventListener("click", async () => {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    if (!email || !password) return showMessage("Enter email & password!");
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const token = await userCredential.user.getIdToken(true);
        await sendTokenToBackend(token);
        showMessage("Account created successfully!", false);
        window.location.href = "/home";
    } catch (err) { showMessage("Signup error: " + err.message); }
});

// Forgot password
document.getElementById("forgot-link")?.addEventListener("click", async (e) => {
    e.preventDefault();
    const email = prompt("Enter your registered email:");
    if (!email) return showMessage("Email is required!");
    try { await sendPasswordResetEmail(auth, email); showMessage("Password reset email sent!", false); }
    catch (err) { showMessage("Error: " + err.message); }
});

// Logout
document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        const res = await fetch("/logout", { method: "GET" });
        // Redirect to sign-in page
        window.location.href = "/signin";
      } catch (err) {
        console.error("Logout failed:", err);
      }
    });
  }
});


// ---------- CART FUNCTIONS ----------
const menuDiv = document.getElementById("menu");
if(menuDiv){
    menuItems.forEach(item => {
        const div = document.createElement("div");
        div.className = "menu-item";
        div.innerHTML = `<img src="${item.img}" alt="${item.name}"><h4>${item.name}</h4><p>$${item.price}</p><button data-id="${item.id}">Add to Cart</button>`;
        menuDiv.appendChild(div);
    });

    menuDiv.addEventListener("click", e => {
        if(e.target.tagName === "BUTTON"){
            const id = parseInt(e.target.dataset.id);
            const item = menuItems.find(i => i.id === id);
            const existing = cart.find(c => c.id === id);
            if(existing) existing.qty++;
            else cart.push({...item, qty:1});
            updateCart();
        }
    });
}

function updateCart(){
    const ul = document.getElementById("cart-items");
    ul.innerHTML = "";
    let total = 0;
    cart.forEach(i => {
        total += i.price * i.qty;
        const li = document.createElement("li");
        li.textContent = `${i.name} x${i.qty} - $${(i.price*i.qty).toFixed(2)}`;
        ul.appendChild(li);
    });
    document.getElementById("total-price").textContent = total.toFixed(2);
}

document.getElementById("checkout")?.addEventListener("click", async () => {
    if(cart.length === 0){ alert("Cart empty"); return; }
    const token = await auth.currentUser.getIdToken();
    const res = await fetch("/api/orders", {
        method:"POST",
        headers:{"Authorization": `Bearer ${token}`, "Content-Type":"application/json"},
        body: JSON.stringify({ items: cart, total: cart.reduce((s,i)=>s+i.price*i.qty,0) })
    });
    const data = await res.json();
    if(data.ok){ alert("Order placed!"); cart=[]; updateCart(); }
    else alert("Order failed!");
});

