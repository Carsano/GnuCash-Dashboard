export function KpiSkeleton() {
  return (
    <div className="kpi-grid" aria-hidden>
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="skeleton-card" />
      ))}
    </div>
  );
}
