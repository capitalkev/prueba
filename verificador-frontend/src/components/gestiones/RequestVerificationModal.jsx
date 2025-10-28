import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Textarea } from "../ui/Textarea";
import { Icon } from "../Icon";

export const RequestVerificationModal = ({ isOpen, onClose, operation, onSendEmails }) => {
  console.log('🔥 RequestVerificationModal render - isOpen:', isOpen, 'operation:', operation);
  const [emails, setEmails] = useState("");
  const [customMessage, setCustomMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!emails.trim()) {
      alert("Por favor ingresa al menos un correo electrónico");
      return;
    }

    setIsLoading(true);
    
    try {
      await onSendEmails({
        operationId: operation.id,
        emails: emails,
        customMessage: customMessage.trim() || undefined
      });
      
      // Reset form and close modal
      setEmails("");
      setCustomMessage("");
      onClose();
    } catch (error) {
      console.error("Error sending verification emails:", error);
      alert("Error al enviar los correos. Por favor intenta nuevamente.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setEmails("");
      setCustomMessage("");
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <Modal onClose={handleClose}>
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-white rounded-xl p-6 w-full max-w-2xl mx-4"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Icon name="Mail" size={24} className="text-blue-600" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Solicitar Verificación
                  </h2>
                  <p className="text-sm text-gray-500">
                    Operación #{operation?.id} - {operation?.cliente}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                disabled={isLoading}
              >
                <Icon name="X" size={20} />
              </Button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Correos Electrónicos *
                </label>
                <Input
                  type="text"
                  placeholder="email1@empresa.com; email2@empresa.com"
                  value={emails}
                  onChange={(e) => setEmails(e.target.value)}
                  disabled={isLoading}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Separa múltiples correos con punto y coma (;)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mensaje Adicional (Opcional)
                </label>
                <Textarea
                  placeholder="Mensaje personalizado que se agregará al correo estándar..."
                  value={customMessage}
                  onChange={(e) => setCustomMessage(e.target.value)}
                  disabled={isLoading}
                  rows={4}
                  className="w-full"
                />
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
                    <span className="text-gray-500">Deudor:</span>
                    <p className="font-medium">{operation?.deudor}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Monto:</span>
                    <p className="font-medium">
                      {operation?.moneda} {operation?.montoTotal?.toLocaleString('es-PE', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Facturas:</span>
                    <p className="font-medium">{operation?.facturas?.length || 0}</p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={isLoading}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={isLoading || !emails.trim()}
                  className="min-w-[120px]"
                >
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Enviando...
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <Icon name="Send" size={16} />
                      Enviar Correos
                    </div>
                  )}
                </Button>
              </div>
            </form>
          </motion.div>
        </Modal>
      )}
    </AnimatePresence>
  );
};