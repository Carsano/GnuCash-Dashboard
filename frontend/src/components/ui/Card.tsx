import type { ReactNode } from "react";

type Props = {
  label: string;
  value: string;
  sub?: ReactNode;
};

export function Card({ label, value, sub }: Props) {
  return (
    <article className="card stagger-in">
      <div className="card-label">{label}</div>
      <div className="card-value">{value}</div>
      {sub ? <div className="card-sub">{sub}</div> : null}
    </article>
  );
}
