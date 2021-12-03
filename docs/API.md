Using the API
----------------

Klub přatel provides a REST api using [django-rest-framework](https://www.django-rest-framework.org/). Django rest framework makes it easy to expose Django models to the outside world. Models are exposed using views that list objects. These lists use pagination.

There are also some views that do not corespond directly to models.

You can find swagger docs here:

[![Swagger docs](https://test.klub-pratel.cz/media/drf-yasg/swagger-ui-dist/favicon-32x32.40d4f2c38d1c.png) Swagger docs](https://test.klub-pratel.cz/api/docs/)

Authentification
-------------------

In order to interact with the API you'll need authentification.

Klub přatel supports an OAuth flow for requesting an Access Token. [OAuth Application](https://test.klub-pratel.cz/oauth2_provider/application/add/).

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
 
User based Login Flows
---------------------------
 
Per user authentification is not supported at this time.

Events
-------

The endpoint `https://test.klub-pratel.cz/api/bronto/event/` lists all events.

Creating editing events:

TODO

Locations
-------

TODO

Interactions
---------------

TODO

Administrative Units
------------------------

TODO



