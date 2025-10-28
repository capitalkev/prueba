// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCueVXr6zs8YXu56pwsNaY4hnZHe3dxa2c",
  authDomain: "operaciones-peru.firebaseapp.com",
  projectId: "operaciones-peru",
  storageBucket: "operaciones-peru.firebasestorage.app",
  messagingSenderId: "598125168090",
  appId: "1:598125168090:web:da14fa7bcf5df913146ce3",
  measurementId: "G-19XPBR134M"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();