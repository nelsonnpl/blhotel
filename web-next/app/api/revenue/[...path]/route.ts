import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.REVENUE_BACKEND_URL ?? "http://127.0.0.1:5000";

async function proxy(req: NextRequest, params: { path: string[] }) {
  const path = params.path?.join("/") ?? "";
  const url = new URL(`/api/${path}`, BACKEND);
  req.nextUrl.searchParams.forEach((value, key) => url.searchParams.set(key, value));

  const init: RequestInit = {
    method: req.method,
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }

  try {
    const response = await fetch(url, init);
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch (error) {
    return NextResponse.json(
      { error: `Proxy backend error: ${error instanceof Error ? error.message : String(error)}` },
      { status: 502 },
    );
  }
}

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(req, params);
}

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(req, params);
}

export async function PUT(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(req, params);
}

export async function DELETE(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(req, params);
}
