// AISurveyAssistantPage.tsx
// Layout grid is now driven by MainLayout's .ai-resizable-shell via --guidance-w.
// This component renders just the two sections — no fixed widths.

import React, { useEffect, useRef, useState } from 'react';
import { sendAgentMessage } from '../services/agentApi';
import type { ChatMessage } from '../types/agent';
import AgentBubble from './agent/AgentBubble';
import './AISurveyAssistantPage.css';

const EXAMPLE_PROMPTS = [
  'Create a survey for Jane Smith. She liked atmosphere and sports, heard from friends, address 123 Main St, Springfield VA 22150, phone 703-555-0100, email jane@example.com, recommendation Likely, date today.',
  'Show all surveys where students liked dorm rooms.',
  "Change John Doe's recommendation to Likely.",
  'Delete survey 12.',
  'How many students liked the campus atmosphere?',
  'Show me a breakdown of interest sources.',
  'Where is the GMU campus located?',
  'Tell me about the GMU official website.',
  'Summarize what students feel about campus life.',
  'Show campus location and give me a survey overview.',
];

const AISurveyAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hi! I can create, search, update, and delete student surveys, show campus information, run analytics, and summarise student feedback. What would you like to do?',
      agent_tags: [],
      ui_hints: {},
      quick_actions: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const submitMessage = async (message: string) => {
    const trimmed = message.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setInput('');
    setLoading(true);
    try {
      const response = await sendAgentMessage(trimmed, sessionId);
      setSessionId(response.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.response,
          agent_tags: response.agent_tags,
          ui_hints: response.ui_hints,
          quick_actions: response.quick_actions,
          requires_confirmation: response.requires_confirmation,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `The agent service returned an error: ${(err as Error).message}`,
        },
      ]);
    } finally {
      setLoading(false);
      // Restore focus to input after response
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    submitMessage(input);
  };

  return (
    <div className="ai-assistant-shell">
      {/* Guidance panel — width controlled by --guidance-w from MainLayout */}
      <section className="ai-guidance-panel">
        <div>
          <span className="assistant-kicker">Multi-Agent AI</span>
          <h2>AI Survey Assistant</h2>
          <p>
            Ask me to create or manage surveys, get campus information,
            run analytics, or summarise student feedback. You can combine
            multiple requests in one message.
          </p>
        </div>

        <div className="assistant-examples">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => submitMessage(prompt)}
              disabled={loading}
            >
              <i className="bi bi-chat-left-text" />
              <span>{prompt}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Chat panel — fills remaining space */}
      <section className="chat-panel">
        <div className="chat-header">
          <div>
            <h3>Conversation</h3>
            <span>Confirm write and delete actions before the agent changes data.</span>
          </div>
          <i className="bi bi-cpu" />
        </div>

        <div className="chat-transcript" ref={transcriptRef} aria-live="polite">
          {messages.map((message, index) => {
            if (message.role === 'user') {
              return (
                <div key={index} className="chat-message user">
                  <div className="chat-avatar">
                    <i className="bi bi-person" />
                  </div>
                  <div className="chat-bubble">
                    <pre>{message.content}</pre>
                  </div>
                </div>
              );
            }
            return (
              <AgentBubble
                key={index}
                message={message}
                onQuickAction={(p) => submitMessage(p)}
              />
            );
          })}
          {loading && (
            <div className="chat-message assistant">
              <div className="chat-avatar">
                <i className="bi bi-stars" />
              </div>
              <div className="chat-bubble">
                <pre className="thinking-text">Agents working...</pre>
              </div>
            </div>
          )}
        </div>

        <form className="chat-composer" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the agent to create, find, update, delete, or analyse surveys…"
            aria-label="Message the AI survey assistant"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            <i className="bi bi-send" />
          </button>
        </form>
      </section>
    </div>
  );
};

export default AISurveyAssistantPage;