import React from "react";

export const ToggleSwitch = ({ enabled, setEnabled }) => (
  <button
    type="button"
    onClick={() => setEnabled(!enabled)}
    className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${enabled ? 'bg-green-500' : 'bg-gray-200'}`}
    role="switch"
    aria-checked={enabled}
  >
    <span
      aria-hidden="true"
      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${enabled ? 'translate-x-5' : 'translate-x-0'}`}
    />
  </button>
);