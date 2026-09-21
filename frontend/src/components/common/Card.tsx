import React from "react";

interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  className = "",
  bodyClassName = "",
  glow = false,
}) => {
  return (
    <div
      className={`rounded-xl border border-zinc-800/80 bg-zinc-900/60 backdrop-blur-md transition-all duration-200 ${
        glow ? "shadow-lg shadow-cyan-950/20 border-cyan-500/20" : ""
      } ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-zinc-800/60 px-5 py-4">
          <div>
            {title && (
              <h3 className="text-sm font-semibold tracking-wide text-zinc-100 flex items-center gap-2">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-zinc-400">{subtitle}</p>
            )}
          </div>
          {action && <div className="flex items-center gap-2">{action}</div>}
        </div>
      )}
      <div className={`p-5 ${bodyClassName}`}>{children}</div>
    </div>
  );
};
