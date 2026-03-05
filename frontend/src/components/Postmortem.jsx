import React, { useState } from 'react';
import { Copy, Download } from 'lucide-react';

/**
 * Postmortem Component
 * Live postmortem document that builds during the incident
 * Shows sections: Summary, Timeline, Root Cause, Impact, Resolution, Action Items
 */
export function Postmortem({ incident = null }) {
  const [copied, setCopied] = useState(false);

  // Extract data from incident
  const summary = incident?.postmortem?.summary || '';
  const rootCause = incident?.postmortem?.rootCause || '';
  const impact = incident?.postmortem?.impact || '';
  const resolution = incident?.postmortem?.resolution || '';
  const actionItems = incident?.postmortem?.actionItems || [];
  const isResolved = incident?.status === 'resolved';

  // Generate markdown postmortem
  const generateMarkdown = () => {
    let md = '# ATOM Incident Postmortem\n\n';
    md += `**Generated:** ${new Date().toISOString()}\n\n`;

    if (summary) {
      md += `## Incident Summary\n${summary}\n\n`;
    }
    if (rootCause) {
      md += `## Root Cause\n${rootCause}\n\n`;
    }
    if (impact) {
      md += `## Impact\n${impact}\n\n`;
    }
    if (resolution) {
      md += `## Resolution\n${resolution}\n\n`;
    }
    if (actionItems.length > 0) {
      md += `## Action Items\n`;
      actionItems.forEach(item => {
        md += `- [ ] ${item}\n`;
      });
    }

    return md;
  };

  const handleCopyMarkdown = () => {
    const markdown = generateMarkdown();
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full bg-card rounded-lg border border-gray-700 overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-bold">Postmortem</h2>
        {isResolved && (
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center gap-2 px-3 py-1 bg-green-900 bg-opacity-30 hover:bg-opacity-50 rounded text-green-400 text-sm transition-colors"
          >
            <Copy size={14} />
            {copied ? 'Copied!' : 'Copy'}
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {!isResolved && !summary ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="animate-pulse text-lg mb-2">⚙️</div>
              <p className="text-sm">GENERATING...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {summary && (
              <section>
                <h3 className="text-sm font-bold text-green-400 mb-2">INCIDENT SUMMARY</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{summary}</p>
              </section>
            )}

            {rootCause && (
              <section>
                <h3 className="text-sm font-bold text-amber-400 mb-2">ROOT CAUSE</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{rootCause}</p>
              </section>
            )}

            {impact && (
              <section>
                <h3 className="text-sm font-bold text-red-400 mb-2">IMPACT</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{impact}</p>
              </section>
            )}

            {resolution && (
              <section>
                <h3 className="text-sm font-bold text-blue-400 mb-2">RESOLUTION</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{resolution}</p>
              </section>
            )}

            {actionItems.length > 0 && (
              <section>
                <h3 className="text-sm font-bold text-purple-400 mb-2">ACTION ITEMS</h3>
                <ul className="space-y-2">
                  {actionItems.map((item, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-purple-400 flex-shrink-0">▸</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {!summary && (
              <div className="text-center text-gray-500 py-8">
                <p className="text-sm">Postmortem will populate as incident resolves...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Postmortem;
