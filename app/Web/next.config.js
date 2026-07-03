/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Produce a self-contained server bundle for a lean container image.
  // See context/spec/features/new/aws-deployment.md.
  output: "standalone",
};

module.exports = nextConfig;
