import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const formData = await request.formData();
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    console.log("Upload with backend URL:", backendUrl);
    console.log("Auth header present:", !!authHeader);

    // Backend expects 'files' as the field name (list of files)
    const file = formData.get("file");
    if (!file) {
      return NextResponse.json(
        { detail: "No file provided" },
        { status: 400 }
      );
    }

    // Create new FormData with correct field name
    const newFormData = new FormData();
    newFormData.append("files", file);

    const response = await fetch(`${backendUrl}/api/documents/upload`, {
      method: "POST",
      headers: { Authorization: authHeader || "" },
      body: newFormData,
    });

    // Handle 502 Bad Gateway (backend down)
    if (response.status === 502) {
      console.error("Backend is down (502)");
      return NextResponse.json(
        { detail: "Backend service is temporarily unavailable. Please try again in a few moments." },
        { status: 503 }
      );
    }

    // Handle 401 Unauthorized
    if (response.status === 401) {
      console.error("Authentication failed (401)");
      return NextResponse.json(
        { detail: "Authentication failed. Please log in again." },
        { status: 401 }
      );
    }

    const contentType = response.headers.get("content-type");
    console.log("Upload response status:", response.status);
    console.log("Response content-type:", contentType);

    // Check if response is JSON
    if (!contentType || !contentType.includes("application/json")) {
      const text = await response.text();
      console.error("Non-JSON response from backend:", text.substring(0, 500));
      return NextResponse.json(
        { detail: "Backend returned an error. The service may be restarting. Please try again in a few moments." },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json(
      { detail: "Network error: Unable to connect to backend. The service may be down." },
      { status: 503 }
    );
  }
}
