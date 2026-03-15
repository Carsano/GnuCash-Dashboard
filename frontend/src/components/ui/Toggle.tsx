import { useId } from "react";

type Props = {
  checked: boolean;
  label: string;
  onChange: (next: boolean) => void;
};

export function Toggle({ checked, label, onChange }: Props) {
  const id = useId();
  return (
    <label className="toggle" htmlFor={id}>
      <input
        id={id}
        className="focusable"
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}
