"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, Trash2, FileText, Loader2 } from "lucide-react";
import AppLayout from "@/components/AppLayout";

interface Document {
  filename: string;
  size_bytes: number;
  uploaded_at: string;
}

export default function KnowledgeBasePage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [uploadedDocs, setUploadedDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  const showToast = (text: string, type: "success" | "error" = "success") => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 3500);
  };

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
    } else {
      setToken(storedToken);
      fetchDocuments(storedToken);
    }
  }, [router]);

  const fetchDocuments = async (authToken: string) => {
    try {
      const response = await fetch("/api/documents", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (response.ok) {
        const data = await response.json();
        setUploadedDocs(data.documents || []);
      } else if (response.status === 401) {
        console.error("Authentication failed - token may be expired");
        showToast("Session expired. Please log in again.", "error");
        router.push("/login");
      } else {
        console.error("Failed to fetch documents:", response.status);
        showToast(`Failed to fetch documents: ${response.status}`, "error");
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
      showToast("Network error. Please check your connection.", "error");
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentFile || !token) return;

    const formData = new FormData();
    formData.append("file", documentFile);

    setUploading(true);
    try {
      const response = await fetch("/api/documents/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setDocumentFile(null);
        fetchDocuments(token);
        showToast("Document uploaded successfully!");
      } else if (response.status === 401) {
        showToast("Session expired. Please log in again.", "error");
        router.push("/login");
      } else {
        showToast(`Upload failed: ${data.detail || "Unknown error"}`, "error");
      }
    } catch (err) {
      console.error("Upload failed", err);
      showToast("Upload failed: Connection error", "error");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (filename: string) => {
    if (!token) return;
    const confirmed = window.confirm(
      `Are you sure you want to delete "${filename}"? This will update your knowledge base index.`
    );
    if (!confirmed) return;

    setDeletingDoc(filename);
    try {
      const response = await fetch(
        `/api/documents/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        showToast(`"${filename}" was deleted successfully.`);
        fetchDocuments(token);
      } else {
        const data = await response.json().catch(() => ({}));
        showToast(data.detail || `Failed to delete "${filename}"`, "error");
      }
    } catch (err) {
      console.error("Delete document error:", err);
      showToast("Connection error while deleting document.", "error");
    } finally {
      setDeletingDoc(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <AppLayout>
      <div className="min-h-screen">
        {/* Header */}
        <header className="header">
          <div>
            <h1 className="text-h1">Knowledge Base</h1>
            <p className="text-muted mt-1">
              Manage your documents and knowledge sources
            </p>
          </div>
        </header>

        {/* Main content */}
        <main className="container-app py-6">
          {/* Upload section */}
          <div className="card mb-6">
            <div className="card-header">
              <h2 className="text-h3">Upload Document</h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleUpload} className="flex items-end gap-4">
                <div className="flex-1">
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) =>
                      setDocumentFile(e.target.files?.[0] || null)
                    }
                    className="input"
                    disabled={uploading}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!documentFile || uploading}
                  className="btn btn-primary"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload
                    </>
                  )}
                </button>
              </form>
              {documentFile && (
                <p className="text-xs text-text-secondary mt-2">
                  Selected: {documentFile.name} ({formatFileSize(documentFile.size)})
                </p>
              )}
            </div>
          </div>

          {/* Documents table */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-h3">Uploaded Documents</h2>
            </div>
            <div className="card-body p-0">
              {uploadedDocs.length === 0 ? (
                <div className="p-12 text-center">
                  <FileText className="w-12 h-12 text-text-secondary mx-auto mb-4" />
                  <p className="text-muted">No documents uploaded yet</p>
                  <p className="text-xs text-text-secondary mt-2">
                    Upload a PDF to get started
                  </p>
                </div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Size</th>
                      <th>Uploaded</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploadedDocs.map((doc) => (
                      <tr key={doc.filename}>
                        <td className="font-medium text-text-primary">
                          {doc.filename}
                        </td>
                        <td className="text-text-secondary">
                          {formatFileSize(doc.size_bytes)}
                        </td>
                        <td className="text-text-secondary">
                          {formatDate(doc.uploaded_at)}
                        </td>
                        <td className="text-right">
                          <button
                            onClick={() => handleDeleteDocument(doc.filename)}
                            disabled={deletingDoc === doc.filename}
                            className="btn btn-ghost p-2 text-error hover:bg-red-50"
                            title="Delete document"
                          >
                            {deletingDoc === doc.filename ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </main>

        {/* Toast notification */}
        {toastMessage && (
          <div
            className={`fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg ${
              toastMessage.type === "success"
                ? "bg-success text-white"
                : "bg-error text-white"
            }`}
          >
            {toastMessage.text}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
