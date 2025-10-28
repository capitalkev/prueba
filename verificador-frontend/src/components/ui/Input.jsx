import React from "react";

export const InputGroup = ({ label, htmlFor, optional = false, children }) => (
  <div>
    <label htmlFor={htmlFor} className="block text-sm font-medium text-gray-500 mb-1.5">
      {label} {optional && <span className="text-xs text-gray-400">(Opcional)</span>}
    </label>
    <div className="relative">{children}</div>
  </div>
);

export const Input = React.forwardRef(({ className = "", type = "text", icon, ...props }, ref) => (
  <>
    <input
      type={type}
      ref={ref}
      className={`h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${icon ? 'pr-10' : ''} ${className}`}
      {...props}
    />
    {icon && <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">{icon}</div>}
  </>
));