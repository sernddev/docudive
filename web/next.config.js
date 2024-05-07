// Get Danswer Web Version
const { version: package_version } = require("./package.json"); // version from package.json
const env_version = process.env.DANSWER_VERSION; // version from env variable
// Use env version if set & valid, otherwise default to package version
const version = env_version || package_version;

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  rewrites: async () => {
    // In production, something else (nginx in the one box setup) should take
    // care of this rewrite. TODO (chris): better support setups where
    // web_server and api_server are on different machines.
    if (process.env.NODE_ENV === "production") return [];

    return [{
        source: "/api/:path*",
        destination: `${process.env.MODEl_ONE_URL}/:path*`,
    }];
  },
  redirects: async () => {
    // In production, something else (nginx in the one box setup) should take
    // care of this redirect. TODO (chris): better support setups where
    // web_server and api_server are on different machines.
    const defaultRedirects = [
      {
        source: "/",
        destination: "/search",
        permanent: true,
      },
      {
        source: '/v2/api/:path*',  // Match all paths starting with /v2/api/
        destination: `${process.env.MODEl_TWO_URL}/:path*`,  // Redirect these requests
        permanent: true
      },
      {
        source: '/v1/api/:path*',  // Match all paths starting with /v1/api/
        destination: `${process.env.MODEl_ONE_URL}/:path*`,  // Redirect these requests
        permanent: true
      }
    ];

    if (process.env.NODE_ENV === "production") return defaultRedirects;

    return defaultRedirects.concat([]);
  },
  publicRuntimeConfig: {
    version,
  },
};

module.exports = nextConfig;