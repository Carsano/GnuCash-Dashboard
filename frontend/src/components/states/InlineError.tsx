import { Button } from "../ui/Button";

type Props = {
  message: string;
  onRetry?: () => void;
};

export function InlineError({ message, onRetry }: Props) {
  return (
    <div className="state state-error" role="alert">
      <strong>Request failed</strong>
      <p>{message}</p>
      {onRetry ? (
        <Button variant="ghost" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
