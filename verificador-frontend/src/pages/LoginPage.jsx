import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { signInWithPopup, signOut } from 'firebase/auth';
import { auth, googleProvider } from '../firebase';
import { Icon } from '../components/Icon';
import logo from '/logo.png';

const ErrorMessage = ({ message }) => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative text-center"
    role="alert"
  >
    <span className="block sm:inline">{message}</span>
  </motion.div>
);

export default function LoginPage() {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      
      const allowedDomains = ['@capitalexpress.cl', '@capitalexpress.pe'];
      const userDomain = user.email.substring(user.email.lastIndexOf("@"));

      if (!allowedDomains.includes(userDomain)) {
        await signOut(auth);
        setError('Acceso denegado. Solo se permiten correos de los dominios permitidos.');
      }
      // La redirección y el manejo de roles ahora se harán en App.jsx
    } catch (error) {
      console.error("Error durante el inicio de sesión con Google:", error);
      if (error.code !== 'auth/popup-closed-by-user') {
        setError('Falló la autenticación con Google. Por favor, intenta de nuevo.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-white to-gray-100 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md bg-white shadow-xl border border-gray-200 rounded-2xl p-8 space-y-6"
      >
        <div className="flex justify-center">
          <img src={logo} alt="Capital Express" className="h-14" />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800">Acceso al Portal de Verificaciones</h1>
          <p className="text-sm text-gray-500 mt-2">
            Inicia sesión con tu correo{" "}
            <span className="text-[#f24123] font-medium">@capitalexpress.pe</span> o{" "}
            <span className="text-[#f24123] font-medium">@capitalexpress.cl</span>
          </p>
        </div>

        {error && <ErrorMessage message={error} />}

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={handleGoogleLogin}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-3 bg-[#f24123] hover:bg-[#d6361b] text-white font-semibold px-4 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Icon name="Loader" className="animate-spin w-5 h-5" />
          ) : (
            <Icon name="KeyRound" className="w-5 h-5" />
          )}
          {isLoading ? "Verificando..." : "Iniciar sesión con Google"}
        </motion.button>

        <p className="text-center text-xs text-gray-400 pt-4">
          Capital Express &copy; {new Date().getFullYear()}
        </p>
      </motion.div>
    </div>
  );
}