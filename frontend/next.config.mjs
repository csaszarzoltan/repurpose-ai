/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  eslint: {
    // Type-checking and linting run via `npm run typecheck` / CI; Next's
    // dev-time eslint would block builds on stylistic nits unrelated to this
    // deliverable. Kept explicit so the intent is visible.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
