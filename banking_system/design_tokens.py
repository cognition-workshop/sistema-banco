"""
Design System Tokens for Banking System
Defines colors, typography, spacing, and other design constants
"""

COLORS = {
    'primary': {
        'blue': '#1E3A8A',
        'blue_light': '#3B82F6',
        'blue_dark': '#1E40AF',
    },
    'success': {
        'green': '#059669',
        'green_light': '#10B981',
        'green_dark': '#047857',
    },
    'neutral': {
        'gray': '#64748B',
        'gray_light': '#94A3B8',
        'gray_dark': '#475569',
    },
    'error': {
        'red': '#DC2626',
        'red_light': '#EF4444',
        'red_dark': '#B91C1C',
    },
    'warning': {
        'yellow': '#F59E0B',
        'yellow_light': '#FBBF24',
        'yellow_dark': '#D97706',
    },
    'background': {
        'light': '#FFFFFF',
        'gray': '#F8FAFC',
        'dark': '#0F172A',
    },
}

TYPOGRAPHY = {
    'font_families': {
        'heading': 'Poppins, sans-serif',
        'body': 'Inter, system-ui, -apple-system, sans-serif',
        'mono': 'Monaco, Courier, monospace',
    },
    'font_sizes': {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2.25rem',
        '5xl': '3rem',
    },
    'font_weights': {
        'light': '300',
        'normal': '400',
        'medium': '500',
        'semibold': '600',
        'bold': '700',
    },
}

SPACING = {
    'xs': '0.25rem',
    'sm': '0.5rem',
    'md': '1rem',
    'lg': '1.5rem',
    'xl': '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
}

BORDER_RADIUS = {
    'sm': '0.25rem',
    'md': '0.5rem',
    'lg': '0.75rem',
    'xl': '1rem',
    'full': '9999px',
}

SHADOWS = {
    'sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    'md': '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    'lg': '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    'xl': '0 20px 25px -5px rgb(0 0 0 / 0.1)',
}

BREAKPOINTS = {
    'sm': '640px',
    'md': '768px',
    'lg': '1024px',
    'xl': '1280px',
    '2xl': '1536px',
}
