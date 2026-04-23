import { NextResponse } from "next/server";

import { getBackendActorHeaders } from "@/lib/api/server-actor";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> }
) {
  if (!API_URL) {
    return NextResponse.json(
      { detail: "Backend API URL is not configured" },
      { status: 500 }
    );
  }

  try {
    const { id } = await context.params;
    const payload = await request.json();
    const actorHeaders = await getBackendActorHeaders();

    const response = await fetch(`${API_URL}/api/users/${id}/role`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...actorHeaders,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const text = await response.text();

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unexpected admin role proxy error";

    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
