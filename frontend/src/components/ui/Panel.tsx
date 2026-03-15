import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function Panel({ title, subtitle, actions, children }: Props) {
  return (
    <section className="panel page-enter">
      <header className="panel-header">
        <div>
          <h3>{title}</h3>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}
