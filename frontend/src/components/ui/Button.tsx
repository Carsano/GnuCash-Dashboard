import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

export function Button({ variant = "primary", className, ...props }: Props) {
  const variantClass = variant === "primary" ? "btn-primary" : "btn-ghost";
  return <button className={`btn focusable ${variantClass} ${className ?? ""}`} {...props} />;
}
