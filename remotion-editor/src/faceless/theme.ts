export type FontPreset = 'inter' | 'roboto' | 'outfit' | 'montserrat';
export type ColorPalette = 'default' | 'neon' | 'monochrome' | 'sunset' | 'cyberpunk';

export const FONTS: Record<FontPreset, string> = {
    inter: "'Inter', sans-serif",
    roboto: "'Roboto', sans-serif",
    outfit: "'Outfit', sans-serif",
    montserrat: "'Montserrat', sans-serif",
};

export const PALETTES: Record<ColorPalette, { primary: string; text: string; bg: string }> = {
    default: { primary: '#FFD700', text: '#FFFFFF', bg: '#111111' },
    neon: { primary: '#00FF41', text: '#FFFFFF', bg: '#0D0208' },
    monochrome: { primary: '#EEEEEE', text: '#FFFFFF', bg: '#000000' },
    sunset: { primary: '#FF7E67', text: '#FEF9F8', bg: '#292B45' },
    cyberpunk: { primary: '#FEE715', text: '#FFFFFF', bg: '#101820' }
};
