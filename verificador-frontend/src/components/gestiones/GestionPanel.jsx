import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/Button';
import { Icon } from '../Icon';
import { Textarea } from '../ui/Textarea';

const TabsContext = React.createContext();
const Tabs = ({ children, defaultValue, className = "" }) => {
    const [activeTab, setActiveTab] = useState(defaultValue);
    return <TabsContext.Provider value={{ activeTab, setActiveTab }}><div className={className}>{children}</div></TabsContext.Provider>;
};
const TabsList = ({ children, className = "" }) => <div className={`flex items-center border-b border-gray-200 ${className}`}>{children}</div>;
const TabsTrigger = ({ children, value, iconName, className = "" }) => {
    const { activeTab, setActiveTab } = React.useContext(TabsContext);
    const isActive = activeTab === value;
    return <button onClick={() => setActiveTab(value)} className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${isActive ? 'border-red-500 text-red-600' : 'border-transparent text-gray-500 hover:text-red-500 hover:border-red-300'} ${className}`}>{iconName && <Icon name={iconName} size={14} />} {children}</button>;
};
const TabsContent = ({ children, value, className = "" }) => {
    const { activeTab } = React.useContext(TabsContext);
    return activeTab === value ? <div className={`py-4 ${className}`}>{children}</div> : null;
};

const GestionForm = ({ onSave, onCancel }) => {
    const [gestion, setGestion] = useState({ tipo: 'Llamada', resultado: 'Conforme', nombre_contacto: '', cargo_contacto: '', telefono_email_contacto: '', notas: '' });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setGestion(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = () => {
        if (!gestion.notas.trim()) {
            alert("Por favor, ingrese una nota cualitativa para la gestión.");
            return;
        }
        onSave(gestion);
    };

    return (
        <div className="space-y-4">
            <h4 className="font-semibold text-gray-800">Registrar Nueva Gestión</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <select name="tipo" value={gestion.tipo} onChange={handleChange} className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-500"><option>Llamada</option><option>Email Manual</option><option>WhatsApp</option><option>Visita en Terreno</option></select>
                <select name="resultado" value={gestion.resultado} onChange={handleChange} className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-500"><option>Conforme</option><option>No Contesta</option><option>Discrepancia de Monto</option><option>Desconoce Factura</option><option>Solicita más tiempo</option></select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                 <input name="nombre_contacto" value={gestion.nombre_contacto} onChange={handleChange} placeholder="Nombre Contacto" className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-500"/>
                 <input name="cargo_contacto" value={gestion.cargo_contacto} onChange={handleChange} placeholder="Cargo" className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-500"/>
                 <input name="telefono_email_contacto" value={gestion.telefono_email_contacto} onChange={handleChange} placeholder="Teléfono/Email" className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-500"/>
            </div>
            <Textarea name="notas" value={gestion.notas} onChange={handleChange} placeholder="Notas cualitativas de la gestión..." required/>
            <div className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={onCancel}>Cancelar</Button>
                <Button variant="outline" size="sm" onClick={handleSave} iconName="Save">Guardar Gestión</Button>
            </div>
        </div>
    );
};

const FacturaChecklist = ({ facturas, onCheck }) => {
    return (
        <div>
            <h5 className="text-sm font-semibold text-gray-700 mb-2">Facturas de la Operación</h5>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
                {facturas.map(factura => (
                    <div key={factura.folio} className={`p-2 rounded-md border flex items-center justify-between transition-colors ${factura.estado === 'Verificada' ? 'bg-green-50 border-green-200' : factura.estado === 'Rechazada' ? 'bg-red-50 border-red-200' : 'bg-white'}`}>
                        <span className="text-sm text-gray-700">{factura.folio} - {new Intl.NumberFormat('es-PE', { style: 'currency', currency: factura.moneda }).format(factura.monto)}</span>
                         <div className="flex items-center gap-1">
                            <button onClick={() => onCheck(factura.folio, 'En Verificación')} title="Desmarcar Estado" className="h-6 w-6 rounded-full hover:bg-gray-200 text-gray-500 flex items-center justify-center">
                                <Icon name="RotateCcw" size={14}/>
                            </button>
                            <button onClick={() => onCheck(factura.folio, 'Rechazada')} title="Rechazar Factura" className="h-6 w-6 rounded-full hover:bg-red-200 text-red-500 flex items-center justify-center"><Icon name="X" size={14}/></button>
                            <button onClick={() => onCheck(factura.folio, 'Verificada')} title="Verificar Factura" className="h-6 w-6 rounded-full hover:bg-green-200 text-green-500 flex items-center justify-center"><Icon name="Check" size={14}/></button>
                         </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const HistorialGestiones = ({ gestiones, operation, onDeleteGestion }) => {
    console.log('=== HISTORIAL DEBUG ===');
    console.log('Gestiones:', gestiones);
    gestiones.forEach((g, i) => {
        console.log(`Gestión ${i}:`, { id: g.id, tipo: g.tipo, hasId: !!g.id });
    });
    console.log('=== FIN HISTORIAL DEBUG ===');
    
    return (
        <div className="space-y-3">
            <h5 className="text-sm font-semibold text-gray-700">Historial de Gestiones</h5>
            {gestiones.length > 0 ? (
                <div className="max-h-48 overflow-y-auto space-y-2 pr-2">
                    {gestiones.map((g, i) => (
                            <div key={i} className="text-xs p-2 bg-gray-100 rounded-md border border-gray-200 group hover:bg-gray-200">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        <p className="font-semibold">{g.tipo}: <span className="font-normal text-gray-600">{g.resultado}</span></p>
                                        <p className="text-gray-500 italic">"{g.notas}" - {g.analista}</p>
                                        <p className="text-right text-gray-400">{new Date(g.fecha).toLocaleString('es-ES')}</p>
                                    </div>
                                    {g.id ? (
                                        <button
                                            onClick={() => onDeleteGestion(g.id, operation.id)}
                                            className="ml-2 bg-red-500 text-white p-1 rounded text-xs"
                                            title="Eliminar gestión"
                                        >
                                            <Icon name="Trash2" size={12} />
                                        </button>
                                    ) : (
                                        <span className="ml-2 bg-gray-300 text-gray-600 p-1 rounded text-xs">
                                            Sin ID
                                        </span>
                                    )}
                                </div>
                            </div>
                    ))}
                </div>
            ) : <p className="text-xs text-gray-500 italic">No hay gestiones manuales registradas.</p>}
        </div>
    );
};

const ContactoInteligente = ({ deudor }) => (
    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg h-full flex flex-col justify-center">
        <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-2"><Icon name="Lightbulb" size={20}/>Asistencia IA ✨</h4>
        <div className="text-sm space-y-2">
            <div>
                <p className="font-semibold text-blue-900/80">Contacto Sugerido:</p>
                <p className="text-blue-900/80">Llamar a <strong className="text-blue-700">Juan Pérez</strong> (Jefe de Tesorería) al <strong className="text-blue-700">998765432</strong>.</p>
            </div>
            <div>
                <p className="font-semibold text-blue-900/80">Insight:</p>
                <p className="text-blue-900/80">Suele responder después del 2do correo de seguimiento.</p>
            </div>
        </div>
    </div>
);

export const GestionPanel = ({
    operation,
    onSaveGestion,
    onFacturaCheck,
    onOpenAdelantoModal,
    onDeleteGestion,
    onCancel
}) => {
    return (
        <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
        >
            <div className="p-5 border-t border-gray-200/60 bg-gray-50/50">
                <Tabs defaultValue="gestion">
                    <TabsList>
                        <TabsTrigger value="facturas" iconName="ListChecks">Facturas ({operation.facturas.filter(f => f.estado === 'Verificada').length}/{operation.facturas.length})</TabsTrigger>
                        <TabsTrigger value="gestion" iconName="PlusCircle">Registrar Gestión</TabsTrigger>
                        <TabsTrigger value="historial" iconName="History">Historial</TabsTrigger>
                        {/*<TabsTrigger value="ia" iconName="Lightbulb">Asistencia IA</TabsTrigger>*/}
                    </TabsList>
                    
                    <TabsContent value="gestion">
                        <GestionForm onSave={(data) => onSaveGestion(operation.id, data)} onCancel={onCancel} />
                    </TabsContent>
                    <TabsContent value="facturas">
                        <FacturaChecklist facturas={operation.facturas} onCheck={(folio, estado) => onFacturaCheck(operation.id, folio, estado)} />
                    </TabsContent>
                    <TabsContent value="historial">
                        <HistorialGestiones gestiones={operation.gestiones} operation={operation} onDeleteGestion={onDeleteGestion} />
                    </TabsContent>
                     <TabsContent value="ia">
                        <ContactoInteligente deudor={operation.deudor}/>
                    </TabsContent>
                </Tabs>
                
                <div className="mt-4 pt-4 border-t border-dashed border-gray-300">
                    <Button variant="outline" size="sm" iconName="Zap" onClick={() => onOpenAdelantoModal(operation)}>
                        Avanzar a Post-Verificado (Adelanto Express)
                    </Button>
                </div>
            </div>
        </motion.div>
    );
};