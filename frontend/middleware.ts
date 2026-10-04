import { NextRequest, NextResponse } from "next/server";
import { isLocalHost } from "./src/shared/server/local-access.mjs";

export function middleware(request: NextRequest) {
  if (!isLocalHost(request.headers.get("host"))) {
    return NextResponse.json(
      {
        error: {
          code: "local_only",
          message: "This workbench accepts loopback access only.",
        },
      },
      { status: 403 },
    );
  }
  return NextResponse.next();
}

export const config = { matcher: "/:path*" };
