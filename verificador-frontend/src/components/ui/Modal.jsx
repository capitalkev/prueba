import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const Modal = ({ isOpen, onClose, children, size = "lg" }) => {
    const sizeClasses = {
        sm: "max-w-md",
        md: "max-w-xl",
        lg: "max-w-3xl",
        xl: "max-w-5xl"
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
                >
                    {/* Contenido del modal que evita el cierre al hacer clic dentro de él */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ duration: 0.2 }}
                        className={`bg-white rounded-xl shadow-2xl w-full ${sizeClasses[size] || sizeClasses.lg}`}
                        onClick={e => e.stopPropagation()}
                    >
                        {children}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};