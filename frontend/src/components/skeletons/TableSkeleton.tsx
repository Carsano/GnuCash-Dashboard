export function TableSkeleton() {
  return (
    <div className="skeleton-table" aria-hidden>
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="skeleton-row" />
      ))}
    </div>
  );
}
