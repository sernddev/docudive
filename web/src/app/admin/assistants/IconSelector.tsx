'use client';
import React, { useEffect, useState } from 'react';

// API fetcher utility (adjust based on your API setup)
const fetchIcons = async () => {
  const res = await fetch('/api/settings/icons'); // Adjust API URL as needed
  return res.json();
};

const IconSelector = ({ onSelect, defaultIcon }: { onSelect: Function, defaultIcon?: string }) => {
  const [icons, setIcons] = useState([]);
  const [selectedIcon, setSelectedIcon] = useState(defaultIcon);

  // Fetch icons from the API when component mounts
  useEffect(() => {
    const loadIcons = async () => {
      const iconData = await fetchIcons();
      setIcons(iconData?.icons_urls || []);
    };
    loadIcons();
  }, []);

  useEffect(()=> {
    setSelectedIcon(defaultIcon);
  }, [defaultIcon])

  const handleIconSelect = (iconUrl: any) => {
    setSelectedIcon(iconUrl);
    onSelect(iconUrl);
  };

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold mb-4">Select an Icon for the Assistant</h3>
      <div className="grid grid-cols-12 gap-4 mb-6">
        {icons.map((iconUrl) => (
          <img
            key={iconUrl}
            src={iconUrl}
            alt="Icon"
            className={`w-16 h-16 cursor-pointer border-2 p-1 rounded-md transition-transform duration-200 ${
              selectedIcon === iconUrl
                ? 'border-blue-500 scale-105'
                : 'border-gray-300 hover:border-blue-400 hover:scale-105'
            }`}
            onClick={() => handleIconSelect(iconUrl)}
          />
        ))}
      </div>
    </div>
  );
};

export default IconSelector;
