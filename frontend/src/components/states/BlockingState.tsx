export function BlockingState({ title, body }: { title: string; body: string }) {
  return (
    <div className="state state-blocking" role="alert">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}
