const configuredBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() ||
  "http://localhost:8000";

const normalizedBaseUrl = configuredBaseUrl.replace(/\/+$/, "");

const apiBaseUrl = new URL(
  "api/v1/",
  `${normalizedBaseUrl}/`,
).toString();

let accessToken: string | null = null;

export class ApiError extends Error {
  readonly status: number;
  readonly details: unknown;

  constructor(
    status: number,
    message: string,
    details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

function getErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return "The request could not be processed. Check your input and try again.";

    case 401:
      return "Your session has expired. Please sign in again.";

    case 403:
      return "You do not have permission to perform this action.";

    case 404:
      return "The requested resource could not be found.";

    case 409:
      return "This action conflicts with the current state of the resource.";

    case 422:
      return "Please check the information you provided and try again.";

    case 429:
      return "Too many requests. Please wait a moment and try again.";

    default:
      return status >= 500
        ? "The server could not complete the request. Please try again."
        : "Something went wrong. Please try again.";
  }
}

function resolveUrl(path: string): string {
  const relativePath = path.replace(/^\/+/, "");

  return new URL(
    relativePath,
    apiBaseUrl,
  ).toString();
}

function getFilename(
  contentDisposition: string | null,
  fallback: string,
): string {
  if (!contentDisposition) {
    return fallback;
  }

  const encodedMatch = contentDisposition.match(
    /filename\*\s*=\s*UTF-8''([^;]+)/i,
  );

  if (encodedMatch?.[1]) {
    try {
      return decodeURIComponent(
        encodedMatch[1]
          .trim()
          .replace(/^"|"$/g, ""),
      );
    } catch {
      return fallback;
    }
  }

  const regularMatch = contentDisposition.match(
    /filename\s*=\s*(?:"([^"]+)"|([^;]+))/i,
  );

  const filename =
    regularMatch?.[1] ??
    regularMatch?.[2]?.trim();

  return filename || fallback;
}

async function parseResponse(
  response: Response,
): Promise<unknown | undefined> {
  if (response.status === 204) {
    return undefined;
  }

  const contentType =
    response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      throw new ApiError(
        response.status,
        getErrorMessage(response.status),
      );
    }
  }

  const text = await response.text();

  return text || undefined;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);

  const isFormData =
    init.body instanceof FormData;

  if (
    init.body !== undefined &&
    !isFormData &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (!headers.has("Accept")) {
    headers.set(
      "Accept",
      "application/json",
    );
  }

  if (accessToken) {
    headers.set(
      "Authorization",
      accessToken
        .toLowerCase()
        .startsWith("bearer ")
        ? accessToken
        : `Bearer ${accessToken}`,
    );
  }

  let response: Response;

  try {
    response = await fetch(
      resolveUrl(path),
      {
        ...init,
        headers,
        credentials: "include",
      },
    );
  } catch (error: unknown) {
    if (
      error instanceof DOMException &&
      (
        error.name === "AbortError" ||
        error.name === "TimeoutError"
      )
    ) {
      throw error;
    }

    throw new ApiError(
      0,
      "Unable to reach the server. Check your connection and try again.",
    );
  }

  const payload = await parseResponse(response);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      getErrorMessage(response.status),
      payload,
    );
  }

  return payload as T;
}

export interface ApiDownload {
  blob: Blob;
  filename: string;
}

export async function apiDownload(
  path: string,
): Promise<ApiDownload> {
  const headers = new Headers({
    Accept: "*/*",
  });

  if (accessToken) {
    headers.set(
      "Authorization",
      accessToken
        .toLowerCase()
        .startsWith("bearer ")
        ? accessToken
        : `Bearer ${accessToken}`,
    );
  }

  let response: Response;

  try {
    response = await fetch(
      resolveUrl(path),
      {
        headers,
        credentials: "include",
      },
    );
  } catch (error: unknown) {
    if (
      error instanceof DOMException &&
      (
        error.name === "AbortError" ||
        error.name === "TimeoutError"
      )
    ) {
      throw error;
    }

    throw new ApiError(
      0,
      "Unable to reach the server. Check your connection and try again.",
    );
  }

  if (!response.ok) {
    const payload = await parseResponse(response);

    throw new ApiError(
      response.status,
      getErrorMessage(response.status),
      payload,
    );
  }

  return {
    blob: await response.blob(),
    filename: getFilename(
      response.headers.get("content-disposition"),
      "analysis-export",
    ),
  };
}