import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  sendPasswordResetEmail
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

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

// Initialize Firebase
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);

let cart = [];
const menuItems = [
  {id:1,name:"Pizza",price:9.99,img:"/static/images/pizza.jpg"},
  {id:2,name:"Burger",price:5.99,img:"/static/images/burger.jpg"},
  {id:3,name:"Sushi",price:12.99,img:"/static/images/sushi.jpg"}
];

// Auth check
onAuthStateChanged(auth, user => {
  if(!user) window.location.href = "/";
});

// Logout
document.getElementById("logout-btn").addEventListener("click", async ()=>{
  await signOut(auth);
  window.location.href = "/";
});

// Render menu
const menuDiv = document.getElementById("menu");
menuItems.forEach(item=>{
  const div = document.createElement("div");
  div.className="menu-item";
  div.innerHTML=`<img src="${item.img}" alt="${item.name}"><h4>${item.name}</h4><p>$${item.price}</p><button data-id="${item.id}">Add to Cart</button>`;
  menuDiv.appendChild(div);
});

// Add to cart
menuDiv.addEventListener("click", e=>{
  if(e.target.tagName==="BUTTON"){
    const id = parseInt(e.target.dataset.id);
    const item = menuItems.find(i=>i.id===id);
    const existing = cart.find(c=>c.id===id);
    if(existing) existing.qty++;
    else cart.push({...item,qty:1});
    updateCart();
  }
});

function updateCart(){
  const ul = document.getElementById("cart-items");
  ul.innerHTML="";
  let total=0;
  cart.forEach(i=>{
    total+=i.price*i.qty;
    const li=document.createElement("li");
    li.textContent=`${i.name} x${i.qty} - $${(i.price*i.qty).toFixed(2)}`;
    ul.appendChild(li);
  });
  document.getElementById("total-price").textContent=total.toFixed(2);
}

// Checkout
document.getElementById("checkout").addEventListener("click", async ()=>{
  if(cart.length===0){ alert("Cart empty"); return; }
  const token = await auth.currentUser.getIdToken();
  const res = await fetch("/api/orders",{
    method:"POST",
    headers:{ "Authorization": `Bearer ${token}`, "Content-Type":"application/json" },
    body:JSON.stringify({items:cart,total:cart.reduce((s,i)=>s+i.price*i.qty,0)})
  });
  const data = await res.json();
  if(data.ok){
    alert("Order placed successfully!");
    cart=[];
    updateCart();
  }else alert("Order failed!");
});
