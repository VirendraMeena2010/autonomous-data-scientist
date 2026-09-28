import { ApiError, apiRequest, isRecord, setAccessToken } from "@/api/client";
import type {
  AuthSession,
  LoginInput,
  SignupInput,
  User,
} from "@/types/auth";

interface AuthResponse {
  accessToken: string | null;
  user: User | null;
}

function isUserPayload(value: unknown): value is User {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.email === "string"
  );
}

function readAccessToken(payload: unknown): string | null {
  if (!isRecord(payload)) {
    return null;
  }

  const nestedData = isRecord(payload.data) ? payload.data : null;

  const candidate =
    payload.access_token ??
    payload.accessToken ??
    payload.token ??
    nestedData?.access_token ??
    nestedData?.accessToken ??
    nestedData?.token;

  return typeof candidate === "string" && candidate.trim()
    ? candidate.trim()
    : null;
}

function readUser(
  payload: unknown,
  fallback: User | null,
): User | null {
  if (!isRecord(payload)) {
    return fallback;
  }

  const nestedData = isRecord(payload.data) ? payload.data : null;

  const candidates: unknown[] = [
    payload.user,
    nestedData?.user,
    nestedData,
    payload,
  ];

  return candidates.find(isUserPayload) ?? fallback;
}

function normalizeAuthResponse(
  payload: unknown,
  fallback: User | null = null,
): AuthResponse {
  return {
    accessToken: readAccessToken(payload),
    user: readUser(payload, fallback),
  };
}

export async function login(input: LoginInput): Promise<AuthSession> {
  const payload = await apiRequest<unknown>("auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });

  const session = normalizeAuthResponse(payload);

  setAccessToken(session.accessToken);

  return session;
}

export async function signup(input: SignupInput): Promise<AuthSession> {
  const payload = await apiRequest<unknown>("auth/signup", {
    method: "POST",
    body: JSON.stringify(input),
  });

  const session = normalizeAuthResponse(payload);

  setAccessToken(session.accessToken);

  return session;
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    const payload = await apiRequest<unknown>("auth/me");

    const accessToken = readAccessToken(payload);

    if (accessToken) {
      setAccessToken(accessToken);
    }

    return readUser(payload, null);
  } catch (error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      setAccessToken(null);
      return null;
    }

    throw error;
  }
}

export function clearSession(): void {
  setAccessToken(null);
}
