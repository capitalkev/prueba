// src/components/FileListItem.jsx
import React from "react";
import { Icon } from "./Icon";

export const FileListItem = ({ file, onRemove }) => {
  const getIconName = () => {
    if (file.type.includes("xml")) return "FileCode";
    if (file.type.includes("pdf")) return "FileText";
    return "File";
  };

  return (
    <div className="flex items-center justify-between p-2 pr-1 bg-gray-100 rounded-md text-sm border border-gray-200">
      <div className="flex items-center gap-2 overflow-hidden">
        <Icon
          name={getIconName()}
          size={18}
          className="text-gray-500 flex-shrink-0"
        />
        <span className="truncate" title={file.name}>
          {file.name}
        </span>
        <span className="text-gray-400 text-xs flex-shrink-0">
          ({(file.size / 1024).toFixed(1)} KB)
        </span>
      </div>
      <button
        type="button"
        onClick={onRemove}
        className="flex-shrink-0 h-6 w-6 rounded-full bg-red-100 text-red-600 hover:bg-red-200 flex items-center justify-center transition-colors"
        aria-label="Eliminar archivo"
      >
        <Icon name="X" size={12} strokeWidth={3} />
      </button>
    </div>
  );
};