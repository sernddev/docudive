"use client";
import { useEffect, useState, useRef, ChangeEvent, Key } from "react";
import { LoadingAnimation } from "@/components/Loading";
import { AdminPageTitle } from "@/components/admin/Title";
import { KeyIcon, TrashIcon } from "@/components/icons/icons";
import { ApiKeyForm } from "@/components/openai/ApiKeyForm";
import { GEN_AI_API_KEY_URL } from "@/components/openai/constants";
import { fetcher } from "@/lib/fetcher";
import { Text, Title } from "@tremor/react";
import { FiCpu } from "react-icons/fi";
import useSWR, { mutate } from "swr";
import {MODELS} from "@/lib/constants";
import {getSelectedModal, sendSelectedModal} from "@/lib/mediator.service";

const ExistingKeys = () => {
  const { data, isLoading, error } = useSWR<{ api_key: string }>(
    GEN_AI_API_KEY_URL,
    fetcher
  );

  if (isLoading) {
    return <LoadingAnimation text="Loading" />;
  }

  if (error) {
    return <div className="text-error">Error loading existing keys</div>;
  }

  if (!data?.api_key) {
    return null;
  }

  return (
    <div>
      <Title className="mb-2">Existing Key</Title>
      <div className="flex mb-1">
        <p className="text-sm italic my-auto">sk- ****...**{data?.api_key}</p>
        <button
          className="ml-1 my-auto hover:bg-hover rounded p-1"
          onClick={async () => {
            await fetch(GEN_AI_API_KEY_URL, {
              method: "DELETE",
            });
            window.location.reload();
          }}
        >
          <TrashIcon />
        </button>
      </div>

    </div>
  );
};

const Page = () => {
  const [models, setmodels] = useState([{id: 1, name: "All Models", checked: false}, {id: 2, name: "Model 1", checked: false
  },
    {id: 3, name: "Model 2", checked: false}]);
  let privileges = getSelectedModal();
  models[Number(privileges)].checked = true;

  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>, id) => {
    let modelsData = models.map((obj: any) => {
      obj.checked = false;
      return obj;
    });
    modelsData[id - 1].checked = true;
    setmodels(modelsData);
    let privilegesCount;
    modelsData.map((obj:any) => {
    if(obj.checked === true){
      privilegesCount = obj.id - 1;
    }
    });
    sendSelectedModal(privilegesCount);
  }
  return (
    <div className="mx-auto container">
      <AdminPageTitle
        title="LLM Keys"
        icon={<FiCpu size={32} className="my-auto" />}
      />

      <ExistingKeys />

      <Title className="mb-2 mt-6">Update Key</Title>
      <Text className="mb-2">
        Specify an OpenAI API key and click the &quot;Submit&quot; button.
      </Text>
      <div className="border rounded-md border-border p-3">
        <ApiKeyForm
          handleResponse={(response) => {
            if (response.ok) {
              mutate(GEN_AI_API_KEY_URL);
            }
          }}
        />
      </div>
      <div className={'admin-model-privileges mt-2'}>
        <p className={''}>Manage User Privileges </p>
        <div className={'set-modal-radio mt-3'}>
          {
            models.map((model)=> (
              <div key={model.id} className={'model-check-box mt-1'}>
                <input
                  type="radio"
                  className={'mt-1'}
                  value={model.id}
                  checked={model.checked}
                  onChange={(event) => { handleCheckboxChange(event, model.id) }}
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
  );
};

export default Page;
