// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // keep your existing export setting
  images: { unoptimized: true },
  async rewrites() {
    return [
      {
        source: '/api/chat',
        destination: 'https://byq6zggjf4.execute-api.us-east-1.amazonaws.com/chat',
      },
    ];
  },
};

export default nextConfig;