import React from 'react';
import { AbsoluteFill, Audio, staticFile } from 'remotion';
import { FacelessVideoProps } from './types';
import { MinimalTemplate } from './templates/MinimalTemplate';
import { BoldTemplate } from './templates/BoldTemplate';
import { TechTemplate } from './templates/TechTemplate';

export const FacelessVideo: React.FC<FacelessVideoProps> = (props) => {
    const templateName = props.template || 'minimal';

    return (
        <AbsoluteFill>
            {templateName === 'minimal' && <MinimalTemplate {...props} />}
            {templateName === 'bold' && <BoldTemplate {...props} />}
            {templateName === 'tech' && <TechTemplate {...props} />}

            {props.bgm_file && (
                <Audio src={staticFile(props.bgm_file)} volume={0.1} />
            )}

            {!['minimal', 'bold', 'tech'].includes(templateName) && (
                <div style={{ color: 'white', fontSize: 40, padding: 40 }}>
                    Template {templateName} not found. Falling back.
                </div>
            )}
        </AbsoluteFill>
    );
};
