import React from "react";
import { Icon } from "../Icon";

export const Card = React.forwardRef(({ children, className = "", ...props }, ref) => (
  <div ref={ref} className={`bg-white rounded-xl shadow-lg border border-gray-200 ${className}`} {...props}>
    {children}
  </div>
));
export const CardHeader = ({ children, className = "" }) => <div className={`p-6 border-b border-gray-200 ${className}`}>{children}</div>;
export const CardTitle = ({ children, className = "", iconName }) => (
  <h3 className={`text-xl font-bold text-gray-900 flex items-center gap-3 ${className}`}>
    {iconName && <Icon name={iconName} size={24} className="text-blue-600"/>}
    {children}
  </h3>
);
export const CardDescription = ({ children, className = "" }) => <p className={`text-sm text-gray-500 mt-1 ${className}`}>{children}</p>;
export const CardContent = ({ children, className = "" }) => <div className={`p-6 ${className}`}>{children}</div>;
export const CardFooter = ({ children, className = "" }) => <div className={`p-6 border-t border-gray-200 bg-gray-50/50 rounded-b-xl ${className}`}>{children}</div>;