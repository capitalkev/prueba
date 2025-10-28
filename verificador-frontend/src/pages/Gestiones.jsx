import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useGestiones } from "../hooks/useGestiones";
import { Icon } from "../components/Icon";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { OperationCard } from "../components/gestiones/OperationCard";
import { DashboardSidebar } from "../components/gestiones/DashboardSidebar";
import { Header } from "../components/gestiones/Header";
import { AdelantoExpressModal } from "../components/gestiones/AdelantoExpressModal";
import { RequestVerificationModal } from "../components/gestiones/RequestVerificationModal";
import { AssignOperationModal } from "../components/gestiones/AssignOperationModal";

export default function Gestiones({ user, handleLogout, isAdmin = false }) {
  console.log('🔥 Gestiones component render');
  const {
    isLoading,
    error,
    filteredData,
    activeFilter,
    setActiveFilter,
    activeGestionId,
    setActiveGestionId,
    handleSaveGestion,
    handleFacturaCheck,
    handleOpenAdelantoModal,
    handleCompleteOperation,
    handleConfirmAdelanto,
    isAdelantoModalOpen,
    setIsAdelantoModalOpen,
    selectedAdelantoOp,
    analysts,
    isAssignModalOpen,
    setIsAssignModalOpen,
    selectedOpToAssign,
    handleOpenAssignModal,
    handleConfirmAssignment,
    handleDeleteGestion,
    isRequestVerificationModalOpen,
    setIsRequestVerificationModalOpen,
    selectedVerificationOp,
    handleOpenRequestVerificationModal,
    handleSendVerificationEmails,
  } = useGestiones(user);
  
  console.log('🔥 Modal states:', {
    isRequestVerificationModalOpen,
    selectedVerificationOp,
    handleOpenRequestVerificationModal
  });

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Icon
            name="LoaderCircle"
            size={40}
            className="mx-auto mb-3 animate-spin text-red-500"
          />
          <p className="font-semibold">Cargando operaciones...</p>
        </div>
      );
    }
    if (error) {
      return (
        <div className="text-center py-12 text-red-600">
          <Icon name="ServerCrash" size={40} className="mx-auto mb-3" />
          <p className="font-semibold">Error al cargar los datos</p>
          <p className="text-sm">{error}</p>
        </div>
      );
    }
    if (filteredData.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          <Icon
            name="CheckCircle"
            size={40}
            className="mx-auto mb-2 opacity-50"
          />
          <p className="font-semibold">¡Todo limpio por aquí!</p>
          <p>No hay operaciones en esta vista.</p>
        </div>
      );
    }
    return (
      <AnimatePresence>
        {filteredData.map((op) => (
          <OperationCard
            key={op.id}
            operation={op}
            activeGestionId={activeGestionId}
            setActiveGestionId={setActiveGestionId}
            onSaveGestion={handleSaveGestion}
            onFacturaCheck={handleFacturaCheck}
            onOpenAdelantoModal={handleOpenAdelantoModal}
            onCompleteOperation={handleCompleteOperation}
            isAdmin={isAdmin}
            onAssignOperation={handleOpenAssignModal}
            onDeleteGestion={handleDeleteGestion}
            onRequestVerification={handleOpenRequestVerificationModal}
          />
        ))}
      </AnimatePresence>
    );
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 font-sans">
      <Header user={user} handleLogout={handleLogout} notifications={[]} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
        <main className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
              <div>
                <CardTitle>Cola de Tareas de Verificación</CardTitle>
                <CardDescription>
                  Operaciones asignadas y priorizadas por el sistema.
                </CardDescription>
              </div>
              <div className="flex flex-wrap gap-2 mt-4 sm:mt-0">
                {["En Proceso", "Adelanto Express"].map((option) => (
                  <Button
                    key={option}
                    variant={activeFilter === option ? "primary" : "outline"}
                    size="sm"
                    onClick={() => setActiveFilter(option)}
                  >
                    {option}
                  </Button>
                ))}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="space-y-4 p-4">{renderContent()}</div>
            </CardContent>
          </Card>
        </main>
        <aside className="lg:col-span-1 space-y-6">
          <DashboardSidebar />
        </aside>
      </div>

      <AdelantoExpressModal
        isOpen={isAdelantoModalOpen}
        onClose={() => setIsAdelantoModalOpen(false)}
        onConfirm={handleConfirmAdelanto}
        operation={selectedAdelantoOp}
      />

      <RequestVerificationModal
        isOpen={isRequestVerificationModalOpen}
        onClose={() => setIsRequestVerificationModalOpen(false)}
        operation={selectedVerificationOp}
        onSendEmails={handleSendVerificationEmails}
      />

      <AssignOperationModal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        onConfirm={handleConfirmAssignment}
        operation={selectedOpToAssign}
        analysts={analysts}
      />
    </div>
  );
}