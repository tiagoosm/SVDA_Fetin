import clsx from 'clsx';
import { useId } from 'react';
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react';

interface FieldShellProps {
  id: string;
  label: string;
  hint?: string;
  children: ReactNode;
}

function FieldShell({ id, label, hint, children }: FieldShellProps) {
  return (
    <div className="grid gap-1.5">
      <label htmlFor={id} className="text-sm font-semibold text-moss">
        {label}
        {hint ? <span className="ml-1 font-normal text-muted">{hint}</span> : null}
      </label>
      {children}
    </div>
  );
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export function TextField({ label, hint, className, ...props }: TextFieldProps) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} hint={hint}>
      <input id={id} className={clsx('field-control', className)} {...props} />
    </FieldShell>
  );
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: { value: string; label: string }[];
  placeholder: string;
}

export function SelectField({
  label,
  options,
  placeholder,
  className,
  ...props
}: SelectFieldProps) {
  const id = useId();
  return (
    <FieldShell id={id} label={label}>
      <select id={id} className={clsx('field-control field-select', className)} {...props}>
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </FieldShell>
  );
}
