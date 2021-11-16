Using the API:

[API swagger docs](https://test.klub-pratel.cz/api/docs/)

You can use the rest api by creating an [OAuth Application](https://test.klub-pratel.cz/oauth2_provider/application/add/).

You'll want to set the `Authorization grant type` to "Client credentials".
 Furthermore, if you want your application to have access to event data you need to add the `can_view_events` scope to the scope string.
 
 To test your new application you can request a token using the curl command
 
 ```
curl --header "Content-Type: application/json" --request POST --data '{"grant_type":"client_credentials","client_id":"<id>","client_secret":"<secret>"}' https://test.klub-pratel.cz/api/o/token
 ```
 
 You can then use your token like so:
 
 ```
curl -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -X GET https://test.klub-pratel.cz/api/bronto/event/
 ```
