import React from 'react';

export const Textarea = React.forwardRef(({ className = "", ...props }, ref) => (
    <textarea
        ref={ref}
        className={`w-full min-h-[80px] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 ${className}`}
        {...props}
    />
));