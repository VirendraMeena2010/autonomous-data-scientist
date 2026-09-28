import {
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import {
  forwardRef,
  useId,
  useState,
  type InputHTMLAttributes,
} from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface FieldLabelProps {
  label: string;
  error?: string;
  description?: string;
}

export type TextFieldProps = InputHTMLAttributes<HTMLInputElement> &
  FieldLabelProps;

export type PasswordFieldProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type"
> &
  FieldLabelProps;

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  function TextField(
    { label, error, description, className, id: providedId, ...props },
    ref,
  ) {
    const generatedId = useId();
    const id = providedId ?? generatedId;
    const descriptionId = `${id}-description`;
    const errorId = `${id}-error`;

    return (
      <div className="space-y-2">
        <label
          htmlFor={id}
          className="block text-sm font-medium leading-none text-foreground"
        >
          {label}
        </label>

        <Input
          {...props}
          ref={ref}
          id={id}
          className={className}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={
            error ? errorId : description ? descriptionId : undefined
          }
        />

        {error ? (
          <p
            id={errorId}
            className="flex items-center gap-1.5 text-xs leading-5 text-destructive"
          >
            <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
            {error}
          </p>
        ) : description ? (
          <p
            id={descriptionId}
            className="text-xs leading-5 text-muted-foreground"
          >
            {description}
          </p>
        ) : null}
      </div>
    );
  },
);

export const PasswordField = forwardRef<
  HTMLInputElement,
  PasswordFieldProps
>(function PasswordField(
  {
    label,
    error,
    description,
    className,
    id: providedId,
    autoComplete = "current-password",
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const id = providedId ?? generatedId;
  const descriptionId = `${id}-description`;
  const errorId = `${id}-error`;

  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="space-y-2">
      <label
        htmlFor={id}
        className="block text-sm font-medium leading-none text-foreground"
      >
        {label}
      </label>

      <div className="relative">
        <Input
          {...props}
          ref={ref}
          id={id}
          type={isVisible ? "text" : "password"}
          autoComplete={autoComplete}
          className={cn("pr-11", className)}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={
            error ? errorId : description ? descriptionId : undefined
          }
        />

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1 size-8 text-muted-foreground hover:text-foreground"
          onClick={() => {
            setIsVisible((current) => !current);
          }}
          title={isVisible ? "Hide password" : "Show password"}
          aria-label={isVisible ? "Hide password" : "Show password"}
          aria-controls={id}
          aria-pressed={isVisible}
        >
          {isVisible ? (
            <EyeOff aria-hidden="true" />
          ) : (
            <Eye aria-hidden="true" />
          )}
        </Button>
      </div>

      {error ? (
        <p
          id={errorId}
          className="flex items-center gap-1.5 text-xs leading-5 text-destructive"
        >
          <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
          {error}
        </p>
      ) : description ? (
        <p
          id={descriptionId}
          className="text-xs leading-5 text-muted-foreground"
        >
          {description}
        </p>
      ) : null}
    </div>
  );
});
