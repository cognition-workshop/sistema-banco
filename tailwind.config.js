module.exports = {
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'bank-blue': {
          50: '#e6f0ff',
          100: '#b3d9ff',
          200: '#99ccff',
          500: '#0066cc',
          600: '#0052a3',
          700: '#003d7a',
          900: '#001f3d',
        },
        'bank-gray': {
          50: '#f8f9fa',
          100: '#e9ecef',
          200: '#dee2e6',
          500: '#6c757d',
          700: '#495057',
          800: '#343a40',
          900: '#212529',
        }
      }
    },
  },
  plugins: [],
}
