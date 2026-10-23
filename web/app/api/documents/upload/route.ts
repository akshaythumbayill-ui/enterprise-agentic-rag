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

    const contentType = response.headers.get("content-type");
    console.log("Upload response status:", response.status);
    console.log("Response content-type:", contentType);

    // Check if response is JSON
    if (!contentType || !contentType.includes("application/json")) {
      const text = await response.text();
      console.error("Non-JSON response from backend:", text.substring(0, 500));
      return NextResponse.json(
        { detail: "Backend returned an error. Please check if the backend is running and has enough memory." },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json(
      { detail: "Internal server error: " + (error as Error).message },
      { status: 500 }
    );
  }
}
