import { Persona } from "@/app/admin/assistants/interfaces";
import { FiCheck, FiChevronDown, FiPlusSquare, FiEdit2 } from "react-icons/fi";
import { CustomDropdown, DefaultDropdownElement } from "@/components/Dropdown";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { checkUserIdOwnsAssistant } from "@/lib/assistants/checkOwnership";
import { getAssistantIcon } from "@/lib/constants";
import { useEffect, useState } from "react";
import { getAssitantServerIcon } from "@/lib/assistants/updateAssistantPreferences";

function PersonaItem({
  id,
  name,
  onSelect,
  isSelected,
  isOwner,
}: {
  id: number;
  name: string;
  onSelect: (personaId: number) => void;
  isSelected: boolean;
  isOwner: boolean;
}) {

  const [assistantIcon, setAssistantIcon] = useState<string>("");
  useEffect(()=> {
    const fetchIcon = async ()=> {
      const iconURL = await getAssitantServerIcon(id);

      if(iconURL) {
        setAssistantIcon(iconURL);
      }
    }

    fetchIcon();
  }, []);

  return (
    <div className="flex w-full">
      <div
        key={id}
        className={`
          flex
          flex-grow
          px-3 
          text-sm 
          py-2 
          my-0.5
          rounded
          mx-1
          select-none 
          cursor-pointer 
          text-emphasis
          bg-background
          hover:bg-hover-light
          ${isSelected ? "bg-hover text-selected-emphasis" : ""}
        `}
        onClick={() => {
          onSelect(id);
        }}
      >
        <div className="flex">
          <img className="mr-2" width={20} src={assistantIcon || getAssistantIcon(id)} alt="" />
          <div className="text">{name}</div>
          {isSelected && (
            <div className="ml-auto mr-1 my-auto">
              <FiCheck />
            </div>
          )}
        </div>
      </div>
      {isOwner && (
        <Link href={`/assistants/edit/${id}`} className="mx-2 my-auto">
          <FiEdit2 className="hover:bg-hover p-0.5 my-auto" size={20} />
        </Link>
      )}
    </div>
  );
}

export function ChatPersonaSelector({
  personas,
  selectedPersonaId,
  onPersonaChange,
  userId,
}: {
  personas: Persona[];
  selectedPersonaId: number | null;
  onPersonaChange: (persona: Persona | null) => void;
  userId: string | undefined;
}) {
  const router = useRouter();

  const currentlySelectedPersona = personas.find(
    (persona) => persona.id === selectedPersonaId
  );

  const [assistantIcon, setAssistantIcon] = useState<string>("");
  useEffect(()=> {
    const fetchIcon = async ()=> {
      if(selectedPersonaId) {
        const iconURL = await getAssitantServerIcon(selectedPersonaId);

        if(iconURL) {
          setAssistantIcon(iconURL);
        }
      }
    }

    fetchIcon();
  }, []);

  return (
    <CustomDropdown
      dropdown={
        <div
          className={`
            border 
            border-border 
            bg-background
            rounded-lg 
            shadow-lg 
            flex 
            flex-col 
            w-64 
            max-h-96 
            overflow-y-auto 
            p-1
            overscroll-contain`}
        >
          {personas.map((persona) => {
            const isSelected = persona.id === selectedPersonaId;
            const isOwner = checkUserIdOwnsAssistant(userId, persona);
            return (
              <PersonaItem
                key={persona.id}
                id={persona.id}
                name={persona.name}
                onSelect={(clickedPersonaId) => {
                  const clickedPersona = personas.find(
                    (persona) => persona.id === clickedPersonaId
                  );
                  if (clickedPersona) {
                    onPersonaChange(clickedPersona);
                  }
                }}
                isSelected={isSelected}
                isOwner={isOwner}
              />
            );
          })}

          <div className="border-t border-border pt-2">
            <DefaultDropdownElement
              name={
                <div className="flex items-center">
                  <FiPlusSquare className="mr-2" />
                  New Assistant
                </div>
              }
              onSelect={() => router.push("/assistants/new")}
              isSelected={false}
            />
          </div>
        </div>
      }
    >
      <div className="select-none text-lg text-strong items-center font-bold flex px-2 rounded cursor-pointer hover:bg-hover-light">
        <div className="mt-auto">
          <div className="flex">
            <img className="mr-2" src={assistantIcon || getAssistantIcon(currentlySelectedPersona?.id||0)} width={25} alt="" />
            <div className="text items-center">
              {currentlySelectedPersona?.name || "Default"}
            </div>
          </div>
        </div>
        <FiChevronDown className="my-auto ml-1" />
      </div>
    </CustomDropdown>
  );
}
