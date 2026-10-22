"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [uploadedDocs, setUploadedDocs] = useState<string[]>([]);
  const [agenticMode, setAgenticMode] = useState(false);
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [clearingChat, setClearingChat] = useState(false);
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
        const docs = (data.documents || []).map((doc: any) => doc.filename);
        setUploadedDocs(docs);
      } else {
        console.error("Failed to fetch documents:", response.status);
      }
    } catch (err) {
      console.error("Failed to fetch documents", err);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentFile || !token) return;

    const formData = new FormData();
    formData.append("file", documentFile);

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
      } else {
        showToast(`Upload failed: ${data.detail || "Unknown error"}`, "error");
      }
    } catch (err) {
      console.error("Upload failed", err);
      showToast("Upload failed: Connection error", "error");
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

  const handleClearChat = async () => {
    if (messages.length === 0) return;
    const confirmed = window.confirm(
      "Are you sure you want to clear this conversation history?"
    );
    if (!confirmed) return;

    setClearingChat(true);
    try {
      if (token && sessionId) {
        await fetch(
          `/api/conversations/${encodeURIComponent(sessionId)}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          }
        ).catch((err) => console.warn("Delete conversation error:", err));
      }

      setMessages([]);
      setSessionId(null);
      showToast("Conversation cleared successfully.");
    } catch (err) {
      console.error("Clear chat error:", err);
      setMessages([]);
      setSessionId(null);
    } finally {
      setClearingChat(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !token) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: currentInput,
          agentic: agenticMode,
          session_id: sessionId || undefined,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        if (data.session_id) {
          setSessionId(data.session_id);
        }
        const assistantMessage: Message = {
          role: "assistant",
          content: data.answer || "No response received",
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        const assistantMessage: Message = {
          role: "assistant",
          content: `Error: ${data.detail || "Failed to get response"}`,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error: Connection failed. Please check if the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  return (
    <div className="min-h-screen gradient-bg">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          className={`fixed top-20 right-6 z-50 px-4 py-3 rounded-xl backdrop-blur-xl border shadow-2xl flex items-center space-x-2 text-sm text-white transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${
            toastMessage.type === "error"
              ? "bg-red-500/90 border-red-400"
              : "bg-emerald-600/90 border-emerald-400"
          }`}
        >
          <span>{toastMessage.type === "error" ? "⚠️" : "✅"}</span>
          <span>{toastMessage.text}</span>
        </div>
      )}

      <nav className="bg-[#08110d]/95 backdrop-blur-xl border-b border-emerald-100/15 px-6 py-4 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center ring-1 ring-emerald-300/40">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-white">Cogniflow</h1>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 bg-white/5 hover:bg-red-500/15 text-white px-4 py-2 rounded-lg transition-all duration-200 border border-emerald-100/20 hover:border-red-300/30"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Document Upload Section */}
          <div className="glass-card p-6 flex flex-col">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-white">Upload Documents</h2>
            </div>
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="relative">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setDocumentFile(e.target.files?.[0] || null)}
                  className="w-full text-emerald-50/80 text-sm file:mr-4 file:py-3 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-600 file:text-white file:font-medium hover:file:bg-emerald-500 file:cursor-pointer file:transition-all file:duration-200"
                />
              </div>
              <button
                type="submit"
                disabled={!documentFile}
                className="btn-primary w-full flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <span>Upload PDF</span>
              </button>
            </form>

            <div className="mt-8 flex-1">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white">Uploaded Documents</h3>
              </div>
              {uploadedDocs.length === 0 ? (
                <div className="text-center py-8 px-4 bg-black/20 rounded-lg border border-emerald-100/15">
                  <svg className="w-12 h-12 text-emerald-100/30 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-emerald-100/55 text-sm">No documents uploaded yet</p>
                </div>
              ) : (
                <ul className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
                  {uploadedDocs.map((doc) => (
                    <li
                      key={doc}
                      className="group flex items-center justify-between bg-black/20 rounded-lg px-4 py-3 text-white text-sm border border-emerald-100/15 hover:bg-emerald-400/10 transition-all duration-200"
                    >
                      <div className="flex items-center space-x-3 overflow-hidden mr-2">
                        <svg className="w-5 h-5 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zm-3 9v2h2v-2H10zm-2 0H6v2h2v-2zm4 0h2v2h-2v-2zm-4 4H6v2h2v-2zm2 0h2v2h-2v-2zm4 0h2v2h-2v-2z" />
                        </svg>
                        <span className="truncate" title={doc}>
                          {doc}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteDocument(doc)}
                        disabled={deletingDoc === doc}
                        title={`Delete ${doc}`}
                        aria-label={`Remove ${doc}`}
                        className="flex items-center gap-1.5 text-emerald-100/60 hover:text-red-200 hover:bg-red-500/15 px-2 py-1.5 rounded-md transition-colors duration-150 flex-shrink-0 disabled:opacity-50"
                      >
                        {deletingDoc === doc ? (
                          <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            <span className="text-xs font-medium">Remove</span>
                          </>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Chat Section */}
          <div className="lg:col-span-2 glass-card p-6 flex flex-col h-[700px]">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-emerald-100/15">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-white">AI Chat</h2>
              </div>
              <div className="flex items-center space-x-4">
                {/* Clear Chat Button */}
                <button
                  onClick={handleClearChat}
                  disabled={messages.length === 0 || clearingChat}
                  title="Clear chat messages and history"
                  aria-label="Clear chat messages and history"
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-emerald-50/80 hover:text-red-200 bg-black/20 hover:bg-red-500/15 border border-emerald-100/15 hover:border-red-400/30 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  {clearingChat ? (
                    <div className="w-3.5 h-3.5 border-2 border-red-300 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  )}
                  <span>Clear Chat</span>
                </button>

                {/* Agentic Mode Toggle */}
                <div className="flex items-center space-x-2 pl-2 border-l border-emerald-100/15">
                  <span className="text-emerald-50/75 text-sm">Agentic Mode</span>
                  <button
                    onClick={() => setAgenticMode(!agenticMode)}
                    aria-label="Toggle agentic mode"
                    aria-pressed={agenticMode}
                    className={`relative w-14 h-7 rounded-full transition-colors duration-200 ${
                      agenticMode ? "bg-emerald-600" : "bg-white/20"
                    }`}
                  >
                    <span
                      className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform duration-200 ${
                        agenticMode ? "translate-x-7" : "translate-x-0"
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
              {messages.length === 0 ? (
                <div className="text-center py-16 px-4">
                  <div className="w-16 h-16 bg-emerald-600 rounded-xl mx-auto mb-4 flex items-center justify-center shadow-lg shadow-emerald-950/40">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <p className="text-emerald-50/85 text-lg mb-2">Start a conversation</p>
                  <p className="text-emerald-100/55 text-sm">Ask questions about your uploaded documents or search the web</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                        msg.role === "user"
                          ? "bg-emerald-600 text-white shadow-lg shadow-emerald-950/40"
                          : "bg-black/20 text-white border border-emerald-100/20"
                      }`}
                    >
                      {msg.role === "assistant" ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                            li: ({ children }) => <li className="ml-2">{children}</li>,
                            code: ({ children }) => (
                              <code className="bg-emerald-500/15 px-1.5 py-0.5 rounded text-sm font-mono">
                                {children}
                              </code>
                            ),
                            pre: ({ children }) => (
                              <pre className="bg-black/30 p-3 rounded-lg overflow-x-auto mb-2">
                                {children}
                              </pre>
                            ),
                            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                            a: ({ children, href }) => (
                              <a href={href} className="text-emerald-300 hover:text-emerald-200 underline" target="_blank" rel="noopener noreferrer">
                                {children}
                              </a>
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      ) : (
                        msg.content
                      )}
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-black/20 rounded-xl px-5 py-3 text-white border border-emerald-100/20">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <form onSubmit={handleSendMessage} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={agenticMode ? "Ask a complex question (agentic mode enabled)..." : "Ask a question about your documents or search..."}
                className="flex-1 input-field"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="btn-primary flex items-center space-x-2 px-6 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Send</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </form>
            {agenticMode && (
              <div className="mt-3 text-center text-emerald-100/60 text-sm">
                <span className="inline-flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Agentic mode: Multi-step reasoning with web search enabled</span>
                </span>
              </div>
            )}
            {!agenticMode && (
              <div className="mt-3 text-center text-emerald-100/60 text-sm">
                <span className="inline-flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Simple mode: Fast responses using document search only</span>
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
