# Ensure all required environment variables are set or have defaults
: "${DOMAIN:=localhost}"
: "${PROXY_READ_TIMEOUT:=600s}"
: "${PROXY_CONNECT_TIMEOUT:=600s}"
: "${PROXY_SEND_TIMEOUT:=600s}"
: "${SEND_TIMEOUT:=600s}"
# fill in the template
envsubst '$DOMAIN $PROXY_READ_TIMEOUT $PROXY_CONNECT_TIMEOUT $PROXY_SEND_TIMEOUT $SEND_TIMEOUT $SSL_CERT_FILE_NAME $SSL_CERT_KEY_FILE_NAME' < "/etc/nginx/conf.d/$1" > /etc/nginx/conf.d/app.conf

# wait for the api_server to be ready
echo "Waiting for API server to boot up; this may take a minute or two..."
echo "If this takes more than ~5 minutes, check the logs of the API server container for errors with the following command:"
echo
echo "docker logs danswer-stack_api_server-1"
echo

while true; do
  # Use curl to send a request and capture the HTTP status code
  status_code=$(curl -o /dev/null -s -w "%{http_code}\n" "http://api_server:8080/health")
  
  # Check if the status code is 200
  if [ "$status_code" -eq 200 ]; then
    echo "API server responded with 200, starting nginx..."
    break  # Exit the loop
  else
    echo "API server responded with $status_code, retrying in 5 seconds..."
    sleep 5  # Sleep for 5 seconds before retrying
  fi
done

# Start nginx and reload every 6 hours
while :; do sleep 6h & wait; nginx -s reload; done & nginx -g "daemon off;"
