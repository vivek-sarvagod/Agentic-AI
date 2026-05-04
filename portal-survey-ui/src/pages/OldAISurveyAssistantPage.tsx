

// import React, { useState } from 'react';
// import { AgentMessage, sendAgentMessage } from '../services/agentApi';

// const EXAMPLE_PROMPTS = [
//   'Create a survey for Jane Smith. She liked atmosphere and sports and heard from friends.',
//   'Show all surveys where students liked dorm rooms.',
//   "Change John Doe's recommendation to Likely.",
//   'Delete survey 12.',
// ];

// const AISurveyAssistantPage: React.FC = () => {
//   const [messages, setMessages] = useState<AgentMessage[]>([
//     {
//       role: 'assistant',
//       content:
//         'Hi, I can create, search, update, and delete student surveys using natural language.',
//     },
//   ]);
//   const [input, setInput] = useState('');
//   const [sessionId, setSessionId] = useState<string | undefined>();
//   const [loading, setLoading] = useState(false);

//   const submitMessage = async (message: string) => {
//     const trimmed = message.trim();
//     if (!trimmed || loading) return;

//     setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
//     setInput('');
//     setLoading(true);

//     try {
//       const response = await sendAgentMessage(trimmed, sessionId);
//       setSessionId(response.session_id);
//       setMessages((prev) => [
//         ...prev,
//         {
//           role: 'assistant',
//           content: response.response,
//           requiresConfirmation: response.requires_confirmation,
//         },
//       ]);
//     } catch (err) {
//       setMessages((prev) => [
//         ...prev,
//         {
//           role: 'assistant',
//           content: `The agent service returned an error: ${(err as Error).message}`,
//         },
//       ]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
//     event.preventDefault();
//     submitMessage(input);
//   };

//   return (
//     <div className="ai-assistant-shell">
//       <section className="ai-guidance-panel">
//         <div>
//           <span className="assistant-kicker">Agentic AI Extension</span>
//           <h2>AI Survey Assistant</h2>
//           <p>
//             Create requests work best when you include full name, address, phone, email,
//             survey date, what the student liked most, how they became interested, and
//             recommendation likelihood.
//           </p>
//         </div>

//         <div className="assistant-examples">
//           {EXAMPLE_PROMPTS.map((prompt) => (
//             <button key={prompt} type="button" onClick={() => submitMessage(prompt)}>
//               <i className="bi bi-chat-left-text"></i>
//               <span>{prompt}</span>
//             </button>
//           ))}
//         </div>
//       </section>

//       <section className="chat-panel">
//         <div className="chat-header">
//           <div>
//             <h3>Conversation</h3>
//             <span>Confirm write and delete actions before the agent changes data.</span>
//           </div>
//           <i className="bi bi-cpu"></i>
//         </div>

//         <div className="chat-transcript" aria-live="polite">
//           {messages.map((message, index) => (
//             <div key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
//               <div className="chat-avatar">
//                 <i className={`bi ${message.role === 'user' ? 'bi-person' : 'bi-stars'}`}></i>
//               </div>
//               <div className="chat-bubble">
//                 <pre>{message.content}</pre>
//                 {message.requiresConfirmation && (
//                   <div className="confirmation-actions">
//                     <button type="button" onClick={() => submitMessage('yes')}>
//                       <i className="bi bi-check2"></i>
//                       Yes
//                     </button>
//                     <button type="button" onClick={() => submitMessage('no')}>
//                       <i className="bi bi-x-lg"></i>
//                       No
//                     </button>
//                   </div>
//                 )}
//               </div>
//             </div>
//           ))}
//           {loading && (
//             <div className="chat-message assistant">
//               <div className="chat-avatar">
//                 <i className="bi bi-stars"></i>
//               </div>
//               <div className="chat-bubble">
//                 <pre>Thinking through the workflow...</pre>
//               </div>
//             </div>
//           )}
//         </div>

//         <form className="chat-composer" onSubmit={handleSubmit}>
//           <input
//             value={input}
//             onChange={(event) => setInput(event.target.value)}
//             placeholder="Ask the agent to create, find, update, or delete a survey"
//             aria-label="Message the AI survey assistant"
//           />
//           <button type="submit" disabled={loading || !input.trim()}>
//             <i className="bi bi-send"></i>
//           </button>
//         </form>
//       </section>
//     </div>
//   );
// };

// export default AISurveyAssistantPage;
