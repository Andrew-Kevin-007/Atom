import React, { useState } from 'react';
import { Copy, ClipboardCheck, FileText } from 'lucide-react';

const SECTIONS = [
  { key: 'summary',    label: 'Summary',      color: '#30d158' },
  { key: 'rootCause',  label: 'Root Cause',   color: '#ffd60a' },
  { key: 'impact',     label: 'Impact',       color: '#ff453a' },
  { key: 'resolution', label: 'Resolution',   color: '#0a84ff' },
];

/**
 * Postmortem — auto-generated incident report
 */
export default function Postmortem({ incident = null }) {
  const [copied, setCopied] = useState(false);

  const pm          = incident?.postmortem || {};
  const actionItems = pm.actionItems || [];
  const resolved    = incident?.status === 'resolved';
  const hasContent  = SECTIONS.some(s => pm[s.key]);

  const toMarkdown = () => {
    let md = `# ATOM Incident Postmortem\n\n**Generated:** ${new Date().toISOString()}\n\n`;
    SECTIONS.forEach(({ key, label }) => { if (pm[key]) md += `## ${label}\n${pm[key]}\n\n`; });
    if (actionItems.length) {
      md += '## Action Items\n';
      actionItems.forEach(i => { md += `- [ ] ${i}\n`; });
    }
    return md;
  };

  const copy = () => {
    navigator.clipboard.writeText(toMarkdown());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="glass h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <FileText size={14} className="text-label-tertiary" />
        <h2 className="text-[13px] font-semibold text-label-primary tracking-tight">Postmortem</h2>
        {resolved && (
          <button
            onClick={copy}
            className="ml-auto flex items-center gap-1.5 h-6 px-2.5 rounded-full
                       text-[11px] font-medium bg-surface-2 text-label-secondary
                       hover:bg-surface-3 active:scale-[0.97]"
          >
            {copied ? <ClipboardCheck size={12} className="text-accent-green" /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy MD'}
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!hasContent ? (
          <div className="h-full flex flex-col items-center justify-center gap-3 text-label-tertiary">
            <div className="w-6 h-6 rounded-full border-2 border-label-tertiary/30 border-t-label-tertiary animate-spin" />
            <p className="text-[13px]">Building postmortem…</p>
          </div>
        ) : (
          <div className="space-y-5">
            {SECTIONS.map(({ key, label, color }) =>
              pm[key] ? (
                <section key={key} className="animate-fade-up">
                  <h3
                    className="text-[11px] font-semibold uppercase tracking-widest mb-1.5"
                    style={{ color }}
                  >
                    {label}
                  </h3>
                  <p className="text-[13px] leading-relaxed text-label-secondary">{pm[key]}</p>
                </section>
              ) : null
            )}

            {actionItems.length > 0 && (
              <section className="animate-fade-up">
                <h3 className="text-[11px] font-semibold uppercase tracking-widest mb-1.5 text-accent-purple">
                  Action Items
                </h3>
                <ul className="space-y-1.5">
                  {actionItems.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-[13px] text-label-secondary">
                      <span className="text-accent-purple flex-none mt-0.5">▸</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {!hasContent && (
              <p className="text-center text-[13px] text-label-tertiary py-6">
                Postmortem populates as the incident progresses…
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
