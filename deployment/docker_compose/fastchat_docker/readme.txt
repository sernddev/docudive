--To Start vlm

docker-cmpose up -d
------------------

1) docker cp mixstral.conf fastchat_v1:/code
   docker exec -u 0 -it fastchat_v1 bash
   supervisord -c mixstral.conf

2) docker cp jaisv3.conf fastchat_v1:/code
   docker exec -u 0 -it fastchat_v1 bash
   supervisord -c jaisv3.conf
   
   
   
curl -XPOST http://192.168.1.74:9198/v1/openapi/chat/completions \  
  -H 'accept: application/json' \ 
  -H 'Content-Type: application/json' \ 
  -d '{
      "model": "Meta-Llama-3-70B-Instruct",
      "messages": [{\"role\": \"user\",\"content\": \"Hello!\"}],
	  "temperature":0
    }'   