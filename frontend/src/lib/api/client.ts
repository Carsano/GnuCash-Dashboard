export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as unknown;
  if (!response.ok) {
    const errorPayload = payload as {
      error?: { message?: string; details?: unknown };
    };
    throw new ApiError(
      errorPayload.error?.message ?? "Request failed",
      response.status,
      errorPayload.error?.details,
    );
  }
  return payload as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });
  return parseResponse<T>(response);
}
