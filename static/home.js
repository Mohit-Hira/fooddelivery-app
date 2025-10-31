import { initializeApp, getApps, getApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// ---------------- FIREBASE CONFIG ----------------
const firebaseConfig = {
  apiKey: "AIzaSyBZegGPZx6MvrNvRQsFCvx2qkJ62oIkULM",
  authDomain: "mohit-45547.firebaseapp.com",
  projectId: "mohit-45547",
  storageBucket: "mohit-45547.firebasestorage.app",
  messagingSenderId: "778528943574",
  appId: "1:778528943574:web:ccd84ce0fad485619b0877",
  measurementId: "G-ES0PK3WFT3"
};

// ---------------- INITIALIZE FIREBASE ----------------
const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);

// ---------------- ON PAGE LOAD ----------------
document.addEventListener("DOMContentLoaded", () => {

  // ✅ No redirect loop: backend handles protection for /home
  onAuthStateChanged(auth, user => {
    if (user) {
      console.log("✅ Firebase user authenticated:", user.email);
    } else {
      console.log("⚠️ No Firebase user (but backend may still allow session)");
    }
  });

  // ---------------- LOGOUT ----------------
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await signOut(auth);
        // Clear backend session cookie
        await fetch("/logout", { method: "POST" });
        window.location.href = "/";
      } catch (err) {
        console.error("Logout error:", err);
        alert("Logout failed. Please try again.");
      }
    });
  }

  // ---------------- TABS ----------------
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      // (optional) Add filtering for delivery/pickup here
    });
  });

  // ---------------- SEARCH ----------------
  const searchInput = document.getElementById("search-input");
  const restaurantGrid = document.getElementById("restaurant-grid");

  if (searchInput && restaurantGrid) {
    searchInput.addEventListener("input", () => {
      const query = searchInput.value.toLowerCase();
      const cards = restaurantGrid.querySelectorAll(".restaurant-card");
      cards.forEach(card => {
        const name = card.querySelector("h4").textContent.toLowerCase();
        const cuisine = card.querySelector("p").textContent.toLowerCase();
        card.style.display =
          name.includes(query) || cuisine.includes(query) ? "" : "none";
      });
    });
  }

  // ---------------- CHANGE LOCATION ----------------
  const changeLocBtn = document.getElementById("change-location");
  const locText = document.getElementById("location-text");

  if (changeLocBtn && locText) {
    changeLocBtn.addEventListener("click", () => {
      const newLoc = prompt("Enter new location:", locText.textContent);
      if (newLoc) locText.textContent = newLoc;
    });
  }
});
