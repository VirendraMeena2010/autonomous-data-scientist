import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import * as authApi from "@/api/auth";
import type { User } from "@/types/auth";

export const authQueryKey = ["auth", "current-user"] as const;

export function useCurrentUser() {
  return useQuery({
    queryKey: authQueryKey,
    queryFn: authApi.getCurrentUser,
    staleTime: 5 * 60_000,
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.login,

    onSuccess: async (session) => {
      // Immediately mark the user as authenticated.
      queryClient.setQueryData<User | null>(
        authQueryKey,
        session.user,
      );

      // Re-check the real server session so the frontend and
      // backend are guaranteed to be in sync.
      await queryClient.invalidateQueries({
        queryKey: authQueryKey,
      });
    },
  });
}

export function useSignup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.signup,

    onSuccess: async (session) => {
      queryClient.setQueryData<User | null>(
        authQueryKey,
        session.user,
      );

      await queryClient.invalidateQueries({
        queryKey: authQueryKey,
      });
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      authApi.clearSession();
    },

    onSuccess: () => {
      queryClient.setQueryData<User | null>(
        authQueryKey,
        null,
      );

      queryClient.removeQueries({
        queryKey: authQueryKey,
      });
    },
  });
}

/**
 * Re-exported so components can import the complete auth interface
 * from the hooks layer without duplicating auth state.
 */
export { useAuth } from "@/components/auth/auth-provider";