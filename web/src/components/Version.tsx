import getConfig from 'next/config';

function Version() {
  const { publicRuntimeConfig } = getConfig();
  return (
    <div className="text-xs text-gray-400">
        Version {publicRuntimeConfig.version}
    </div>
  );
}

export default Version;
