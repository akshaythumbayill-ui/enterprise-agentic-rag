import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization");
    const formData = await request.formData();
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    // Backend expects 'files' as the field name, rename 'file' to 'files'
    const file = formData.get("file");
    if (file) {
      formData.delete("file");
      formData.append("files", file);
    }

    const response = await fetch(`${backendUrl}/api/documents/upload`, {
      method: "POST",
      headers: { Authorization: authHeader || "" },
      body: formData,
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
