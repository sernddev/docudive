import { useState } from "react";
import { FiCheck, FiCopy } from "react-icons/fi";
import { Hoverable } from "./Hoverable";
import { fallbackCopyTextToClipboard } from "@/lib/utils";

export function CopyButton({
  content,
  onClick,
}: {
  content?: string;
  onClick?: () => void;
}) {
  const [copyClicked, setCopyClicked] = useState(false);

  return (
    <Hoverable
      icon={copyClicked ? FiCheck : FiCopy}
      onClick={() => {
        if (content) {
          if(navigator.clipboard) {
            navigator.clipboard.writeText(content.toString());
          } else {
            fallbackCopyTextToClipboard(content.toString());
          }
        }
        onClick && onClick();

        setCopyClicked(true);
        setTimeout(() => setCopyClicked(false), 3000);
      }}
    />
  );
}
