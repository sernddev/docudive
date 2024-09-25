import debounce from "lodash/debounce";
import { IconType } from "react-icons";

const ICON_SIZE = 15;

export const Hoverable: React.FC<{
  icon: IconType;
  onClick?: () => void;
  size?: number;
}> = ({ icon, onClick, size = ICON_SIZE }) => {

  const debouncedOnClick = onClick ? debounce(onClick, 500) : undefined;

  return (
    <div
      className="hover:bg-hover p-1.5 rounded h-fit cursor-pointer"
      onClick={debouncedOnClick}
    >
      {icon({ size: size, className: "my-auto" })}
    </div>
  );
};
