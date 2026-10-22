"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Loader2, Sparkles, FileText } from "lucide-react";
import AppLayout from "@/components/AppLayout";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{
    filename: string;
    similarity: number;
  }>;
}

export default function AssistantPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agenticMode, setAgenticMode] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [hasDocuments, setHasDocuments] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
    } else {
      setToken(storedToken);
      // Check if user has documents
      fetch("/api/documents", {
        headers: { Authorization: `Bearer ${storedToken}` },
      })
        .then((res) => res.json())
        .then((data) => {
          const docs = data.documents || [];
          setHasDocuments(docs.length > 0);
        })
        .catch((err) => console.error("Failed to check documents:", err));
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !token || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: userMessage,
          session_id: sessionId,
          agentic: agenticMode,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        if (!sessionId && data.session_id) {
          setSessionId(data.session_id);
        }

        console.log("Chat response:", data);
        console.log("Sources:", data.sources);

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.answer,
            sources: data.sources || [],
          },
        ]);
      } else if (response.status === 401) {
        console.error("Authentication failed - token may be expired");
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Your session has expired. Please log in again.",
          },
        ]);
        setTimeout(() => router.push("/login"), 2000);
      } else {
        console.error("Chat error response:", data);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${data.detail || "Failed to get response"}`,
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error: Failed to connect to the server",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (messages.length === 0) return;
    const confirmed = window.confirm(
      "Are you sure you want to clear this conversation?"
    );
    if (!confirmed) return;

    try {
      if (token && sessionId) {
        await fetch(`/api/conversations/${encodeURIComponent(sessionId)}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }).catch((err) => console.warn("Delete conversation error:", err));
      }

      setMessages([]);
      setSessionId(null);
    } catch (err) {
      console.error("Clear chat error:", err);
      setMessages([]);
      setSessionId(null);
    }
  };

  const suggestedPrompts = [
    "Summarize the employee handbook",
    "Explain the company travel policy",
    "Find information about benefits",
    "What are the security protocols?",
  ];

  return (
    <AppLayout>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <header className="header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-h1">AI Assistant</h1>
              <p className="text-muted mt-1">
                Ask questions about your documents
              </p>
            </div>
            <button
              onClick={handleClearChat}
              disabled={messages.length === 0}
              className="btn btn-ghost text-sm"
            >
              Clear Chat
            </button>
          </div>
        </header>

        {/* Main content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat area */}
          <div className="flex-1 flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {messages.length === 0 ? (
                <div className="max-w-2xl mx-auto py-12">
                  <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Sparkles className="w-8 h-8 text-blue-600" />
                    </div>
                    <h2 className="text-h2 mb-2">Start a conversation</h2>
                    <p className="text-muted">
                      {hasDocuments
                        ? "Ask questions about your uploaded documents"
                        : "Upload documents to start asking questions"}
                    </p>
                  </div>

                  {!hasDocuments && (
                    <div className="text-center mb-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        <strong>No documents uploaded yet.</strong> Go to the
                        Knowledge Base to upload PDFs first.
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {suggestedPrompts.map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => setInput(prompt)}
                        className="text-left p-4 rounded-lg border border-gray-200 hover:border-blue-600 hover:bg-blue-50 transition-colors"
                      >
                        <p className="text-sm text-gray-900">{prompt}</p>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="max-w-4xl mx-auto space-y-6">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${
                        msg.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[85%] lg:max-w-[75%] rounded-lg px-4 py-3 ${
                          msg.role === "user"
                            ? "bg-blue-600 text-white shadow-sm"
                            : "bg-white border border-gray-200"
                        }`}
                      >
                        {msg.role === "assistant" ? (
                          <div className="prose prose-sm max-w-none">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                p: ({ children }) => (
                                  <p className="mb-2 last:mb-0">{children}</p>
                                ),
                                ul: ({ children }) => (
                                  <ul className="list-disc list-inside mb-2 space-y-1 ml-4">
                                    {children}
                                  </ul>
                                ),
                                ol: ({ children }) => (
                                  <ol className="list-decimal list-inside mb-2 space-y-1 ml-4">
                                    {children}
                                  </ol>
                                ),
                                code: ({ children }) => (
                                  <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">
                                    {children}
                                  </code>
                                ),
                                pre: ({ children }) => (
                                  <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto mb-2 text-sm">
                                    {children}
                                  </pre>
                                ),
                                strong: ({ children }) => (
                                  <strong className="font-semibold">
                                    {children}
                                  </strong>
                                ),
                                a: ({ children, href }) => (
                                  <a
                                    href={href}
                                    className="text-primary hover:underline"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                  >
                                    {children}
                                  </a>
                                ),
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>

                            {msg.sources && msg.sources.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-gray-200">
                                <button
                                  onClick={() => setShowSources(!showSources)}
                                  className="flex items-center gap-2 text-xs text-gray-600 hover:text-gray-900 transition-colors"
                                >
                                  <FileText className="w-3 h-3" />
                                  <span>
                                    {msg.sources.length} source(s)
                                  </span>
                                </button>

                                {showSources && (
                                  <div className="mt-2 space-y-1">
                                    {msg.sources.map((source, i) => (
                                      <div
                                        key={i}
                                        className="text-xs text-gray-600 flex items-center gap-2"
                                      >
                                        <FileText className="w-3 h-3" />
                                        <span>{source.filename}</span>
                                        <span className="text-gray-400">
                                          ({(source.similarity * 100).toFixed(1)}%)
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        ) : (
                          <p className="text-sm leading-relaxed">{msg.content}</p>
                        )}
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-surface border border-border rounded-lg px-4 py-3">
                        <Loader2 className="w-5 h-5 text-text-secondary animate-spin" />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Input area */}
            <div className="border-t border-border bg-surface p-4">
              <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                <div className="flex items-end gap-3">
                  <div className="flex-1">
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSubmit(e);
                        }
                      }}
                      placeholder="Ask a question..."
                      rows={1}
                      className="input resize-none"
                      disabled={loading}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={!input.trim() || loading}
                    className="btn btn-primary h-10 px-4"
                  >
                    {loading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>

                <div className="flex items-center justify-between mt-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={agenticMode}
                      onChange={(e) => setAgenticMode(e.target.checked)}
                      className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                    />
                    <span className="text-sm text-text-secondary">
                      Agentic mode (multi-step reasoning with web search)
                    </span>
                  </label>

                  <span className="text-xs text-text-secondary">
                    Press Enter to send, Shift + Enter for new line
                  </span>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
