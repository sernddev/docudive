"use client";
import { useEffect, useState, useRef, ChangeEvent, Key } from "react";
import { useSearchParams } from "next/navigation";
import { ChatSession } from "./interfaces";
import { ChatSidebar } from "./sessionSidebar/ChatSidebar";
import { FiRefreshCcw, FiSend, FiStopCircle } from "react-icons/fi";

import { Chat } from "./Chat";
import { DocumentSet, Tag, User, ValidSources } from "@/lib/types";
import { Persona } from "../admin/personas/interfaces";
import { Header } from "@/components/Header";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { InstantSSRAutoRefresh } from "@/components/SSRAutoRefresh";
import { MODELS } from "@/lib/constants";
import { ChatPersonaSelector } from "./ChatPersonaSelector";
import router from "next/router";
import { createChatSession } from "./lib";

const MAX_INPUT_HEIGHT = 200;
type UpdateData = {
  key: string;
  value: any;
};

type Model = {
  id: number, 
  name: string, 
  sessionId: number | null
}

export function ChatLayout({
  user,
  chatSessions,
  availableSources,
  availableDocumentSets,
  availablePersonas,
  availableTags,
  defaultSelectedPersonaId,
  documentSidebarInitialWidth,
}: {
  user: User | null;
  chatSessions: ChatSession[];
  availableSources: ValidSources[];
  availableDocumentSets: DocumentSet[];
  availablePersonas: Persona[];
  availableTags: Tag[];
  defaultSelectedPersonaId?: number; // what persona to default to
  documentSidebarInitialWidth?: number;
}) {
  const searchParams = useSearchParams();
  const chatIdRaw = searchParams.get("chatId");
  const chatId = chatIdRaw ? parseInt(chatIdRaw) : null;

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const selectedChatSession = chatSessions.find(
    (chatSession) => chatSession.id === chatId
  );

  const [message, setMessage] = useState("");
  const [postMessage, setPostMessage] = useState(!chatId?"Welcome":"");
  const [streamingQ, setStreamingQ] = useState<boolean[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<Persona | undefined>(
    selectedChatSession?.persona_id !== undefined
      ? availablePersonas.find(
          (persona) => persona.id === selectedChatSession?.persona_id
        )
      : defaultSelectedPersonaId !== undefined
        ? availablePersonas.find(
            (persona) => persona.id === defaultSelectedPersonaId
          )
        : undefined
  );
  const livePersona = selectedPersona || availablePersonas[0];
  // list of models
  // const models = [ {id: MODELS.ModelOne, name: "Model 1", sessionId: chatId}, {id: MODELS.ModelTwo, name: "Model 2", sessionId: null}];

  const [selectedModels, setSelectedModels] = useState<number[]>([MODELS.ModelOne]);
  const [models, setModels] = useState<Model[]>([{id: MODELS.ModelOne, name: "Model 1", sessionId: chatId}, {id: MODELS.ModelTwo, name: "Model 2", sessionId: null}]);
  const [windowWidth, setwindowWidth] = useState('w100');
  useEffect(()=>{
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "0px";
      textarea.style.height = `${Math.min(
        textarea.scrollHeight,
        MAX_INPUT_HEIGHT
      )}px`;
    }
  }, [message]);

  const handleEventCycle = ({key, value}: UpdateData) => {
    if(key === 'isStreaming') {
      setStreamingQ(oldState=> value? [...oldState, true]: oldState.slice(0, -1));
    }
    if(key === 'sessionId') {
      setModels(models.map((model: Model)=> {
        if(model.id === value.modelNumber) {
          model.sessionId = value.sesssionId;
        }
        return model;
      }));
    }
  }

  const handleCheckboxChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const selectedId: number = parseInt(event.target.value);

    if(event.target.checked){
      setSelectedModels([...selectedModels, selectedId])
     }else{
      setSelectedModels(selectedModels.filter(id=>id !== selectedId))
     }
     if(selectedModels.length === 1){
       setwindowWidth('w50')
     } else{
       setwindowWidth('w100')
     }
   
  }

  return (
    <>
      <div className="fixed top-0 z-20 w-full pt-[84]">
        <Header user={user} />
        <div className="ml-2 p-2 rounded mt-2 bg-slate-100/90 fixed top-0 left-1/2 -translate-x-1/2">
          <div className={'set-modal-check'}>
            {
              models.map((model, index)=> (
              <div key={model.id} className={'model-check-box'}>
                <input
                type="checkbox"
                className={'mt-1'}
                value={model.id}
                checked={selectedModels.includes(model.id)}
                disabled={index=== 0}
                onChange={(event) => { handleCheckboxChange(event) }}
                />
                <div
                  key={model.name}
                  className="w-full ml-2"
                >
                {model.name}
                </div>
              </div>
              ))
            }
          </div>
          </div>
      </div>
      <HealthCheckBanner />
      <InstantSSRAutoRefresh />
      <div className="chat-select-box">
        <div className="ml-2 p-1 rounded mt-2 w-fit">
          <ChatPersonaSelector
            personas={availablePersonas}
            selectedPersonaId={livePersona.id}
            onPersonaChange={(persona) => {
              if (persona) {
                setSelectedPersona(persona);
                textareaRef.current?.focus();
                router.push(`/chat?personaId=${persona.id}`);
              }
            }}
          />
        </div>
      </div>

      <div className="flex relative bg-background text-default  chat-container-height">
        {/* <ChatSidebar
          existingChats={chatSessions}
          currentChatSession={selectedChatSession}
          user={user}
        /> */}

        <div className="flex flex-wrap w100">
        {selectedModels.map((model)=> (
          <div key={model as Key} className={windowWidth +' min-w-0'} style={{height: "calc(100vh - 70px)"}}>
            {/* <p className="bg-slate-100/80 inline-block chat-modal-item">Model {model}</p> */}
            <Chat
              existingChatSessionId={models.find(m=> m.id === model)?.sessionId || null}
              existingChatSessionPersonaId={selectedPersona?.id}
              availableSources={availableSources}
              availableDocumentSets={availableDocumentSets}
              availablePersonas={availablePersonas}
              availableTags={availableTags}
              message={postMessage}
              modelNumber={model}
              eventCycle={handleEventCycle}
              defaultSelectedPersonaId={defaultSelectedPersonaId}
              documentSidebarInitialWidth={documentSidebarInitialWidth}
              updatedPersona={selectedPersona}
            />
          </div>
        ))}
        </div>

        <div className="fixed bottom-0 z-10 w-full bg-background border-t border-border">
          <div className="flex justify-center py-2 max-w-screen-lg mx-auto mb-2 mt-4">
            <div className="w-full shrink relative px-4 w-searchbar-xs 2xl:w-searchbar-sm 3xl:w-searchbar mx-auto">
              <textarea
                ref={textareaRef}
                autoFocus
                className={`
                  opacity-100
                  w-full
                  shrink
                  border
                  border-border
                  rounded-lg
                  outline-none
                  placeholder-gray-400
                  pl-4
                  pr-12
                  py-4
                  overflow-hidden
                  h-14
                  ${
                    (textareaRef?.current?.scrollHeight || 0) >
                    MAX_INPUT_HEIGHT
                      ? "overflow-y-auto"
                      : ""
                  }
                  whitespace-normal
                  break-word
                  overscroll-contain
                  resize-none
                `}
                style={{ scrollbarWidth: "thin" }}
                role="textarea"
                aria-multiline
                placeholder="Ask me anything..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey &&
                    message
                  ) {
                    // onSubmit();
                    setPostMessage(message);
                    setMessage('');
                    event.preventDefault();
                  }
                }}
                suppressContentEditableWarning={true}
              />
              <div className="absolute bottom-4 right-10">
                <div
                  className={"cursor-pointer"}
                  onClick={() => {
                    // if (!isStreaming) {
                      if (message) {
                        // onSubmit();
                        setPostMessage(message);
                        setMessage('');
                      }
                    // } else {
                    //   setIsCancelled(true);
                    // }
                  }}
                >

                  {streamingQ.length ? (
                    <FiStopCircle
                      size={18}
                      className={
                        "text-emphasis w-9 h-9 p-2 rounded-lg hover:bg-hover"
                      }
                    />
                  ) : (
                    <FiSend
                      size={18}
                      className={
                        "text-emphasis w-9 h-9 p-2 rounded-lg " +
                        (message ? "bg-blue-200" : "")
                      }
                    />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </>
  );
}