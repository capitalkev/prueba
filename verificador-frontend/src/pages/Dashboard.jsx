import React, { useState, useMemo, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom'; // <-- Import ReactDOM for portals
import * as LucideIcons from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { formatInPeruTimeZone } from '../utils/dateFormatter';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config/api';

// --- Componente Envoltorio para Iconos (Wrapper) ---
const Icon = ({ name, size = 16, ...props }) => {
    const iconMap = { ...LucideIcons, HelpCircle: LucideIcons.HelpCircle };
    const LucideIcon = iconMap[name];
    if (!LucideIcon) {
        return <LucideIcons.HelpCircle size={size} {...props} />;
    }
    return <LucideIcon size={size} {...props} className={`inline-block flex-shrink-0 ${props.className || ''}`} />;
};

const Card = React.forwardRef(({ children, className = "", ...props }, ref) => (
    <div ref={ref} className={`bg-white rounded-xl shadow-lg border border-gray-200/80 ${className}`} {...props}>{children}</div>
));
const CardHeader = ({ children, className = "" }) => <div className={`p-5 border-b border-gray-200/80 ${className}`}>{children}</div>;
const CardTitle = ({ children, className = "" }) => <h3 className={`text-base font-semibold text-gray-800 ${className}`}>{children}</h3>;
const CardDescription = ({ children, className = "" }) => <p className={`text-sm text-gray-500 ${className}`}>{children}</p>;
const CardContent = ({ children, className = "" }) => <div className={`p-5 ${className}`}>{children}</div>;

const Button = React.forwardRef(({ className = "", variant = "default", size="default", children, iconName, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-60 disabled:pointer-events-none";
    const variants = {
        default: "bg-blue-600 text-white shadow-sm hover:bg-blue-700",
        destructive: "bg-red-600 text-white shadow-sm hover:bg-red-700",
        outline: "border border-gray-300 bg-transparent hover:bg-gray-100 text-gray-700",
        ghost: "hover:bg-gray-100 text-gray-800",
        success: "bg-green-600 text-white hover:bg-green-700",
    };
    const sizes = { default: "h-10 px-4 py-2", sm: "h-9 px-3", xs: "h-7 px-2 text-xs" };
    return <button ref={ref} className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>{iconName && <Icon name={iconName} size={16} className="mr-1"/>}{children}</button>;
});

const Badge = ({ variant, iconName, children, className="", animate=false }) => {
    const variants = {
        success: "bg-green-100 text-green-800",
        warning: "bg-yellow-100 text-yellow-800",
        error: "bg-red-100 text-red-800",
        info: "bg-blue-100 text-blue-800",
        neutral: "bg-gray-100 text-gray-700",
    };
    return (
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${variants[variant]} ${className}`}>
            {iconName && <Icon name={iconName} size={14} className={animate ? 'animate-spin' : ''}/>}
            {children}
        </div>
    );
};

const Modal = ({ isOpen, onClose, title, children, size = "lg" }) => {
    if (!isOpen) return null;
    const sizeClasses = { md: "max-w-xl", lg: "max-w-3xl", xl: "max-w-5xl" };
    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className={`bg-white rounded-xl shadow-2xl w-full ${sizeClasses[size] || sizeClasses.lg}`} onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center p-4 border-b border-gray-200">
                    <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}><Icon name="X" size={20}/></Button>
                </div>
                <div className="p-6 max-h-[75vh] overflow-y-auto">{children}</div>
            </div>
        </div>
    );
};

const ProgressBar = ({ value, max, colorClass="bg-blue-500" }) => {
    const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    return (
        <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1 overflow-hidden">
            <div className={`${colorClass} h-2.5 rounded-full transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
        </div>
    );
};

const SugerenciasIA = ({ operaciones }) => {
    const operacionesAntiguas = operaciones.filter(op => {
        const antiquity = Math.ceil(Math.abs(new Date() - new Date(op.fechaIngreso)) / (1000 * 60 * 60 * 24)) || 0;
        return antiquity > 15 && op.estado === "En Verificación";
    });

    if (operacionesAntiguas.length === 0) return null;

    return (
        <Card className="bg-blue-50 border-blue-200 mb-8">
            <CardContent className="flex items-start gap-4 p-4">
                <Icon name="Lightbulb" size={24} className="text-blue-600 mt-1"/>
                <div>
                    <h4 className="font-semibold text-blue-800">Sugerencias del Día por IA ✨</h4>
                    <p className="text-sm text-blue-700/90">
                        Hola, tienes <strong className="font-bold">{operacionesAntiguas.length} {operacionesAntiguas.length > 1 ? 'operaciones' : 'operación'} con más de 15 días de antigüedad</strong>. Considera priorizar la gestión de {operacionesAntiguas.map(op => <strong key={op.id} className="font-bold">{op.id}</strong>).reduce((prev, curr) => [prev, ', ', curr])}.
                    </p>
                </div>
            </CardContent>
        </Card>
    );
};

const GaugeChart = ({ value, max, label }) => {
    const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    const strokeWidth = 10;
    const radius = 50;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
        <div className="relative flex flex-col items-center justify-center">
            <svg width="140" height="140" viewBox="0 0 120 120" className="-rotate-90">
                <circle cx="60" cy="60" r={radius} fill="none" strokeWidth={strokeWidth} className="stroke-gray-200" />
                <circle
                    cx="60"
                    cy="60"
                    r={radius}
                    fill="none"
                    strokeWidth={strokeWidth}
                    className="stroke-purple-600"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
                />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-purple-700">{percentage.toFixed(0)}%</span>
                <span className="text-xs text-gray-500">{label}</span>
            </div>
        </div>
    );
};

const MetasDashboard = ({ kpis }) => (
    <Card>
        <CardHeader>
            <CardTitle className="flex items-center gap-2"><Icon name="Target" className="text-purple-600"/>Meta de Colocación Mensual</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-4">
            <GaugeChart value={kpis.colocacionMensual} max={kpis.metaColocacion} label="Completado" />
            <div className="text-center">
                <p className="text-lg font-semibold text-gray-800">S/ {kpis.colocacionMensual.toLocaleString('es-PE')}</p>
                <p className="text-sm text-gray-500">En Proceso</p> {/*de tu meta de S/ {kpis.metaColocacion.toLocaleString('es-PE')}*/}
            </div>
        </CardContent>
    </Card>
);

const EstadisticasClave = ({ operations }) => {
    const verificadas = operations.filter(op => op.estado === 'Verificada').length;
    const rechazadas = operations.filter(op => op.estado === 'Rechazada').length;
    const totalGestionadas = verificadas + rechazadas;

    const stats = [
        { icon: "Clock", label: "Tiempo Prom. de Curse", value: "En Proceso", color: "text-blue-600" },
        { icon: "CheckCircle", label: "Operaciones Verificadas", value: "En Proceso" , color: "text-green-600" }, //{/*verificadas*/}
        { icon: "TrendingUp", label: "Tasa de Aprobación", value: "En Proceso", color: "text-indigo-600" } //`${tasaAprobacion}%`
    ];

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2"><Icon name="BarChart2" className="text-gray-500"/>Estadísticas Clave</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {stats.map(stat => (
                    <div key={stat.label} className="flex justify-between items-center text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                           <Icon name={stat.icon} size={16} className={stat.color} />
                           <span>{stat.label}</span>
                        </div>
                        <span className="font-semibold text-gray-800">{stat.value}</span>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
};

const LogroDestacado = ({ logro }) => {
    if (!logro) return null;

    return (
        <Card className="bg-gradient-to-tr from-yellow-50 to-amber-100 border-yellow-200">
            <CardContent className="flex items-center gap-4 p-4">
                 <div className={`flex-shrink-0 h-12 w-12 rounded-lg flex items-center justify-center ${logro.colorClass}`}>
                    <span className="text-2xl">{logro.emoji}</span>
                </div>
                <div>
                    <p className="font-bold text-yellow-900">{logro.titulo}</p>
                    <p className="text-sm text-yellow-800/90">{logro.descripcion}</p>
                </div>
            </CardContent>
        </Card>
    );
};

const VistaResumenSemanal = ({ kpis, operations, onClose }) => {
    const weeklyGoal = kpis.metaColocacion / 4;
    const getWeekNumber = (d) => {
        d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    };
    const latestDate = new Date(Math.max.apply(null, operations.map(op => new Date(op.fechaIngreso))));
    const currentWeek = getWeekNumber(latestDate);
    const currentYear = latestDate.getUTCFullYear();
    const opsThisWeek = operations.filter(op => {
        const opDate = new Date(op.fechaIngreso);
        return getWeekNumber(opDate) === currentWeek && opDate.getUTCFullYear() === currentYear;
    });
    const verifiedOpsThisWeek = opsThisWeek.filter(op => op.estado === "Verificada");
    const weeklyPlacement = verifiedOpsThisWeek.reduce((sum, op) => sum + (op.moneda === "PEN" ? op.monto : op.monto * 3.75), 0);
    const checkListItems = [
        { text: `Has ingresado ${opsThisWeek.length} nuevas operaciones.`, achieved: opsThisWeek.length > 0 },
        { text: `Lograste verificar ${verifiedOpsThisWeek.length} operaciones.`, achieved: verifiedOpsThisWeek.length > 0 },
        { text: `Colocaste S/ ${weeklyPlacement.toLocaleString('es-PE')} esta semana.`, achieved: weeklyPlacement > 10000 },
        { text: "¡Tu racha de 0 rechazos esta semana continúa!", achieved: !opsThisWeek.some(op => op.estado === "Rechazada") },
    ];

    return (
        <Card className="bg-gradient-to-br from-purple-50 via-white to-blue-50 border-purple-200/80 mb-8 transition-all duration-300 ease-in-out">
            <CardHeader className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                    <Icon name="TrendingUp" className="text-purple-600" />
                    Tu Resumen Semanal
                </CardTitle>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
                    <Icon name="X" size={20} />
                </Button>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <div className="flex justify-between items-baseline">
                        <p className="text-sm text-gray-600">Progreso meta semanal: EN PROCESO</p>
                        <p className="text-sm font-medium text-purple-700">
                            {((weeklyPlacement / weeklyGoal) * 100).toFixed(0)}%
                        </p>
                    </div>
                    <ProgressBar value={weeklyPlacement} max={weeklyGoal} colorClass="bg-purple-500" />
                    <p className="text-xs text-center text-gray-500 mt-1"> EN PROCESO
                        {/*S/ {weeklyPlacement.toLocaleString('es-PE')} de S/ {weeklyGoal.toLocaleString('es-PE')} */}
                    </p>
                </div>
                <div>
                    <h5 className="font-semibold text-sm text-gray-800 mb-2">Checklist de Logros de la Semana:</h5>
                    <ul className="space-y-2">
                        {checkListItems.filter(item => item.achieved).map((item, index) => (
                            <li key={index} className="flex items-center gap-2 text-sm text-gray-700">
                                <Icon name="CheckCircle2" className="text-green-500 flex-shrink-0" size={16} />
                                <span>{item.text}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            </CardContent>
        </Card>
    );
};

const NotificationDropdown = ({ notifications, onClose }) => {
    const dropdownRef = useRef(null);
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                onClose();
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [onClose]);
    
    const iconMap = { success: "CheckCircle", info: "MessageSquare", warning: "AlertTriangle" };
    const colorMap = { success: "text-green-500", info: "text-blue-500", warning: "text-orange-500" };

    return (
        <div ref={dropdownRef} className="origin-top-right absolute right-0 mt-2 w-80 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
            <div className="p-2">
                <div className="px-2 py-1 font-semibold text-sm">Notificaciones</div>
                <ul className="max-h-80 overflow-y-auto">
                    {notifications.map(notif => (
                        <li key={notif.id} className="p-2 hover:bg-gray-100 rounded-md">
                            <div className="flex items-start gap-3">
                                <Icon name={iconMap[notif.type]} className={colorMap[notif.type]} size={20} />
                                <div className="text-xs">
                                    <p className="text-gray-800" dangerouslySetInnerHTML={{__html: notif.message}}></p>
                                    <p className="text-gray-400">{notif.time}</p>
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

const ProcessTimeline = ({ steps, currentStep }) => (
    <div>
        <h4 className="font-semibold text-gray-700 mb-3">Línea de Tiempo del Proceso</h4>
        <div className="flex justify-between items-center text-xs">
            {steps.map((step, index) => {
                const stepIndex = steps.indexOf(step);
                const currentStepIndex = steps.indexOf(currentStep);
                const isCompleted = stepIndex < currentStepIndex;
                const isCurrent = step === currentStep;
                const color = isCompleted ? 'bg-green-500' : isCurrent ? 'bg-blue-500' : 'bg-gray-300';
                const iconName = isCompleted ? 'Check' : 'HelpCircle';
                
                return (
                    <React.Fragment key={step}>
                        <div className="flex flex-col items-center text-center w-20">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${color} ${isCurrent ? 'ring-4 ring-blue-200' : ''}`}>
                                <Icon name={iconName} size={16}/>
                            </div>
                            <p className={`mt-1 font-semibold ${isCurrent ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-400'}`}>{step}</p>
                        </div>
                        {index < steps.length - 1 && <div className={`flex-1 h-0.5 ${isCompleted ? 'bg-green-500' : 'bg-gray-300'}`}></div>}
                    </React.Fragment>
                );
            })}
        </div>
    </div>
);

// Modal simple para solicitar verificación
const SimpleVerificationModal = ({ operation, onClose, onSendEmails }) => {
    const [emailList, setEmailList] = useState([""]);
    const [customMessage, setCustomMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const addEmailField = () => {
        setEmailList([...emailList, ""]);
    };

    const removeEmailField = (index) => {
        if (emailList.length > 1) {
            setEmailList(emailList.filter((_, i) => i !== index));
        }
    };

    const updateEmail = (index, value) => {
        const updatedEmails = emailList.map((email, i) => i === index ? value : email);
        setEmailList(updatedEmails);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const validEmails = emailList.filter(email => email.trim());
        
        if (validEmails.length === 0) {
            alert("Por favor ingresa al menos un correo electrónico válido");
            return;
        }

        setIsLoading(true);
        
        try {
            await onSendEmails({
                operationId: operation.id,
                emails: validEmails.join("; "),
                customMessage: customMessage.trim() || undefined
            });
            
            setEmailList([""]);
            setCustomMessage("");
            onClose();
        } catch (error) {
            console.error("Error sending verification emails:", error);
            alert("Error al enviar los correos. Por favor intenta nuevamente.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center p-4 border-b border-gray-200">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <Icon name="Mail" size={24} className="text-blue-600" />
                        </div>
                        <div>
                            <h3 className="text-xl font-semibold text-gray-900">Solicitar Verificación</h3>
                            <p className="text-sm text-gray-500">Operación #{operation?.id} - {operation?.cliente}</p>
                        </div>
                    </div>
                    <button onClick={onClose} disabled={isLoading} className="p-1 hover:bg-gray-100 rounded">
                        <Icon name="X" size={20} />
                    </button>
                </div>
                
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-3">
                            Correos Electrónicos *
                        </label>
                        <div className="space-y-3">
                            {emailList.map((email, index) => (
                                <div key={index} className="flex items-center gap-2">
                                    <input
                                        type="email"
                                        placeholder="ejemplo@empresa.com"
                                        value={email}
                                        onChange={(e) => updateEmail(index, e.target.value)}
                                        disabled={isLoading}
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                    {emailList.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => removeEmailField(index)}
                                            disabled={isLoading}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                                            title="Eliminar correo"
                                        >
                                            <Icon name="Minus" size={16} />
                                        </button>
                                    )}
                                    {index === emailList.length - 1 && (
                                        <button
                                            type="button"
                                            onClick={addEmailField}
                                            disabled={isLoading}
                                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                                            title="Agregar otro correo"
                                        >
                                            <Icon name="Plus" size={16} />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                            Haz click en <Icon name="Plus" size={12} className="inline mx-1" /> para agregar más correos
                        </p>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                            Información de la Operación:
                        </h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500">Cliente:</span>
                                <p className="font-medium">{operation?.cliente}</p>
                            </div>
                            <div>
                                <span className="text-gray-500">Monto:</span>
                                <p className="font-medium">
                                    {operation?.moneda} {operation?.monto?.toLocaleString('es-PE', {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    })}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={isLoading}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !emailList.some(email => email.trim())}
                            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 min-w-[120px]"
                        >
                            {isLoading ? (
                                <div className="flex items-center gap-2">
                                    <Icon name="Loader" size={16} className="animate-spin" />
                                    Enviando...
                                </div>
                            ) : (
                                <div className="flex items-center gap-2">
                                    <Icon name="Send" size={16} />
                                    Enviar Correos
                                </div>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default function Dashboard({ handleLogout, isAdmin = false }) {
    const navigate = useNavigate();
    const { firebaseUser } = useAuth();
    const [operaciones, setOperaciones] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const [activeFilter, setActiveFilter] = useState('Todas');
    const [openActionMenuId, setOpenActionMenuId] = useState(null);
    const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
    const [selectedOperation, setSelectedOperation] = useState(null);
    const [operationDetails, setOperationDetails] = useState(null);
    const [loadingDetails, setLoadingDetails] = useState(false);
    const [lastLogin, setLastLogin] = useState(null);
    const [showSummary, setShowSummary] = useState(true);

    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [totalOperations, setTotalOperations] = useState(0);
    const PAGE_SIZE = 20;
    
    // Estados para modal de solicitar verificación
    const [isRequestVerificationModalOpen, setIsRequestVerificationModalOpen] = useState(false);
    const [selectedVerificationOp, setSelectedVerificationOp] = useState(null);
    useEffect(() => {
        const fetchOperaciones = async (pageToFetch, filterToApply) => {
            if (!firebaseUser) return;

            setIsLoading(true);
            try {
                const token = await firebaseUser.getIdToken();
                
                // Build URL with filter parameter if not "Todas"
                let url = `https://orquestador-service-598125168090.southamerica-west1.run.app/api/operaciones?page=${pageToFetch}&limit=${PAGE_SIZE}`;
                if (filterToApply && filterToApply !== 'Todas') {
                    url += `&estado=${encodeURIComponent(filterToApply)}`;
                }

                const response = await fetch(url, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Error del servidor');
                
                setOperaciones(data.operations || []);
                setTotalOperations(data.total || 0);
                setTotalPages(Math.ceil((data.total || 0) / PAGE_SIZE));
                setLastLogin(data.last_login);
                setError(null);

            } catch (err) {
                console.error("Error al obtener datos:", err);
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchOperaciones(currentPage, activeFilter);
    }, [firebaseUser, currentPage, activeFilter]);

    const formatLastLogin = (dateString) => {
        if (!dateString) return "Este es tu primer ingreso.";
        const date = new Date(dateString);
        return `Tu último ingreso fue el ${date.toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' })} a las ${date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}`;
    };

    // Now we don't need frontend filtering since backend handles it
    const filteredData = operaciones;
    
    const kpis = useMemo(() => ({
            colocacionMensual: operaciones.filter(op => op.estado === "Verificada").reduce((sum, op) => sum + (op.moneda === "PEN" ? op.monto : op.monto * 3.75), 0),
            metaColocacion: 500000,
        }), [operaciones]);
    
    const notifications = [ { id: 1, type: "success", message: "<b>Verificación Aprobada:</b> La operación <b>OP-00124</b> ha sido verificada.", time: "hace 5 minutos" }];
    const filterOptions = ["Todas", "En Verificación", "Verificada", "Rechazada"];
    
    const handleNewOperationClick = () => {
        navigate('/new-operation');
    };

    const handleSunatClick = () => {
        navigate('/sunat');
    };

    const handleFilterChange = (newFilter) => {
        setActiveFilter(newFilter);
        setCurrentPage(1); // Reset to page 1 when filter changes
    };

    const fetchOperationDetails = async (operationId) => {
        if (!firebaseUser) return;

        try {
            setLoadingDetails(true);
            const token = await firebaseUser.getIdToken();
            
            const response = await fetch(`https://orquestador-service-598125168090.southamerica-west1.run.app/api/operaciones/${operationId}/detalle`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) {
                throw new Error('Error al cargar los detalles de la operación');
            }
            
            const detailData = await response.json();
            setOperationDetails(detailData);
        } catch (error) {
            console.error('Error fetching operation details:', error);
            setError('Error al cargar los detalles de la operación');
        } finally {
            setLoadingDetails(false);
        }
    };

    const handleOpenOperationDetail = (operation) => {
        setSelectedOperation(operation);
        setOperationDetails(null);
        fetchOperationDetails(operation.id);
    };

    const handleCloseOperationDetail = () => {
        setSelectedOperation(null);
        setOperationDetails(null);
    };

    const handleOpenRequestVerificationModal = (operation) => {
        console.log('🔥 Opening verification modal for operation:', operation);
        setSelectedVerificationOp(operation);
        setIsRequestVerificationModalOpen(true);
    };

    const handleSendVerificationEmails = async ({ operationId, emails, customMessage }) => {
        if (!firebaseUser) {
            throw new Error("Usuario no autenticado");
        }
        
        try {
            const token = await firebaseUser.getIdToken();
            const response = await fetch(`${API_BASE_URL}/operaciones/${operationId}/send-verification`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json', 
                    'Authorization': `Bearer ${token}` 
                },
                body: JSON.stringify({ 
                    emails: emails,
                    customMessage: customMessage
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al enviar correos de verificación');
            }
            
            const result = await response.json();
            setIsRequestVerificationModalOpen(false);
            
            alert('Correos de verificación enviados exitosamente');
            
            return result;
        } catch (error) {
            console.error('Error sending verification emails:', error);
            throw error;
        }
    };

    const renderTableBody = () => {
        if (isLoading) return <tr><td colSpan="6" className="text-center py-16"><div className="flex justify-center items-center text-gray-500"><Icon name="Loader" className="animate-spin mr-3" size={24} />Cargando tus operaciones...</div></td></tr>;
        if (error) return <tr><td colSpan="6" className="text-center py-16 text-red-600"><Icon name="ServerCrash" size={32} className="mx-auto mb-2" /><p className="font-semibold">No se pudieron cargar los datos</p><p className="text-sm">{error}</p></td></tr>;
        if (filteredData.length === 0) return <tr><td colSpan="6" className="text-center text-gray-500 py-16"><Icon name="SearchX" size={40} className="mx-auto mb-2 opacity-50"/><p className="font-semibold">No se encontraron operaciones en este estado.</p></td></tr>;
        
        return filteredData.map(op => (
            <OperationRow
                key={op.id}
                operation={op}
                onActionMenuToggle={setOpenActionMenuId}
                isActionMenuOpen={openActionMenuId === op.id}
                setSelectedOperation={handleOpenOperationDetail}
                onRequestVerification={handleOpenRequestVerificationModal}
            />
        ));
    };

    return (
        <div className="p-4 sm:p-6 lg:p-8">
            
            {!isAdmin}
            <header className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Mi Panel de Operaciones</h1>
                    <p className="text-lg text-gray-500">Bienvenido de vuelta, {firebaseUser?.displayName?.split(' ')[0] || 'Usuario'} 👋</p>
                     {!isLoading && (
                         <div className="mt-2 flex items-center text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-md w-fit">
                            <Icon name="ShieldCheck" size={14} className="mr-1.5 text-green-600"/>
                            <span>{formatLastLogin(lastLogin)}</span>
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <Button variant="ghost" size="icon" className="h-10 w-10" onClick={() => setIsNotificationsOpen(prev => !prev)}><Icon name="Bell" /></Button>
                        {isNotificationsOpen && <NotificationDropdown notifications={notifications} onClose={() => setIsNotificationsOpen(false)} />}
                    </div>
                     <Button variant="outline" iconName="LogOut" onClick={handleLogout}>Cerrar Sesión</Button>
                     <Button variant="success" iconName="FileText" onClick={handleSunatClick}>Software SUNAT</Button>
                     <Button variant="default" iconName="PlusCircle" onClick={handleNewOperationClick}>Ingresar Nueva Operación</Button>
                </div>
            </header>
            

            <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                    {showSummary && (
                        <VistaResumenSemanal 
                            kpis={kpis} 
                            operations={operaciones} 
                            onClose={() => setShowSummary(false)} 
                        />
                    )}
                    <Card>
                        <CardHeader className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
                            <div>
                                <CardTitle>Mis Operaciones Cargadas</CardTitle>
                                <CardDescription>Visualiza y gestiona el estado de tus operaciones.</CardDescription>
                            </div>
                            <div className="flex flex-wrap gap-2 mt-4 sm:mt-0">
                                {filterOptions.map(option => (
                                   <Button key={option} variant={activeFilter === option ? 'default' : 'outline'} size="sm" onClick={() => handleFilterChange(option)}>{option}</Button>
                                ))}
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-5 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Cliente / Deudor</th>
                                            <th className="px-5 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Monto</th>
                                            <th className="px-5 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Antigüedad</th>
                                            <th className="px-5 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Gestión</th>
                                            <th className="px-5 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Estado</th>
                                            {/* <th className="px-5 py-3 relative"><span className="sr-only">Acciones</span></th>*/}
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {renderTableBody()}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                        {totalPages > 1 && (
        <div className="flex items-center justify-between p-4 border-t border-gray-200">
            <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1 || isLoading}
            >
                <Icon name="ArrowLeft" size={14} className="mr-1" />
                Anterior
            </Button>
            <span className="text-sm text-gray-600">
                Página <strong>{currentPage}</strong> de <strong>{totalPages}</strong> ({totalOperations} operaciones)
            </span>
            <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages || isLoading}
            >
                Siguiente
                <Icon name="ArrowRight" size={14} className="ml-1" />
            </Button>
        </div>
    )}
                    </Card>
                </div>
                <aside className="lg:col-span-1 space-y-6">
                    <MetasDashboard kpis={kpis}/>
                    <EstadisticasClave operations={operaciones} />
                    {/*<LogroDestacado logro={logros[0]} /> */}
                </aside>
            </main>
            
            <Modal isOpen={!!selectedOperation} onClose={handleCloseOperationDetail} title={`Detalle Operación: ${selectedOperation?.id}`}>
                {selectedOperation && (
                    <OperationDetailModalContent 
                        operation={operationDetails || selectedOperation}
                        isLoading={loadingDetails}
                        onRequestVerification={handleOpenRequestVerificationModal}
                    />
                )}
            </Modal>
            
            {/* Modal de Solicitar Verificación */}
            {isRequestVerificationModalOpen && selectedVerificationOp && (
                <SimpleVerificationModal 
                    operation={selectedVerificationOp}
                    onClose={() => setIsRequestVerificationModalOpen(false)}
                    onSendEmails={handleSendVerificationEmails}
                />
            )}
        </div>
    );
}

const ActionMenuPortal = ({ children, onClose, menuPosition }) => {
    const menuRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                onClose();
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [onClose]);

    // Usamos el portal para renderizar el menú fuera del DOM de la tabla
    return ReactDOM.createPortal(
        <div
            ref={menuRef}
            style={{
                position: 'absolute',
                top: `${menuPosition.top}px`,
                left: `${menuPosition.left}px`,
            }}
            className="z-50" // <-- z-index alto para estar por encima de todo
        >
            {children}
        </div>,
        document.body
    );
};

const OperationRow = React.memo(({ operation, onActionMenuToggle, isActionMenuOpen, setSelectedOperation, onRequestVerification }) => {
    const statusMap = { "En Verificación": { variant: 'warning', icon: 'Clock', text: 'En Verificación' }, "Verificada": { variant: 'success', icon: 'CheckCircle', text: 'Verificada' }, "Rechazada": { variant: 'error', icon: 'XCircle', text: 'Rechazada' }};
    const currentStatus = statusMap[operation.estado] || { variant: 'neutral', icon: 'HelpCircle', text: operation.estado };

    const formatCurrency = (value, currency) => {
      const validCurrency = currency && currency !== "N/A" ? currency : "PEN";
      return new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: validCurrency,
      }).format(value || 0);
    };

    const calculateAntiquity = (dateString) => {
        const diffMs = Math.abs(new Date() - new Date(dateString));
        const totalHours = Math.floor(diffMs / (1000 * 60 * 60));
        const totalDays = Math.floor(totalHours / 24);

        if (totalHours < 24) {
            if (totalHours === 0) return { display: "Recién creado", days: 0 };
            return { display: `${totalHours} hora${totalHours > 1 ? 's' : ''}`, days: 0 };
        }
        return { display: `${totalDays} día${totalDays > 1 ? 's' : ''}`, days: totalDays };
    };
    const antiquityInfo = calculateAntiquity(operation.fechaIngreso);
    const antiquityDays = antiquityInfo.days;

    const buttonRef = useRef(null);
    const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
    const fechaFormateada = formatInPeruTimeZone(operation.fechaIngreso, 'dd/MM/yy');


    const handleMenuToggle = () => {
        if (buttonRef.current) {
            const rect = buttonRef.current.getBoundingClientRect();
            setMenuPosition({
                top: rect.bottom + window.scrollY,
                left: rect.left + window.scrollX - 224,
            });
        }
        onActionMenuToggle(isActionMenuOpen ? null : operation.id);
    };
    
    return (
        <tr className="hover:bg-gray-50">
            <td className="px-5 py-4">
                <div className="font-semibold text-gray-900">{operation.cliente}</div>
                <div className="text-xs text-gray-500">{operation.id || 'N/A'}</div>
            </td>
            <td className="px-5 py-4 whitespace-nowrap font-semibold text-blue-600">
                {formatCurrency(operation.monto, operation.moneda)}
            </td>
            
            <td className="px-5 text-center py-4 whitespace-nowrap">
                {/* 3. Actualiza esta línea para usar la nueva variable */}
                <div className={`font-semibold ${antiquityDays > 15 ? 'text-red-600' : 'text-gray-800'}`}>{antiquityInfo.display}</div>
                <div className="text-xs  text-gray-500">{fechaFormateada}</div>
            </td>

             <td className="px-5 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2 text-gray-700">
                    <Icon name="Mail" size={16}/>
                    <span>{operation.gestionesVerificacion?.length || 0} Correo(s)</span>
                </div>
            </td>
            <td className="px-5 py-4 whitespace-nowrap">
                <Badge variant={currentStatus.variant} iconName={currentStatus.icon}>
                    {currentStatus.text}
                </Badge>
            </td>
            
            <td className="px-5 py-4 whitespace-nowrap text-right text-sm font-medium">
                <Button ref={buttonRef} variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:bg-gray-200" onClick={handleMenuToggle}>
                    <Icon name="MoreHorizontal" size={20}/>
                </Button>
                {isActionMenuOpen && (
                    <ActionMenuPortal onClose={() => onActionMenuToggle(null)} menuPosition={menuPosition}>
                        <div className="w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5">
                            <div className="py-1" role="menu">
                                <button onClick={() => { setSelectedOperation(operation); onActionMenuToggle(null); }} className="w-full text-left flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" role="menuitem"><Icon name="Eye" size={16}/> Ver Detalle Completo</button>
                                <button onClick={() => { onRequestVerification && onRequestVerification(operation); onActionMenuToggle(null); }} className="w-full text-left flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" role="menuitem"><Icon name="Send" size={16}/> Solicitar Verificación</button>
                                <button className="w-full text-left flex items-center gap-3 px-4 py-2 text-sm text-red-700 hover:bg-red-50" role="menuitem"><Icon name="Trash2" size={16}/> Solicitar Anulación</button>
                            </div>
                        </div>
                    </ActionMenuPortal>
                )}
            </td>
            
            
        </tr>
    );
});

// --- Componente para mostrar historial de gestiones ---
const HistorialGestiones = ({ gestiones }) => {
    return (
        <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <Icon name="Phone" size={16} />
                Historial de Gestiones ({gestiones?.length || 0})
            </h5>
            {gestiones && gestiones.length > 0 ? (
                <div className="max-h-48 overflow-y-auto space-y-2 pr-2">
                    {gestiones.map((g, i) => (
                        <div key={g.id || i} className="text-xs p-3 bg-gray-50 rounded-md border border-gray-200">
                            <div className="flex justify-between items-start mb-1">
                                <div className="flex-1">
                                    <p className="font-semibold text-gray-800">
                                        {g.tipo}: <span className="font-normal text-gray-600">{g.resultado}</span>
                                    </p>
                                    {(g.nombreContacto || g.nombre_contacto) && (
                                        <p className="text-gray-600 text-xs">
                                            Contacto: {g.nombreContacto || g.nombre_contacto} {(g.cargoContacto || g.cargo_contacto) && `(${g.cargoContacto || g.cargo_contacto})`}
                                        </p>
                                    )}
                                    {(g.telefonoEmailContacto || g.telefono_email_contacto) && (
                                        <p className="text-gray-600 text-xs">
                                            {g.telefonoEmailContacto || g.telefono_email_contacto}
                                        </p>
                                    )}
                                    <p className="text-gray-500 italic mt-1">"{g.notas}"</p>
                                    <div className="flex justify-between items-center mt-2">
                                        <span className="text-gray-600 font-medium">{g.analista}</span>
                                        <span className="text-gray-400">{new Date(g.fecha).toLocaleString('es-ES')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-4">
                    <Icon name="MessageSquare" className="mx-auto mb-2 text-gray-400" size={24} />
                    <p className="text-xs text-gray-500 italic">No hay gestiones manuales registradas.</p>
                </div>
            )}
        </div>
    );
};

// --- Componente para el contenido del Modal de Detalles ---
const OperationDetailModalContent = ({ operation, isLoading, onRequestVerification }) => {
    const processSteps = ["Ingresada", "Verificando", "Cavali", "Cursada"];
    const etapaActual = operation?.etapaActual || "Ingresada";

    if (isLoading) {
        return (
            <div className="text-center py-12">
                <Icon name="Loader" className="animate-spin mx-auto mb-4 text-blue-600" size={32} />
                <p className="text-gray-500">Cargando detalles de la operación...</p>
            </div>
        );
    }

    if (!operation) {
        return (
            <div className="text-center py-12">
                <Icon name="AlertCircle" className="mx-auto mb-4 text-red-600" size={32} />
                <p className="text-red-500">Error: No se pudo cargar la información de la operación</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <ProcessTimeline steps={processSteps} currentStep={etapaActual}/>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mt-6">
                <p><strong className="text-gray-500 block">ID Operación:</strong> {operation?.id || 'N/A'}</p>
                <p><strong className="text-gray-500 block">Fecha Ingreso:</strong> {operation?.fechaIngreso ? new Date(operation.fechaIngreso).toLocaleDateString('es-ES', { dateStyle: 'long' }) : 'N/A'}</p>
                <p><strong className="text-gray-500 block">Cliente:</strong> {operation?.cliente || 'N/A'}</p>
                <p><strong className="text-gray-500 block">Deudor:</strong> {operation?.deudor || 'N/A'}</p>
                <p><strong className="text-gray-500 block">Tasa:</strong> {operation?.tasa || 'N/A'}</p>
                <p><strong className="text-gray-500 block">Comisión:</strong> {operation?.comision || 'N/A'}</p>
            </div>
            
            {/* Nueva sección para mostrar gestiones */}
            <div className="pt-4 border-t border-gray-200">
                <HistorialGestiones gestiones={operation?.gestiones || operation?.gestionesVerificacion} />
            </div>
            
            <div className="pt-4 border-t border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-2">Acciones Rápidas</h4>
                <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" iconName="Send" onClick={() => onRequestVerification && onRequestVerification(operation)}>Solicitar Verificación</Button>
                    <Button variant="outline" size="sm" iconName="MessageSquare" onClick={() => alert(`Simulando añadir nota para ${operation?.id || 'N/A'}`)}>Añadir Nota</Button>
                </div>
            </div>
        </div>
    );
};



