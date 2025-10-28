import React from "react";
import { Icon } from "../Icon";

export const Button = React.forwardRef(({ className = "", variant = "default", size="default", children, iconName, ...props }, ref) => {
  const base = "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    destructive: "bg-red-600 text-white hover:bg-red-700",
    outline: "border border-gray-300 bg-transparent hover:bg-gray-100 text-gray-800"
  };
  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 px-3",
    xs: "h-7 px-2 text-xs"
  };
  return (
    <button ref={ref} className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {iconName && <Icon name={iconName} size={16} />}
      {children}
    </button>
  );
});