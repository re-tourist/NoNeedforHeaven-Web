import { describe, expect, it, vi } from "vitest";

import { ApiClientError, HttpGameApi } from "./game";

const STATE_PAYLOAD = {
  revision: 1,
  elapsed_days: 3,
  player: {
    name: "测试角色",
    aptitudes: {
      constitution: 5,
      comprehension: 5,
      spiritual_sense: 5,
      temperament: 5,
      fortune: 5,
    },
    traits: [
      {
        trait_id: "prototype.calm",
        name: "沉着",
        description: "中性测试说明。",
      },
      {
        trait_id: "prototype.steady",
        name: "稳健",
        description: "中性测试说明。",
      },
    ],
  },
};

function jsonResponse(payload: object, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("HttpGameApi", () => {
  it("does not bind the browser fetch function to the API client", async () => {
    const receivers: unknown[] = [];
    const browserFetch = vi.fn(function (this: unknown): Promise<Response> {
      receivers.push(this);
      return Promise.resolve(
        jsonResponse({
          save_exists: false,
          save_available: false,
          session_active: false,
          state: null,
          error: null,
        }),
      );
    });
    vi.stubGlobal("fetch", browserFetch);

    try {
      await new HttpGameApi().getStatus();
    } finally {
      vi.unstubAllGlobals();
    }

    expect(receivers).toEqual([undefined]);
  });

  it("validates the startup status contract", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.resolve(
        jsonResponse({
          save_exists: true,
          save_available: true,
          session_active: false,
          state: null,
          error: null,
        }),
      ),
    );

    await expect(new HttpGameApi(fetcher).getStatus()).resolves.toEqual({
      save_exists: true,
      save_available: true,
      session_active: false,
      state: null,
      error: null,
    });
  });

  it("submits wait intent and returns only server-projected state", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.resolve(jsonResponse({ state: STATE_PAYLOAD })),
    );
    const api = new HttpGameApi(fetcher);

    const state = await api.wait({ days: 3, expected_revision: 0 });

    expect(state.elapsed_days).toBe(3);
    expect(state.revision).toBe(1);
    expect(fetcher).toHaveBeenCalledWith("/api/game/wait", {
      method: "POST",
      body: JSON.stringify({ days: 3, expected_revision: 0 }),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });
  });

  it("preserves stable backend error code and refresh state", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.resolve(
        jsonResponse(
          {
            error: {
              code: "revision_conflict",
              message: "状态已更新。",
              fields: [],
            },
            state: STATE_PAYLOAD,
          },
          409,
        ),
      ),
    );

    const error = await new HttpGameApi(fetcher)
      .wait({ days: 1, expected_revision: 0 })
      .catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiClientError);
    if (!(error instanceof ApiClientError)) {
      throw new Error("预期 ApiClientError。 ");
    }
    expect(error.code).toBe("revision_conflict");
    expect(error.state?.revision).toBe(1);
  });

  it("rejects a successful response with an invalid contract", async () => {
    const fetcher = vi.fn((): Promise<Response> =>
      Promise.resolve(jsonResponse({ state: { revision: "one" } })),
    );

    await expect(
      new HttpGameApi(fetcher).wait({ days: 1, expected_revision: 0 }),
    ).rejects.toMatchObject({ code: "invalid_response" });
  });
});
