import React from 'react';

export const ProgressBar = ({ value, max, colorClass = "bg-red-500" }) => {
    const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    return (
        <div className="w-full bg-gray-200 rounded-full h-2.5 mt-1 overflow-hidden">
            <div
                className={`${colorClass} h-2.5 rounded-full transition-all duration-500`}
                style={{ width: `${percentage}%` }}
            ></div>
        </div>
    );
};