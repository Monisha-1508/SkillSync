/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Keeps the browser talking to one origin while the FastAPI service runs
    // on its own port - no CORS dance to debug during the demo.
    const apiBase = process.env.SKILLSYNC_API_BASE || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
