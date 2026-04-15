import React from "react";

import { MessageCircle } from "lucide-react";

import type { Message } from "@/types/homeops";

interface ChatPageProps {
  messages: Message[];
  isTyping: boolean;
  apiError: string;
  chatInput: string;
  onChangeChatInput: (value: string) => void;
  onChatKeyDown: (e: React.KeyboardEvent) => void;
  onSendMessage: () => void;
  chatBottomRef: React.RefObject<HTMLDivElement | null>;
}

function renderMessageText(text: string) {
  const lines = text.split("\n");

  return lines.map((line, lineIndex) => {
    const parts = line.split(/(https?:\/\/[^\s]+)/gi);

    return (
      <p key={`${lineIndex}-${line.slice(0, 24)}`} className={lineIndex > 0 ? "mt-2" : ""}>
        {parts.map((part, partIndex) => {
          const isUrl = /^https?:\/\/[^\s]+$/i.test(part);
          if (!isUrl) return <React.Fragment key={partIndex}>{part}</React.Fragment>;

          return (
            <a
              key={partIndex}
              href={part}
              target="_blank"
              rel="noreferrer"
              className="underline text-teal-300 break-all hover:text-teal-200"
            >
              {part}
            </a>
          );
        })}
      </p>
    );
  });
}

export function ChatPage({
  messages,
  isTyping,
  apiError,
  chatInput,
  onChangeChatInput,
  onChatKeyDown,
  onSendMessage,
  chatBottomRef,
}: ChatPageProps) {
  return (
    <div className="max-w-3xl mx-auto h-full flex flex-col">
      <div className="mb-4 flex items-center gap-4 bg-zinc-900 rounded-3xl px-5 py-4">
        <div className="bg-linear-to-br from-teal-400 to-cyan-400 w-9 h-9 rounded-2xl flex items-center justify-center shrink-0">
          <MessageCircle className="w-5 h-5 text-black" />
        </div>
        <div>
          <div className="font-semibold">HOME_SENSE Assistant</div>
          <div className="text-xs text-emerald-400 flex items-center gap-1">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
            Always on • Connected to all your manuals
          </div>
        </div>
      </div>

      <div className="flex-1 bg-zinc-900 rounded-3xl p-6 overflow-auto space-y-8 mb-4" id="chat-window">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.isUser ? "justify-end" : "justify-start"}`}>
            {!msg.isUser && (
              <div className="w-8 h-8 bg-linear-to-br from-teal-400 to-cyan-300 rounded-2xl shrink-0 mr-3 mt-1"></div>
            )}
            <div className={`max-w-[70%] rounded-3xl px-6 py-4 text-sm ${msg.isUser ? "bg-white text-zinc-900 rounded-tr-none" : "bg-zinc-800 text-zinc-100 rounded-tl-none"}`}>
              {renderMessageText(msg.text)}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center gap-3 pl-11">
            <div className="w-8 h-8 bg-linear-to-br from-teal-400 to-cyan-300 rounded-2xl shrink-0"></div>
            <div className="bg-zinc-800 text-zinc-400 text-sm px-5 py-3 rounded-3xl flex items-center gap-2">
              <span className="animate-pulse">thinking</span>
              <span className="w-1 h-1 bg-current rounded-full animate-ping"></span>
            </div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {apiError && (
        <div className="mb-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {apiError}
        </div>
      )}

      <div className="bg-zinc-900 rounded-3xl p-2 flex items-center">
        <input
          type="text"
          value={chatInput}
          onChange={(e) => onChangeChatInput(e.target.value)}
          onKeyDown={onChatKeyDown}
          placeholder="Ask about any appliance... e.g. Why is my dryer making noise?"
          className="flex-1 bg-transparent px-6 py-5 outline-none placeholder:text-zinc-500 text-sm"
        />
        <button
          onClick={onSendMessage}
          title="Send message"
          className="bg-white text-black h-12 w-12 flex items-center justify-center rounded-2xl hover:bg-amber-200 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.874L5.999 12zm0 0h7.07" />
          </svg>
        </button>
      </div>

      <div className="text-center text-[10px] text-zinc-500 mt-6">Try asking about error codes, maintenance, or sensor readings</div>
    </div>
  );
}
