Using the API
----------------

Klub přatel provides a REST api using [django-rest-framework](https://www.django-rest-framework.org/). Django rest framework makes it easy to expose Django models to the outside world. Models are exposed using views that list objects. These lists use pagination.

There are also some views that do not correspond directly to models.

You can find swagger docs here:

[![Swagger docs](https://test.klub-pratel.cz/media/drf-yasg/swagger-ui-dist/favicon-32x32.40d4f2c38d1c.png) Swagger docs](https://test.klub-pratel.cz/api/docs/)

Also, if you open endpoints as Admin user in the browser you will be presented with a user friendly interface explaining how to use the endpoint.

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


Please note this endpoint is likely to be updated in the future to include a CAPTCHA code.

Resetting passwords
-----------------------

Password reset emails can be triggered with the `reset_password_email/` endpoint. This endpoint takes a json object with a single field `email`:

Example

```
{
   "email": "foo@example.com"
}
```

Please note this endpoint is likely to be updated in the future to include a CAPTCHA code.

 
User based Login Flows
---------------------------

You can log in to the user based rest API using the endpoint `http://localhost:8000/api/token/`. This will give you a JWT token.

You can get your refresh token using the endpoint `http://localhost:8000/api/token/refresh/`

You can then send request using the usage [can be found inthe simplejwt docs](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html#usage).

Finding out about the current user
-----------------------------------------

There are various levels of permissions that users can have in the front end:

0. Anonymous User
 - Can see the structure of the organization: Administrative Units
 - Can view all events
1. Ordinary user:
 - Can find out which events they signed up: TODO
 - Can update events that they have organized: TODO
 - Can list their own interactions: TODO
 - Can express interest in an event
2. Event organizers and Staff: TODO
 - Can create update Events in their Administrative Units
 - Can update events organizational team: TODO
 - Can search for users by name/email: TODO
3. Superusers
 - Can create and update events globally
 - Access all other endpoints: see the [Swagger docs](https://test.klub-pratel.cz/api/docs/)
 
 
Who am I?
-----------

Once you are logged in you can find out what kind of user you are with the

`api/frontend/whoami`

endpoint. With this endpoint, you can also update your own First and Last name.

Administrative Units
-------------------------

Administrative units can be viewed at the endpoint `/api/bronto/administrative_unit/`


Payments
----------

Users can check if their payment is up to date according to their subscription using the `check_last_payment/` endpoint which returns 200 if up to date and 404 otherwise.


Events
-------

The endpoint `https://test.klub-pratel.cz/api/bronto/event/` lists all events.

Creating editing events:

- Admin only

- permissions GET, POST, DELETE

- endpoint `https://test.klub-pratel.cz/api/frontend/events/`

Event Types
-------------

- Admin only

- permissions GET, POST, DELETE

- endpoint `https://test.klub-pratel.cz/api/frontend/event-type/`


Locations
-------

- Admin only

- permissions GET, POST, DELETE

- endpoint `https://test.klub-pratel.cz/api/frontend/location/`

Interactions
---------------

TODO
