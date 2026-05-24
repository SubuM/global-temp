/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                dark: '#0d0d11',
                card: 'rgba(26, 26, 36, 0.65)',
                primary: '#ff4b4b',
            },
            fontFamily: {
                sans: ['Plus Jakarta Sans', 'sans-serif'],
                display: ['Outfit', 'sans-serif'],
            }
        },
    },
    plugins: [],
}