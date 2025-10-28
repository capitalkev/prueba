// src/components/FormSection.jsx
import React from "react";

export const FormSection = ({ number, title, children }) => {
  return (
    <div className="form-section">
      <div className="flex items-center gap-3 pb-3 mb-6 border-b border-gray-200">
        <div className="w-8 h-8 rounded-full flex items-center justify-center font-semibold bg-blue-600 text-white">
          {number}
        </div>
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="space-y-6 pl-12">{children}</div>
    </div>
  );
};