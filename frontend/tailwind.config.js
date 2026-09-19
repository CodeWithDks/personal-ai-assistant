/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Each token reads from a CSS variable (defined in index.css for
        // both :root and .dark) as an "R G B" triplet, wrapped in rgb()
        // with the <alpha-value> placeholder. This is what lets Tailwind
        // opacity modifiers (bg-signal/90, text-white/60, etc.) keep
        // working *and* lets every one of these tokens retheme instantly
        // when the .dark class toggles on <html> — no dark: prefix
        // needed anywhere a component already uses these names.
        bg: 'rgb(var(--color-bg) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        ink: 'rgb(var(--color-ink) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',
        subtle: 'rgb(var(--color-subtle) / <alpha-value>)',
        'subtle-hover': 'rgb(var(--color-subtle-hover) / <alpha-value>)',
        signal: 'rgb(var(--color-signal) / <alpha-value>)',
        'signal-soft': 'rgb(var(--color-signal-soft) / <alpha-value>)',
        ember: 'rgb(var(--color-ember) / <alpha-value>)',
        'ember-soft': 'rgb(var(--color-ember-soft) / <alpha-value>)',
        danger: 'rgb(var(--color-danger) / <alpha-value>)',
        'danger-soft': 'rgb(var(--color-danger-soft) / <alpha-value>)',
        success: 'rgb(var(--color-success) / <alpha-value>)',
        'success-soft': 'rgb(var(--color-success-soft) / <alpha-value>)',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
