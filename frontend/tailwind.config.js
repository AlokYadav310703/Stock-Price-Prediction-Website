/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0A0E14',
          900: '#0F1420',
          800: '#161D2B',
          700: '#1D2536',
          600: '#232B3D',
        },
        paper: {
          DEFAULT: '#E8ECF2',
          dim: '#8993A8',
        },
        signal: {
          up: '#2FBF8F',
          down: '#E5484D',
          warn: '#E8A33D',
          info: '#4C7EFF',
        },
        accent: {
          DEFAULT: '#4C7EFF',
          dim: '#2A3A5C',
        },
      },
      fontFamily: {
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.6)',
      },
      keyframes: {
        ticker: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
      animation: {
        ticker: 'ticker 32s linear infinite',
      },
    },
  },
  plugins: [],
}
