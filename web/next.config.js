// Get SPECTRA Web Version
const { version: package_version } = require("./package.json"); // version from package.json
const env_version = process.env.SPECTRA_VERSION; // version from env variable
// Use env version if set & valid, otherwise default to package version
const version = env_version || package_version;

/** @type {import('next').NextConfig} */

// next.config.js
const iconMapping = process.env.NEXT_PUBLIC_ASSISTANTS_ICON_MAPPING
  ? JSON.parse(process.env.NEXT_PUBLIC_ASSISTANTS_ICON_MAPPING)
  : {};

const nextConfig = {
  output: "standalone",
  swcMinify: true,
  env: {
    NEXT_PUBLIC_ASSISTANTS_ICON_MAPPING: JSON.stringify(iconMapping),
  },
  rewrites: async () => {
    // In production, something else (nginx in the one box setup) should take
    // care of this rewrite. TODO (chris): better support setups where
    // web_server and api_server are on different machines.
    if (process.env.NODE_ENV === "production") return [
      {
        source: "/icons/:path*",
        destination: `${process.env.ICONS_SERVER || 'http://127.0.0.1:9123'}/:path*`, // Proxy to Backend
      }
    ];

    return [
      {
        source: "/api/:path*",
        destination: `${process.env.INTERNAL_URL || 'http://127.0.0.1:8080'}/:path*`, // Proxy to Backend
      },
      {
        source: "/icons/:path*",
        destination: `${process.env.ICONS_SERVER || 'http://127.0.0.1:9123'}/:path*`, // Proxy to Backend
      }
    ];
  },
  redirects: async () => {
    // In production, something else (nginx in the one box setup) should take
    // care of this redirect. TODO (chris): better support setups where
    // web_server and api_server are on different machines.
    const defaultRedirects = [];

    if (process.env.NODE_ENV === "production") return defaultRedirects;

    return defaultRedirects.concat([
      {
        source: "/api/chat/send-message:params*",
        destination: `${process.env.INTERNAL_URL || 'http://127.0.0.1:8080'}/chat/send-message:params*`, // Proxy to Backend
        permanent: true,
      },
      {
        source: "/api/query/stream-answer-with-quote:params*",
        destination:
          `${process.env.INTERNAL_URL || 'http://127.0.0.1:8080'}/query/stream-answer-with-quote:params*`, // Proxy to Backend
        permanent: true,
      },
      {
        source: "/api/query/stream-query-validation:params*",
        destination:
          `${process.env.INTERNAL_URL || 'http://127.0.0.1:8080'}/query/stream-query-validation:params*`, // Proxy to Backend
        permanent: true,
      },
    ]);
  },
  publicRuntimeConfig: {
    version,
  },
};

module.exports = nextConfig;
