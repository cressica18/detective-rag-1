/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        'bg-void': '#0A0B0D',
        'bg-charcoal': '#14151A',
        'bg-panel': '#1B1C22',
        'bg-corkboard': '#2B2118',
        'bg-paper': '#E8E1D3',
        // Accents
        'accent-amber': '#C89550',
        'accent-amber-dim': '#8A6636',
        'accent-brass': '#9C8552',
        // Signals
        'signal-red': '#8C2F2B',
        'signal-green': '#5C6B4F',
        // Text
        'text-primary': '#E7E2D6',
        'text-on-paper': '#1E1B16',
        'text-muted': '#8C8779',
        'divider': '#2E2F36',
      },
      fontFamily: {
        'report': ['"Special Elite"', 'cursive'],
        'stamp': ['"JetBrains Mono"', 'monospace'],
        'reading': ['Inter', 'sans-serif'],
        'archive': ['"Courier Prime"', 'monospace'],
      },
      backgroundImage: {
        'lamp-glow': 'radial-gradient(ellipse at 50% -10%, rgba(200, 149, 80, 0.12) 0%, transparent 60%)',
      },
      animation: {
        'highlighter': 'highlighter 0.4s ease-out forwards',
        'typewriter': 'typewriter 0.05s steps(1) forwards',
        'pin-drop': 'pinDrop 0.2s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'stamp-in': 'stampIn 0.15s cubic-bezier(0.4, 0, 0.2, 1) forwards',
      },
      keyframes: {
        highlighter: {
          '0%': { backgroundSize: '0% 100%' },
          '100%': { backgroundSize: '100% 100%' },
        },
        pinDrop: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        stampIn: {
          '0%': { transform: 'scale(1.1)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
