import { LoaderCircle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { AuthError } from "@/components/auth/auth-error";
import { AuthLayout } from "@/components/auth/auth-layout";
import {
  PasswordField,
  TextField,
} from "@/components/auth/form-field";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { getErrorMessage } from "@/types/auth";

interface SignupValues {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

type SignupErrors = Partial<Record<keyof SignupValues, string>>;
// Add a specific type for the touched fields state
type SignupTouched = Partial<Record<keyof SignupValues, boolean>>;

function validateSignup(values: SignupValues): SignupErrors {
  const errors: SignupErrors = {};
  const name = values.name.trim();
  const email = values.email.trim();

  if (!name) {
    errors.name = "Enter your name.";
  } else if (name.length < 2) {
    errors.name = "Enter at least 2 characters.";
  }

  if (!email) {
    errors.email = "Enter your email address.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!values.password) {
    errors.password = "Create a password.";
  } else if (values.password.length < 8) {
    errors.password = "Use at least 8 characters.";
  } else if (!/[A-Za-z]/.test(values.password)) {
    errors.password = "Include at least one letter.";
  } else if (!/\d/.test(values.password)) {
    errors.password = "Include at least one number.";
  }

  if (
    values.confirmPassword &&
    values.password !== values.confirmPassword
  ) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}

export default function Signup() {
  const navigate = useNavigate();
  const { signup, isSigningUp } = useAuth();

  const [values, setValues] = useState<SignupValues>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  // Update this line to use the new SignupTouched type instead of SignupErrors
  const [touched, setTouched] = useState<SignupTouched>({});
  const [actionError, setActionError] = useState<string | null>(null);

  const errors = validateSignup(values);
  const isSubmitting = isSigningUp;

  function updateField<Field extends keyof SignupValues>(
    field: Field,
    value: SignupValues[Field],
  ) {
    setValues((current) => ({
      ...current,
      [field]: value,
    }));

    setActionError(null);
  }

  function markTouched(field: keyof SignupValues) {
    setTouched((current) => ({
      ...current,
      [field]: true,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setTouched({
      name: true,
      email: true,
      password: true,
      confirmPassword: true,
    });

    setActionError(null);

    const validationErrors = validateSignup(values);
    const firstInvalidField = (
      Object.keys(validationErrors) as (keyof SignupValues)[]
    ).find((field) => validationErrors[field]);

    if (firstInvalidField) {
      document.getElementById(firstInvalidField)?.focus();
      return;
    }

    try {
      const user = await signup({
        name: values.name.trim(),
        email: values.email.trim(),
        password: values.password,
      });

      if (user) {
        navigate("/projects", { replace: true });
        return;
      }

      toast.success("Account created. Sign in to continue.");

      navigate(
        `/login?email=${encodeURIComponent(values.email.trim())}`,
        { replace: true },
      );
    } catch (error: unknown) {
      setActionError(getErrorMessage(error));
    }
  }

  return (
    <AuthLayout>
      <header className="mb-8">
        <p className="mb-3 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          Your analysis workspace
        </p>
        <h1 className="text-3xl font-semibold tracking-[-0.035em]">
          Create your account
        </h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          Start turning questions into evidence-backed insights.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        noValidate
        aria-busy={isSubmitting}
        className="space-y-5"
      >
        {actionError && <AuthError message={actionError} />}

        <TextField
          id="name"
          name="name"
          label="Name"
          autoComplete="name"
          placeholder="Your full name"
          maxLength={120}
          value={values.name}
          onChange={(event) => {
            updateField("name", event.target.value);
          }}
          onBlur={() => {
            markTouched("name");
          }}
          error={touched.name ? errors.name : undefined}
          disabled={isSubmitting}
          autoFocus
        />

        <TextField
          id="email"
          name="email"
          label="Email"
          type="email"
          inputMode="email"
          autoComplete="email"
          placeholder="you@company.com"
          value={values.email}
          onChange={(event) => {
            updateField("email", event.target.value);
          }}
          onBlur={() => {
            markTouched("email");
          }}
          error={touched.email ? errors.email : undefined}
          disabled={isSubmitting}
        />

        <PasswordField
          id="password"
          name="password"
          label="Password"
          autoComplete="new-password"
          placeholder="Create a secure password"
          value={values.password}
          onChange={(event) => {
            updateField("password", event.target.value);
          }}
          onBlur={() => {
            markTouched("password");
          }}
          error={touched.password ? errors.password : undefined}
          description="Use at least 8 characters with a letter and a number."
          disabled={isSubmitting}
        />

        <PasswordField
          id="confirmPassword"
          name="confirmPassword"
          label="Confirm password"
          autoComplete="new-password"
          placeholder="Enter your password again"
          value={values.confirmPassword}
          onChange={(event) => {
            updateField("confirmPassword", event.target.value);
          }}
          onBlur={() => {
            markTouched("confirmPassword");
          }}
          error={
            touched.confirmPassword ? errors.confirmPassword : undefined
          }
          disabled={isSubmitting}
        />

        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={isSubmitting}
        >
          {isSubmitting && (
            <LoaderCircle
              className="animate-spin"
              aria-hidden="true"
            />
          )}
          {isSubmitting ? "Creating account…" : "Create Account"}
        </Button>
      </form>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          to="/login"
          className="font-medium text-foreground underline-offset-4 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}