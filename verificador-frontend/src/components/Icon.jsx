import * as LucideIcons from "lucide-react";

export const Icon = ({ name, size = 16, ...props }) => {
  const LucideIcon = LucideIcons[name];
  if (!LucideIcon) return <LucideIcons.HelpCircle size={size} {...props} />;
  return <LucideIcon size={size} {...props} className={`inline-block flex-shrink-0 ${props.className || ''}`} />;
};