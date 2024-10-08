import { Bubble } from "@/components/Bubble";
import { ToolSnapshot } from "@/lib/tools/interfaces";
import { FiImage, FiSearch, FiGlobe } from "react-icons/fi";

export function ToolsDisplay({ tools }: { tools: ToolSnapshot[] }) {
  return (
    <div className="text-xs text-subtle flex flex-wrap gap-1 mt-2">
      {tools.map((tool) => {
        let toolName = tool.name;
        let toolIcon = null;

        if (tool.name === "SearchTool") {
          toolName = "Search";
          toolIcon = <FiSearch className="mr-1 my-auto" />;
        } else if (tool.name === "ImageGenerationTool") {
          toolName = "Image Generation";
          toolIcon = <FiImage className="mr-1 my-auto" />;
        } else if (tool.name === "SQLGenerationTool") {
          toolName = "SQL Generation";
          toolIcon = <FiImage className="mr-1 my-auto" />;
        } else if (tool.name === "SummaryGenerationTool") {
          toolName = "Summary Generation";
          toolIcon = <FiImage className="mr-1 my-auto" />;
        } else if (tool.name === "InternetSearchTool") {
          toolName = "Internet Search";
          toolIcon = <FiGlobe className="mr-1 my-auto" />;
        } else if (tool.name === "ComposeEmailTool") {
          toolName = "Compose Email";
          toolIcon = <FiGlobe className="mr-1 my-auto" />;
        } else if (tool.name === "FileDataInfographicsTool") {
          toolName = "File Data Infographics";
        }else if (tool.name === "ExcelAnalyzerTool") {
          toolName = "Excel Analyzer";
          toolIcon = <FiGlobe className="mr-1 my-auto" />;
        }


        return (
          <Bubble key={tool.id} isSelected={false} notSelectable>
            <div className="flex flex-row gap-0.5">
              {toolIcon}
              {toolName}
            </div>
          </Bubble>
        );
      })}
    </div>
  );
}
