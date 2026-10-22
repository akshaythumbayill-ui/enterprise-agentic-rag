import { NextRequest, NextResponse } from "next/server";

export async function DELETE(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const authHeader = request.headers.get("authorization");
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const filename = params.filename;

    console.log(`Deleting document ${filename} via backend: ${backendUrl}`);

    const response = await fetch(
      `${backendUrl}/api/documents/${encodeURIComponent(filename)}`,
      {
        method: "DELETE",
        headers: { Authorization: authHeader || "" },
      }
    );

    const data = await response.json().catch(() => ({}));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Document delete proxy error:", error);
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
