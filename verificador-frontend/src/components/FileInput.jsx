import React, { useCallback, useRef, useState } from "react";
import { Icon } from "./Icon";
export const FileInput = ({ onFileChange, accept, title, iconName }) => {
  const [isActive, setIsActive] = useState(false);
  const inputRef = useRef();

  const handleDrag = useCallback((e) => {
    e.preventDefault(); e.stopPropagation();
    if (["dragenter", "dragover"].includes(e.type)) setIsActive(true);
    if (e.type === "dragleave") setIsActive(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation(); setIsActive(false);
    if (e.dataTransfer.files.length > 0) onFileChange(e.dataTransfer.files);
  }, [onFileChange]);
  
  const handleChange = (e) => onFileChange(e.target.files);

  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center cursor-pointer rounded-xl border-2 border-dashed transition-all duration-200 ${isActive ? 'border-primary bg-primary/5' : 'border-border-color hover:border-primary/50'}`} onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop} onClick={() => inputRef.current.click()}>
      <input ref={inputRef} type="file" multiple accept={accept} onChange={handleChange} className="hidden" />
      <div className="p-3 bg-primary/10 rounded-full mb-3"><Icon name={iconName} size={28} className="text-primary" /></div>
      <p className="font-semibold text-primary">{title}</p>
      <p className="text-sm text-muted">Arrastra y suelta o haz clic para seleccionar.</p>
    </div>
  );
};