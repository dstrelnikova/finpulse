// src/components/Message.tsx
import React from "react";

type Props = {
  id: number;
  author: string;
  text: string;
  time: string;
  isBot: boolean;
};

export default function Message({ author, text, time, isBot }: Props) {
  const wrapperAlign = isBot ? "justify-start" : "justify-end";
  const bubbleBg = isBot
    ? "border border-slate-200 bg-white text-slate-900 shadow-sm"
    : "bg-slate-950 text-white shadow-sm";
  const metaColor = isBot ? "text-slate-500" : "text-slate-300";
  const displayText = isBot ? text.replace(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]/g, "") : text;

  return (
    <div className={`flex ${wrapperAlign}`}>
      <div className={`max-w-[86%] rounded-lg px-4 py-3 sm:max-w-2xl ${bubbleBg}`}>
        <div className={`mb-1.5 text-xs font-medium ${metaColor}`}>
          {author} • {time}
        </div>
        <div className="whitespace-pre-wrap text-base leading-relaxed">{displayText}</div>
      </div>
    </div>
  );
}
