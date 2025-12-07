import React from 'react';
import ThemeCodeBlock from '@theme/CodeBlock';

interface CustomCodeBlockProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  showLineNumbers?: boolean;
}

export default function CustomCodeBlock({
  children,
  className,
  title,
  showLineNumbers = false,
}: CustomCodeBlockProps): React.ReactElement {
  return (
    <div className="custom-code-block">
      <ThemeCodeBlock
        children={children}
        className={className}
        title={title}
        showLineNumbers={showLineNumbers}
      />
    </div>
  );
}