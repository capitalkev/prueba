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

const NavigationSidebar = ({ user, handleLogout }) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const location = window.location.pathname;

    const toggleSidebar = () => setIsOpen(!isOpen);
    const closeSidebar = () => setIsOpen(false);

    return (
        <>
            {/* Botón Hamburger - Siempre visible */}
            <button
                onClick={toggleSidebar}
                className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg hover:bg-gray-100 transition-colors"
                title="Abrir menú"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 text-gray-700">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
            </button>

            {/* Overlay oscuro cuando el sidebar está abierto */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
                    onClick={closeSidebar}
                ></div>
            )}

            {/* Sidebar */}
            <aside
                className={`fixed top-0 left-0 h-full w-60 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
                    isOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                <div className="flex flex-col h-full">
                    {/* Header del Sidebar */}
                    <div className="flex items-center justify-between p-6 border-b">
                        <img src="/logo.png" alt="Capital Express" className="h-8
                        " />
                        <button
                            onClick={closeSidebar}
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Cerrar menú"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 text-gray-700">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Usuario Info */}
                    <div className="p-6 border-b bg-gray-50">
                        <p className="text-sm text-gray-600">Bienvenido,</p>
                        <p className="text-lg font-bold text-gray-900">{user.displayName?.split(' ')[0] || 'Usuario'}</p>
                    </div>

                    {/* Navegación */}
                    <nav className="flex-1 p-4 space-y-2">
                        <Link
                            to="/dashboard"
                            onClick={closeSidebar}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                                location === '/dashboard'
                                    ? 'bg-blue-600 text-white font-semibold'
                                    : 'text-gray-700 hover:bg-gray-100'
                            }`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                            </svg>
                            <span>Ventas</span>
                        </Link>

                        <Link
                            to="/gestion"
                            onClick={closeSidebar}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                                location === '/gestion'
                                    ? 'bg-blue-600 text-white font-semibold'
                                    : 'text-gray-700 hover:bg-gray-100'
                            }`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                            </svg>
                            <span>Gestión</span>
                        </Link>

                        <Link
                            to="/sunat"
                            onClick={closeSidebar}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                                location === '/sunat'
                                    ? 'bg-blue-600 text-white font-semibold'
                                    : 'text-gray-700 hover:bg-gray-100'
                            }`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                            </svg>
                            <span>SUNAT</span>
                        </Link>
                    </nav>

                    {/* Footer con botón de Logout */}
                    <div className="p-4 border-t">
                        <button
                            onClick={() => {
                                closeSidebar();
                                handleLogout();
                            }}
                            className="w-full px-4 py-3 bg-red-500 text-white rounded-lg text-sm font-semibold flex items-center justify-center gap-2 hover:bg-red-600 transition-colors"
                        >
                            <Icon name="LogOut" size={18} />
                            Cerrar Sesión
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
};

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
        {isAdmin && currentUser && <NavigationSidebar user={{displayName}} handleLogout={handleLogout} />}

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