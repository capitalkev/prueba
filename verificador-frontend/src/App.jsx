import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, Link } from 'react-router-dom';
import { signOut } from 'firebase/auth';
import { auth } from './firebase';
import { useAuth } from './context/AuthContext';

import NewOperationPage from './pages/NewOperationPage';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import Gestiones from './pages/Gestiones';
import SunatPage from './pages/SunatPage';
import { Icon } from './components/Icon';

const ProtectedRoute = ({ children }) => {
    const { currentUser } = useAuth();
    if (!currentUser) {
      return <Navigate to="/login" />;
    }
    return children;
};

const NavigationHeader = ({ user, handleLogout }) => (
    <header className="flex justify-between items-center p-4 bg-white shadow-md sticky top-0 z-10">
        <div className="flex items-center gap-4">
            <img src="/logo.png" alt="Capital Express" className="h-10" />
            <nav className="flex gap-4">
                {/* Estos links solo son visibles para el admin que puede ver ambas páginas */}
                <Link to="/dashboard" className="font-semibold text-gray-600 hover:text-blue-600">Ventas</Link>
                <Link to="/gestion" className="font-semibold text-gray-600 hover:text-blue-600">Gestión</Link>
            </nav>
        </div>
        <div className='flex items-center gap-2'>
          <p className='text-sm text-gray-600'>Bienvenido, <b>{user.displayName?.split(' ')[0] || 'Usuario'}</b></p>
          <button onClick={handleLogout} className="px-3 py-2 bg-red-500 text-white rounded-lg text-sm flex items-center gap-2">
              <Icon name="LogOut" size={16} /> Cerrar Sesión
          </button>
        </div>
    </header>
);

const AppContent = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  // Este useEffect maneja la redirección INICIAL después del login
  React.useEffect(() => {
    if (currentUser) {
        const currentPath = window.location.pathname;
        if (['/login', '/'].includes(currentPath)) {
            const role = currentUser.rol;
            if (role === 'admin' || role === 'gestion') {
                navigate('/gestion');
            } else { // 'ventas'
                navigate('/dashboard');
            }
        }
    } else if (window.location.pathname !== '/login') {
        navigate('/login');
    }
  }, [currentUser, navigate]);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate('/login');
    } catch (error) {
      console.error("Error al cerrar sesión:", error);
    }
  };
  
  // Si aún no tenemos la información del usuario, no renderizamos las rutas
  if (!currentUser && window.location.pathname !== '/login') {
      return null; // O un spinner de carga global
  }

  const userRole = currentUser ? currentUser.rol : null;
  const displayName = currentUser ? currentUser.nombre : 'Usuario';
  
  const isAdmin = userRole === 'admin';
  const canAccessVentas = userRole === 'ventas' || isAdmin;
  const canAccessGestion = userRole === 'gestion' || isAdmin;

  // Ruta por defecto a la que siempre volver si se intenta acceder a un lugar incorrecto
  const defaultRedirectPath = !currentUser
    ? '/login'
    : (isAdmin || userRole === 'gestion') ? '/gestion' : '/dashboard';

  return (
    <div className="min-h-screen bg-gray-50">
        {/* La barra de navegación solo la ve el admin, que es el único que necesita cambiar entre vistas */}
        {isAdmin && currentUser && <NavigationHeader user={{displayName}} handleLogout={handleLogout} />}

        <Routes>
            <Route path="/login" element={!currentUser ? <LoginPage /> : <Navigate to={defaultRedirectPath} />} />
            
            {/* RUTA DASHBOARD (VENTAS) */}
            <Route path="/dashboard" element={
                <ProtectedRoute>
                    {canAccessVentas ? <Dashboard handleLogout={handleLogout} isAdmin={isAdmin} /> : <Navigate to={defaultRedirectPath} />}
                </ProtectedRoute>
            }/>

            {/* RUTA GESTIONES (GESTIÓN) */}
            <Route path="/gestion" element={
                <ProtectedRoute>
                    {canAccessGestion ? <Gestiones handleLogout={handleLogout} isAdmin={isAdmin} /> : <Navigate to={defaultRedirectPath} />}
                </ProtectedRoute>
            }/>
            
            {/* RUTA NUEVA OPERACIÓN (VENTAS) */}
            <Route path="/new-operation" element={
                <ProtectedRoute>
                    {canAccessVentas ? <NewOperationPage /> : <Navigate to={defaultRedirectPath} />}
                </ProtectedRoute>
            }/>

            {/* RUTA SOFTWARE SUNAT */}
            <Route path="/sunat" element={
                <ProtectedRoute>
                    <SunatPage />
                </ProtectedRoute>
            }/>

            {/* CUALQUIER OTRA RUTA */}
            <Route path="*" element={<Navigate to={defaultRedirectPath} />} />
        </Routes>
    </div>
  );
};

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}