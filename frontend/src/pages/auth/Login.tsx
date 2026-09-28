import { LoaderCircle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { AuthError } from "@/components/auth/auth-error";
import { AuthLayout } from "@/components/auth/auth-layout";
import {
  PasswordField,
  TextField,
} from "@/components/auth/form-field";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { getErrorMessage } from "@/types/auth";

interface LoginValues {
  email: string;
  password: string;
}

type LoginErrors = Partial<Record<keyof LoginValues, string>>;
type LoginTouched = Partial<Record<keyof LoginValues, boolean>>;

function validateLogin(values: LoginValues): LoginErrors {
  const errors: LoginErrors = {};
  const email = values.email.trim();

  if (!email) {
    errors.email = "Enter your email address.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!values.password) {
    errors.password = "Enter your password.";
  }

  return errors;
}

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isLoggingIn } = useAuth();

  const [values, setValues] = useState<LoginValues>({
    email: searchParams.get("email")?.trim() ?? "",
    password: "",
  });

  const [touched, setTouched] = useState<LoginTouched>({});
  const [actionError, setActionError] = useState<string | null>(null);

  const errors = validateLogin(values);
  const isSubmitting = isLoggingIn;

  // Added proper TypeScript generics for the field and value
  function updateField<K extends keyof LoginValues>(
    field: K,
    value: LoginValues[K],
  ) {
    setValues((current) => ({
      ...current,
      [field]: value,
    }));
    setActionError(null);
  }

  function markTouched(field: keyof LoginValues) {
    setTouched((current) => ({
      ...current,
      [field]: true,
    }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    setTouched({
      email: true,
      password: true,
    });

    setActionError(null);

    const validationErrors = validateLogin(values);

    const firstInvalidField = (
      Object.keys(validationErrors) as (keyof LoginValues)[]
    ).find((field) => validationErrors[field]);

    if (firstInvalidField) {
      document.getElementById(firstInvalidField)?.focus();
      return;
    }

    try {
      console.log("LOGIN: submitting");

      const user = await login({
        email: values.email.trim(),
        password: values.password,
      });

      console.log("LOGIN: user returned", user);

      if (!user) {
        throw new Error(
          "Login succeeded, but the authenticated user was not returned.",
        );
      }

      console.log("LOGIN: navigating to /projects");

      navigate("/projects", {
        replace: true,
      });
    } catch (error: unknown) {
      console.error("LOGIN: failed", error);
      setActionError(getErrorMessage(error));
    }
  }

  return (
    <AuthLayout>
      <header className="mb-8">
        <p className="mb-2 text-sm font-medium text-muted-foreground">
          Analysis workspace
        </p>
        <h1 className="text-3xl font-semibold tracking-[-0.035em]">
          Welcome back
        </h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          Continue your analysis workspace.
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
          id="email"
          name="email"
          label="Email"
          type="email"
          inputMode="email"
          autoComplete="username"
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
          autoFocus
        />

        <PasswordField
          id="password"
          name="password"
          label="Password"
          placeholder="Enter your password"
          value={values.password}
          onChange={(event) => {
            updateField("password", event.target.value);
          }}
          onBlur={() => {
            markTouched("password");
          }}
          error={touched.password ? errors.password : undefined}
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
              className="mr-2 h-4 w-4 animate-spin"
              aria-hidden="true"
            />
          )}

          {isSubmitting ? "Signing in…" : "Sign In"}
        </Button>
      </form>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link
          to="/signup"
          className="font-medium text-foreground underline-offset-4 hover:underline"
        >
          Create one
        </Link>
      </p>
    </AuthLayout>
  );
}