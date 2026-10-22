import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const body = await request.json();
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    console.log("Chat with backend URL:", backendUrl);
    console.log("Auth header present:", !!authHeader);
    console.log("Agentic mode:", body.agentic);

    const response = await fetch(`${backendUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader || "",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    console.log("Chat response status:", response.status);

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Chat error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get("session_id");
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    if (sessionId) {
      await fetch(
        `${backendUrl}/api/conversations/${encodeURIComponent(sessionId)}`,
        {
          method: "DELETE",
          headers: { Authorization: authHeader || "" },
        }
      );
    }

    return NextResponse.json({ message: "Chat cleared successfully." });
  } catch (error) {
    console.error("Chat delete error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
