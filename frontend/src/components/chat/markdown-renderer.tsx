"use client";

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from '@/lib/utils';
import { Citation } from '@/types/chat';
import { CitationMarker } from './citation-marker';
import React from 'react';
import { remarkCitations } from '@/lib/remark-citations';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  citations?: Citation[];
}

export function MarkdownRenderer({ content, className, citations }: MarkdownRendererProps) {
  return (
    <div
      className={cn(
        'prose prose-zinc dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0 prose-pre:bg-transparent',
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkCitations]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // @ts-expect-error - node type is from rehype
          cite({ node, children }) {
            const id = (node?.properties?.['data-id'] as string) || String(children);
            return <CitationMarker id={id} citations={citations || []} />;
          },
          // @ts-expect-error - props are passed from react-markdown
          code({ inline, className: codeClassName, children, ...props }) {
            const match = /language-(\w+)/.exec(codeClassName || '');
            return !inline && match ? (
              <div className="relative my-4 rounded-lg overflow-hidden border border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center justify-between px-4 py-2 bg-zinc-100 dark:bg-zinc-800 text-xs font-mono text-zinc-500">
                  <span>{match[1]}</span>
                </div>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    margin: 0,
                    padding: '1rem',
                    fontSize: '0.875rem',
                    lineHeight: '1.5',
                    backgroundColor: 'transparent',
                  }}
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              </div>
            ) : (
              <code className={cn("bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-sm font-mono", codeClassName)} {...props}>
                {children}
              </code>
            );
          },
          // Override link to open in new tab
          a: ({ ...props }) => (
            <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
