export interface HealthResponse {
  readonly status: "ok";
  readonly app_id: "buxianxian";
  readonly app_name: "不羡仙";
  readonly version: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isHealthResponse(value: unknown): value is HealthResponse {
  return (
    isRecord(value) &&
    value.status === "ok" &&
    value.app_id === "buxianxian" &&
    value.app_name === "不羡仙" &&
    typeof value.version === "string" &&
    value.version.length > 0
  );
}

export async function fetchHealth(
  fetcher: typeof fetch = fetch,
): Promise<HealthResponse> {
  let response: Response;

  try {
    response = await fetcher("/api/health", {
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new Error("无法连接到不羡仙后端。", { cause: "network_error" });
  }

  if (!response.ok) {
    throw new Error(`不羡仙后端返回 HTTP ${String(response.status)}。`);
  }

  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new Error("不羡仙后端返回了无法解析的数据。", {
      cause: "invalid_json",
    });
  }

  if (!isHealthResponse(payload)) {
    throw new Error("不羡仙后端返回了无效的健康状态。", {
      cause: "invalid_contract",
    });
  }

  return payload;
}
