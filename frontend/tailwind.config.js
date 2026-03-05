/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        card: '#12121a',
        'dark-bg': '#0a0a0f',
        'text-primary': '#e0e0e0',
        'text-muted': '#888888',
        'green-accent': '#00ff88',
        'red-accent': '#ff3333',
        'amber-accent': '#ffaa00',
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out forwards',
        'pulse-fast': 'pulse 0.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        slideIn: {
          '0%': {
            opacity: '0',
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
      },
    },
  },
  plugins: [],
}
