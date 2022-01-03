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
 
Registering users via API
------------------------------

The endpoint for registering users is `/api/register-userprofile`. Here are some example contents:

```
{
    "username": "test2",
    "password": "foobarbaz",
    "first_name": "Test",
    "last_name": "Test",
    "telephone": "334534534",
    "email": "test@example.com",
    "userchannels": [
      {
        "money_account": "obecne_darujme",
        "event": "obecne",
        "regular_amount": 250,
        "regular_frequency": "monthly"
        
      }
    ]
}
```

Possible values for `regular_frequency` are

- `monthly`
- `quaterly`
- `biannually`
- `annually`

`money_account` and `event ` should be set to slugs.

You can find event slugs in the admin at `/events/event/` for example `https://test.klub-pratel.cz/events/event/`.

Money account slugs are in the admin at `/aklub/bankaccount/` aka `https://test.klub-pratel.cz/aklub/bankaccount/`

 
User based Login Flows
---------------------------

You can log in to the user based rest API using the endpoint `http://localhost:8000/api/token/`. This will give you a JWT token.

You can get your refresh token using the endpoint `http://localhost:8000/api/token/refresh/`

You can then send request using the usage info here: `https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html#usage`


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
