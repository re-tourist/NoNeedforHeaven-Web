import { describe, expect, it, vi } from "vitest";

import { fetchHealth } from "./health";

describe("fetchHealth", () => {
  it("returns a validated 不羡仙 health contract", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            status: "ok",
            app_id: "buxianxian",
            app_name: "不羡仙",
            version: "0.1.0",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(fetchHealth(fetcher)).resolves.toEqual({
      status: "ok",
      app_id: "buxianxian",
      app_name: "不羡仙",
      version: "0.1.0",
    });
    expect(fetcher).toHaveBeenCalledWith("/api/health", {
      headers: { Accept: "application/json" },
    });
  });

  it("rejects a successful response with an invalid contract", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.resolve(
        new Response(JSON.stringify({ status: "ok", app_id: "other" }), {
          status: 200,
        }),
      ),
    );

    await expect(fetchHealth(fetcher)).rejects.toThrow(
      "不羡仙后端返回了无效的健康状态。",
    );
  });

  it("reports an unavailable backend clearly", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.reject(new TypeError("connection refused")),
    );

    await expect(fetchHealth(fetcher)).rejects.toThrow(
      "无法连接到不羡仙后端。",
    );
  });
});
