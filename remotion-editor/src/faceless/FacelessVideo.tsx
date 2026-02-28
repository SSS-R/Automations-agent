import React from 'react';
import { AbsoluteFill } from 'remotion';
import { FacelessVideoProps } from './types';
import { MinimalTemplate } from './templates/MinimalTemplate';

export const FacelessVideo: React.FC<FacelessVideoProps> = (props) => {
    // Determine which template to render based on props
    const templateName = props.template || 'minimal';

    return (
        <AbsoluteFill>
            {templateName === 'minimal' && <MinimalTemplate {...props} />}
            {/* other templates will go here */}
            {templateName !== 'minimal' && (
                <div style={{ color: 'white', fontSize: 40, padding: 40 }}>
                    Template {templateName} not found. Falling back to Minimal.
                </div>
            )}
        </AbsoluteFill>
    );
};
