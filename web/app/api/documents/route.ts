import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    console.log("Fetching documents with backend URL:", backendUrl);
    console.log("Auth header present:", !!authHeader);

    const response = await fetch(`${backendUrl}/api/documents`, {
      headers: { Authorization: authHeader || "" },
    });

    const data = await response.json();
    console.log("Documents response status:", response.status);

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Documents fetch error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
