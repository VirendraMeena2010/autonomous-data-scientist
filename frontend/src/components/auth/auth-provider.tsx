import {
  createContext,
  useContext,
  type ReactNode,
} from "react";

import {
  useCurrentUser,
  useLogin,
  useLogout,
  useSignup,
} from "@/hooks/use-auth";

import type {
  LoginInput,
  SignupInput,
  User,
} from "@/types/auth";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isLoggingIn: boolean;
  isSigningUp: boolean;
  isLoggingOut: boolean;
  error: Error | null;
  login: (input: LoginInput) => Promise<User | null>;
  signup: (input: SignupInput) => Promise<User | null>;
  logout: () => Promise<void>;
  refresh: () => void;
}

const AuthContext =
  createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const currentUser = useCurrentUser();
  const loginMutation = useLogin();
  const signupMutation = useSignup();
  const logoutMutation = useLogout();

  const user = currentUser.data ?? null;

  /*
   * An old /auth/me 401 should not be treated as an error once
   * we already have an authenticated user.
   */
  const authError =
    user || currentUser.isPending
      ? null
      : currentUser.error;

  return (
    <AuthContext.Provider
      value={{
        user,

        isAuthenticated: Boolean(user),

        isLoading: currentUser.isPending,

        isLoggingIn: loginMutation.isPending,

        isSigningUp: signupMutation.isPending,

        isLoggingOut: logoutMutation.isPending,

        error: authError,

        login: async (input) => {
          const session =
            await loginMutation.mutateAsync(input);

          if (session.user) {
            return session.user;
          }

          /*
           * Fallback in case the login response contains a token
           * but does not include the user object.
           */
          const restoredUser =
            await authApiGetCurrentUser();

          return restoredUser;
        },

        signup: async (input) => {
          const session =
            await signupMutation.mutateAsync(input);

          if (session.user) {
            return session.user;
          }

          const restoredUser =
            await authApiGetCurrentUser();

          return restoredUser;
        },

        logout: async () => {
          await logoutMutation.mutateAsync();
        },

        refresh: () => {
          void currentUser.refetch();
        },
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

async function authApiGetCurrentUser(): Promise<User | null> {
  const { getCurrentUser } =
    await import("@/api/auth");

  const user = await getCurrentUser();

  return user;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within AuthProvider.",
    );
  }

  return context;
}