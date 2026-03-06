/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#000000',
          1: 'rgba(255,255,255,0.03)',
          2: 'rgba(255,255,255,0.05)',
          3: 'rgba(255,255,255,0.08)',
        },
        border: {
          DEFAULT: 'rgba(255,255,255,0.06)',
          hover:   'rgba(255,255,255,0.12)',
        },
        label: {
          primary:   'rgba(255,255,255,0.92)',
          secondary: 'rgba(255,255,255,0.55)',
          tertiary:  'rgba(255,255,255,0.32)',
        },
        accent: {
          green:  '#30d158',
          red:    '#ff453a',
          amber:  '#ffd60a',
          blue:   '#0a84ff',
          purple: '#bf5af2',
          teal:   '#64d2ff',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', '"SF Pro Text"', '"Helvetica Neue"', 'system-ui', 'sans-serif'],
        mono: ['"SF Mono"', '"Fira Code"', '"Cascadia Code"', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '20px',
        '4xl': '24px',
      },
      animation: {
        'fade-up':   'fadeUp 0.35s cubic-bezier(0.23,1,0.32,1) both',
        'fade-in':   'fadeIn 0.3s ease both',
        'breathe':   'breathe 2.4s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)',   opacity: '0.4' },
          '50%':      { transform: 'scale(1.8)', opacity: '0'   },
        },
      },
    },
  },
  plugins: [],
}
