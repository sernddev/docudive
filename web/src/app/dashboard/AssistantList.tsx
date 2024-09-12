"use client";

import { getAssistantIcon } from "@/lib/constants";
import { Persona } from "../admin/assistants/interfaces";
import { useRouter } from 'next/navigation';

const AssistantList = ({assistants, icons}: {assistants: Persona[], icons: {[key: string]: string}}) => {
    const router = useRouter();
    const handleClick = (id:number) => {
        router.push(`/chat?assistantId=${id}`);
    };

    const getAssitantList = () => {
        return assistants.filter((assistant: Persona)=> assistant.is_visible).map((assistant: Persona)=> {
            const imageUrl = icons && icons[assistant.id] ? icons[assistant.id] : getAssistantIcon(assistant.id);

            return (
                <div 
                    key={assistant.id} 
                    className="bg-white p-4 rounded-lg shadow-md flex items-start cursor-pointer transition-all transform hover:scale-103 hover:bg-gray-100"
                    onClick={()=> handleClick(assistant.id)}>
                        <img className="w-12 mr-4" src={imageUrl} alt={assistant.name} />
                        <div>
                            <h2 className="text-md font-bold text-gray-800">{assistant.name}</h2>
                            <p className="text-gray-600 text-sm">{assistant.description}</p>
                        </div>
                </div>
            );
        });
    }

    return (
        <div className="grid grid-cols-3 gap-5 w-full max-w-5xl">
            {getAssitantList()}
        </div>
    );
}

export default AssistantList;