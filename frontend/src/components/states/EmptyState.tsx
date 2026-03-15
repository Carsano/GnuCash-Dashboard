export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="state state-empty">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}
